from core.models import BatchRequest, BatchResponse, BatchError


def process():
    return "core"


class LargeFileStorage:

    def exist(self, oid: str) -> bool:
        pass

    def prepare_to_download(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        pass

    def prepare_to_upload(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        pass

    def download(self):
        pass

    def upload(self):
        pass


class BatchFacade:

    def __init__(self, storage: LargeFileStorage):
        self.storage = storage

    def process(self, request: BatchRequest) -> BatchResponse:
        if 'basic' not in request.transfers:
            raise ValueError(f'Unsupported transfers {request.transfers}')

        objects = []
        if request.operation == 'download':
            for obj in request.objects:
                objects.append(self.download(obj))

        elif request.operation == 'upload':
            for obj in request.objects:
                objects.append(self.upload(obj))

        else:
            raise ValueError(f'Unsupported operation: {request.operation}')

        return BatchResponse(transfer='basic', objects=objects)

    def download(self, obj: BatchRequest.ObjectLfs) -> BatchResponse.ObjectLfs:
        res = BatchResponse.ObjectLfs(obj.oid, obj.size)
        try:
            if not self.storage.exist(obj.oid):
                raise BatchError(404, 'The object does not exist on the server')

            res.authenticated = True
            res.actions = {
                'download': self.storage.prepare_to_download(obj.oid, obj.size)
            }

        except BatchError as be:
            res.error = BatchResponse.ObjectLfs.Error(be.code, be.message)

        return res

    def upload(self, obj: BatchRequest.ObjectLfs) -> BatchResponse.ObjectLfs:
        res = BatchResponse.ObjectLfs(obj.oid, obj.size)
        try:
            res.authenticated = True
            res.actions = {
                'upload': self.storage.prepare_to_upload(obj.oid, obj.size)
            }

        except BatchError as be:
            res.error = BatchResponse.ObjectLfs.Error(be.code, be.message)

        return res
