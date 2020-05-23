import json
import logging
import os
import re
from datetime import datetime, timedelta, timezone

import azure.functions as func
from azure.storage.blob import blockblobservice, BlobPermissions

try:
    from ..core import *
except:
    from core import *

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

__all__ = (
    'BlobLargeFileStorage',
    'Factory',

    'process',
    'main'
)


class BlobLargeFileStorage(LargeFileStorage):

    def __init__(self, env=os.environ):
        self.storage_account_name = env['STORAGE_ACCOUNT']
        self.storage_account_primary_key = env['STORAGE_ACCOUNT_PRIMARY_KEY']
        self.storage_container_name = env['STORAGE_CONTAINER']
        self.client = blockblobservice.BlockBlobService(
            account_name=self.storage_account_name,
            account_key=self.storage_account_primary_key
        )

    def exists(self, oid: str) -> bool:
        return self.client.exists(self.storage_container_name, oid)

    def prepare_download(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        expiry = datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc) + timedelta(hours=1)

        return BatchResponse.ObjectLfs.Action(
            href=self.generate_blob_shared_access_signature_url(
                oid, BlobPermissions.READ, expiry
            ),
            expires_at=expiry.isoformat()
        )

    def prepare_upload(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        expiry = datetime.utcnow().replace(microsecond=0, tzinfo=timezone.utc) + timedelta(hours=1)

        return BatchResponse.ObjectLfs.Action(
            href=self.generate_blob_shared_access_signature_url(
                oid, BlobPermissions.WRITE, expiry
            ),
            header={
                'x-ms-blob-type': 'BlockBlob'
            },
            expires_at=expiry.isoformat()
        )

    def generate_blob_shared_access_signature_url(self, oid, permission, expiry):
        sas = self.client.generate_blob_shared_access_signature(
            self.storage_container_name, oid, permission, expiry
        )

        return f'https://{self.storage_account_name}.blob.core.windows.net/{self.storage_container_name}/{oid}?{sas}'


class KeyInsensitiveDict(dict):
    def __getitem__(self, key):
        return dict.__getitem__(self, key.lower())

    def get(self, key, *args, **kwargs):
        return dict.get(self, key.lower(), *args, **kwargs)


class Factory:
    @staticmethod
    def create_batch_facade():
        return BatchFacade(BlobLargeFileStorage())


def process(request: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    try:
        facade = Factory.create_batch_facade()

        response = facade.process(
            HttpRequest(
                path=re.split('(api)', request.url)[2],
                method=request.method,
                headers=KeyInsensitiveDict(request.headers),
                parameters=KeyInsensitiveDict(request.params),
                body=request.get_body().decode()
            )
        )

        return func.HttpResponse(
            status_code=response.status_code,
            headers=response.headers,
            body=json.dumps(
                dataclass_as_dict(response.body)
            )
        )

    except HttpError as e:
        return func.HttpResponse(
            status_code=e.code,
            mimetype='application/json',
            body=json.dumps(
                {
                    'message': e.message,
                    'request_id': context.invocation_id
                }
            )
        )

    except Exception as e:
        logger.error(e, exc_info=True)
        return func.HttpResponse(
            status_code=500,
            mimetype='application/json',
            body=json.dumps(
                {
                    'message': 'Internal Server Error',
                    'request_id': context.invocation_id
                }
            )
        )


def main(req: func.HttpRequest, context: func.Context) -> func.HttpResponse:
    logger.info('azure.HttpRequest: %s' % vars(req))
    res = process(req, context)
    logger.info('azure.HttpResponse: %s' % vars(res))
    return res
