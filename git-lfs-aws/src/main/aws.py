import json
import logging
import os
from dataclasses import dataclass, field
from typing import List, Dict, Any

import boto3
from botocore.client import Config

from core import *

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

__all__ = (
    'ProxyRequest',
    'ProxyResponse',
    'S3LargeFileStorage',
    'Factory',

    'process',
    'lambda_handler'
)


@dataclass(init=False)
class ProxyRequest:
    resource: str
    path: str
    http_method: str
    headers: Dict[str, str]
    multi_value_headers: Dict[str, List[str]]
    query_string_parameters: Dict[str, str]
    multi_value_query_string_parameters: Dict[str, List[str]]
    path_parameters: Dict[str, str]
    stage_variables: Dict[str, str]
    request_context: Dict[str, Any]
    body: str
    is_base64_encoded: bool

    def __init__(self, request):
        self.resource = request.get('resource')
        self.path = request.get('path')
        self.http_method = request.get('httpMethod')
        self.headers = request.get('headers', dict())
        self.multi_value_headers = request.get('multiValueHeaders', dict())
        self.query_string_parameters = request.get('queryStringParameters', dict())
        self.multi_value_query_string_parameters = request.get('multiValueQueryStringParameters', dict())
        self.path_parameters = request.get('pathParameters', dict())
        self.stage_variables = request.get('stageVariables', dict())
        self.request_context = request.get('requestContext', dict())
        self.body = request.get('body')
        self.is_base64_encoded = request.get('isBase64Encoded')


@dataclass
class ProxyResponse:
    body: Any
    is_base64_encoded: bool = False
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)
    multi_value_headers: Dict[str, List[str]] = field(default_factory=dict)

    def as_dict(self):
        return {
            'isBase64Encoded': self.is_base64_encoded,
            'statusCode': self.status_code,
            'headers': self.headers,
            'multiValueHeaders': self.multi_value_headers,
            'body': json.dumps(self.body)
        }


class S3LargeFileStorage(LargeFileStorage):

    def __init__(self) -> None:
        self.bucket_name = os.getenv('S3_BUCKET_NAME')
        self.s3 = boto3.client(
            service_name='s3',
            config=Config(signature_version='s3v4')
        )

    def exists(self, oid: str) -> bool:
        res = self.s3.list_objects_v2(
            Bucket=self.bucket_name,
            Prefix=oid,
            MaxKeys=1
        )

        return 'Contents' in res

    def prepare_download(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return BatchResponse.ObjectLfs.Action(
            href=self.presign('get_object', oid)
        )

    def prepare_upload(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        return BatchResponse.ObjectLfs.Action(
            href=self.presign('put_object', oid)
        )

    def presign(self, action: str, oid: str) -> str:
        return self.s3.generate_presigned_url(
            action,
            Params={
                'Bucket': self.bucket_name,
                'Key': oid
            },
            ExpiresIn=3600
        )


class Factory:
    @staticmethod
    def create_batch_facade():
        return BatchFacade(S3LargeFileStorage())


def process(request: ProxyRequest, context) -> ProxyResponse:
    try:
        if request.path == '/objects/batch':
            facade = Factory.create_batch_facade()
        else:
            raise HttpError(404, 'Not found')

        response = facade.process(
            HttpRequest(
                path=request.path,
                method=request.http_method,
                headers=request.headers,
                parameters=request.query_string_parameters,
                body=request.body
            )
        )

        return ProxyResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=dataclass_as_dict(response.body)
        )

    except HttpError as e:
        return ProxyResponse(
            status_code=e.code,
            body={
                'message': e.message,
                'request_id': context.aws_request_id
            }
        )

    except Exception as e:
        logger.error(e, exc_info=True)
        return ProxyResponse(
            status_code=500,
            body={
                'message': 'Internal Server Error',
                'request_id': context.aws_request_id
            }
        )


def lambda_handler(request, context):
    logger.info('ProxyRequest: %s' % json.dumps(request))
    response = process(ProxyRequest(request), context)
    logger.info('ProxyResponse: %s' % json.dumps(response.as_dict()))
    return response.as_dict()
