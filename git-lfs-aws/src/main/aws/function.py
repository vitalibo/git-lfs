import json
import os

import boto3

from aws.models import ProxyRequest, ProxyResponse
from core import logger
from core.facades import BatchFacade
from core.facades import LargeFileStorage
from core.models import BatchRequest, BatchResponse, BatchError


def handler(request, context):
    logger.info('ProxyRequest: %s' % json.dumps(request))
    response = process(ProxyRequest(request), context).as_dict()
    logger.info('ProxyResponse: %s' % json.dumps(response))
    return response


def process(request: ProxyRequest, context) -> ProxyResponse:
    try:
        if request.path == '/objects/batch':
            facade = BatchFacade(S3LargeFileStorage(os.getenv('S3_BUCKET_NAME')))
        else:
            raise BatchError(404, 'Not found')

        response = facade.process(parse_proxy_request(request))

        return ProxyResponse(
            status_code=200,
            headers={
                'Content-Type': 'application/vnd.git-lfs+json'
            },
            body=response.as_dict()
        )

    except BatchError as e:
        return ProxyResponse(
            status_code=e.code,
            body={
                'code': e.code,
                'message': e.message,
                'request_id': context.aws_request_id
            }
        )
    except:
        return ProxyResponse(
            status_code=500,
            body={
                'code': 500,
                'message': 'Internal Server Error',
                'request_id': context.aws_request_id
            }
        )


def parse_proxy_request(request: ProxyRequest):
    request = json.loads(request.body)

    return BatchRequest(
        operation=request['operation'],
        transfers=request.get('transfers', ['basic', ]),
        ref=None if request.get('ref') is None else BatchRequest.RefSpec(request['ref']['name']),
        objects=[BatchRequest.ObjectLfs(obj['oid'], obj['size']) for obj in request['objects']]
    )


class S3LargeFileStorage(LargeFileStorage):

    def __init__(self, bucket_name: str) -> None:
        self.s3 = boto3.client('s3')
        self.bucket_name = bucket_name

    def exist(self, oid: str) -> bool:
        res = self.s3.list_objects_v2(Bucket=self.bucket_name, Prefix=oid, MaxKeys=1)
        return 'Contents' in res

    def prepare_to_download(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return BatchResponse.ObjectLfs.Action(
            href=self.generate_presigned_url('get_object', oid)
        )

    def prepare_to_upload(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return BatchResponse.ObjectLfs.Action(
            href=self.generate_presigned_url('put_object', oid)
        )

    def download(self):
        raise ValueError('Method not implemented')

    def upload(self):
        raise ValueError('Method not implemented')

    def generate_presigned_url(self, action: str, oid: str):
        return self.s3.generate_presigned_url(
            action,
            Params={'Bucket': self.bucket_name, 'Key': oid},
            ExpiresIn=3600)
