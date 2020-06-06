import argparse
import json
import uuid
from pathlib import Path

import flask
from flask import request
from werkzeug import wsgi

from core import *

__all__ = (
    'SimpleLargeFileStorage',
    'Factory',
    'Web'
)


class SimpleLargeFileStorage(LargeFileStorage):

    def __init__(self, repo: Path, endpoint: str):
        self.repo = repo
        self.endpoint = endpoint

    def exists(self, oid: str) -> bool:
        oid_path = self.path(oid)
        return oid_path.exists()

    def prepare_download(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return self.prepare(oid)

    def download(self, oid: str):
        oid_path = self.path(oid)
        return flask.helpers.send_file(str(oid_path))

    def prepare_upload(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return self.prepare(oid)

    def upload(self, oid: str):
        def mkdir(p):
            try:
                p.mkdir()
            except FileExistsError:
                pass

        oid_path = self.path(oid)
        mkdir(oid_path.parent.parent)
        mkdir(oid_path.parent)

        with open(oid_path, "wb") as f:
            for chunk in wsgi.FileWrapper(request.stream):
                f.write(chunk)

    def prepare(self, oid: str) -> BatchResponse.ObjectLfs.Action:
        return BatchResponse.ObjectLfs.Action(
            href=f'{self.endpoint}transfer/{oid}'
        )

    def path(self, oid):
        return self.repo / oid[:2] / oid[2:4] / oid


class Factory:

    @staticmethod
    def create_large_file_storage():
        return SimpleLargeFileStorage(
            repo=Path(args.repo),
            endpoint=args.endpoint if args.endpoint else request.url_root
        )

    @staticmethod
    def create_batch_facade():
        return BatchFacade(
            Factory.create_large_file_storage()
        )


class Web:
    app = flask.Flask(__name__)

    @staticmethod
    @app.route('/objects/batch', methods=['POST'])
    def objects_batch():
        facade = Factory.create_batch_facade()

        response = facade.process(
            HttpRequest(
                path=request.path,
                method=request.method,
                headers=request.headers,
                parameters=request.args,
                body=json.dumps(request.json)
            )
        )

        return dataclass_as_dict(response.body), response.status_code, response.headers

    @staticmethod
    @app.route('/transfer/<oid>', methods=['GET', 'PUT'])
    def transfer(oid: str):
        lfs = Factory.create_large_file_storage()

        if request.method == 'GET':
            if not lfs.exists(oid):
                raise HttpError(404, 'Not found')

            return lfs.download(oid), 200

        elif request.method == 'PUT':
            lfs.upload(oid)
            return '', 202

    @staticmethod
    @app.errorhandler(404)
    @app.errorhandler(405)
    def not_found(e):
        response = {
            'message': 'Not found',
            'request_id': str(uuid.uuid4())
        }

        return flask.jsonify(response), 404

    @staticmethod
    @app.errorhandler(HttpError)
    def http_error(e):
        response = {
            'message': e.message,
            'request_id': str(uuid.uuid4())
        }

        return flask.jsonify(response), e.code

    @staticmethod
    @app.errorhandler(Exception)
    def internal_server_error(e):
        Web.app.logger.error(e, exc_info=True)
        response = {
            'message': 'Internal Server Error',
            'request_id': str(uuid.uuid4())
        }

        return flask.jsonify(response), 500


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Git LFS: Self Hosted', add_help=False)
    parser.add_argument('--port', type=int, default=5000, help="The port of the web server.")
    parser.add_argument('--host', type=str, default='127.0.0.1', help="The hostname to listen on.")
    parser.add_argument('--repo', type=str, required=True, help="Absolute path to Git LFS repository.")
    parser.add_argument('--endpoint', type=str, required=False, default=None, help="Public endpoint address.")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode.")
    parser.add_argument('-h', '--help', action='help', default=argparse.SUPPRESS, help='Print this message')
    args = parser.parse_args()

    web = Web()
    web.app.run(port=args.port, host=args.host, debug=args.debug)
