import datetime
import json
import logging
import os
import uuid

import flask
from google.cloud import storage

from core import *

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

__all__ = (
    'GoogleCloudFileStorage',
    'Factory',
    'process',
    'function_handler'
)


class GoogleCloudFileStorage(LargeFileStorage):

    def __init__(self) -> None:
        storage_client = storage.Client()
        self.bucket = storage_client.bucket(os.getenv('BUCKET_NAME'))

    def exists(self, oid: str) -> bool:
        blob = self.bucket.blob(oid)
        return blob.exists()

    def prepare_download(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return BatchResponse.ObjectLfs.Action(
            href=self.presign('GET', oid)
        )

    def prepare_upload(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return BatchResponse.ObjectLfs.Action(
            href=self.presign('PUT', oid)
        )

    def presign(self, method: str, oid: str):
        blob = self.bucket.blob(oid)
        return blob.generate_signed_url(
            version='v4',
            expiration=datetime.timedelta(minutes=60),
            method=method
        )


class Factory:

    @staticmethod
    def create_batch_facade():
        return BatchFacade(GoogleCloudFileStorage())


def process(request: flask.Request):
    try:
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

    except HttpError as e:
        response = {
            'message': e.message,
            'request_id': str(uuid.uuid4())
        }

        return response, e.code

    except Exception as e:
        logger.error(e, exc_info=True)
        response = {
            'message': 'Internal Server Error',
            'request_id': str(uuid.uuid4())
        }

        return response, 500


def function_handler(req: flask.Request):
    logger.info(f'Request: method={req.method}, path={req.full_path}, body={req.json}')
    response = process(req)
    logger.info('Response: %s' % json.dumps(response))
    return response
