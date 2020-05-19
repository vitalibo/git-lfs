from __future__ import annotations

import json
from abc import ABC
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

__all__ = (
    'HttpRequest',
    'HttpResponse',
    'HttpError',
    'BatchRequest',
    'BatchResponse',
    'BatchError',
    'LargeFileStorage',
    'BatchFacade',

    'dataclass_as_dict'
)


@dataclass
class HttpRequest:
    path: str
    method: str
    headers: Dict[str, str] = field(default_factory=dict)
    parameters: Dict[str, str] = field(default_factory=dict)
    body: str = None


@dataclass
class HttpResponse:
    body: Any
    status_code: int = 200
    headers: Dict[str, str] = field(default_factory=dict)


class HttpError(Exception):

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


@dataclass
class BatchRequest:
    @dataclass
    class RefSpec:
        name: str

    @dataclass
    class ObjectLfs:
        oid: str
        size: int

    operation: str
    objects: List[ObjectLfs]
    transfers: List[str] = field(default_factory=lambda: ['basic'])
    ref: RefSpec = None


@dataclass
class BatchResponse:
    @dataclass
    class ObjectLfs:
        @dataclass
        class Action:
            href: str
            header: Dict[str, str] = field(default_factory=dict)
            expires_in: int = None
            expires_at: str = None

        @dataclass
        class Error:
            code: int
            message: str

        oid: str
        size: int
        authenticated: bool = None
        actions: Dict[str, Action] = None
        error: Error = None

    transfer: str
    objects: List[ObjectLfs]

    def as_dict(self) -> Dict[str, Any]:
        return dataclass_as_dict(self)


class BatchError(Exception):

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


def dataclass_as_dict(obj):
    def scrub_dict(d):
        scrubbed_dict = {}
        for k, v in d.items():
            if isinstance(v, dict):
                v = scrub_dict(v)
            if isinstance(v, list):
                v = scrub_list(v)
            if v not in (u'', None, {}):
                scrubbed_dict[k] = v
        return scrubbed_dict

    def scrub_list(d):
        scrubbed_list = []
        for v in d:
            if isinstance(v, dict):
                v = scrub_dict(v)
            scrubbed_list.append(v)
        return scrubbed_list

    return scrub_dict(asdict(obj))


class LargeFileStorage(ABC):
    def exists(self, oid: str) -> bool:
        pass

    def prepare_download(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        pass

    def prepare_upload(self, oid: str, size: int) -> BatchResponse.ObjectLfs.Action:
        pass


class BatchFacade:

    def __init__(self, lfs: LargeFileStorage):
        self.lfs = lfs

    def process(self, request: HttpRequest) -> HttpResponse:
        if request.path != '/objects/batch' or request.method != 'POST':
            raise HttpError(404, 'Not found')

        if 'application/vnd.git-lfs+json' not in request.headers.get('Accept', ''):
            raise HttpError(406, 'Not Acceptable')

        body = json.loads(request.body)

        response = self.batch_request(
            BatchRequest(
                operation=body['operation'],
                transfers=body.get('transfers', ['basic', ]),
                ref=BatchRequest.RefSpec(body['ref']['name']) if body.get('ref') else None,
                objects=[BatchRequest.ObjectLfs(obj['oid'], obj['size']) for obj in body['objects']]
            )
        )

        return HttpResponse(
            status_code=200,
            headers={
                'Content-Type': 'application/vnd.git-lfs+json'
            },
            body=response
        )

    def batch_request(self, request: BatchRequest) -> BatchResponse:
        if 'basic' not in request.transfers:
            raise HttpError(422, 'Unprocessable Entity')

        objects = []
        for obj in request.objects:
            result = BatchResponse.ObjectLfs(obj.oid, obj.size)
            try:
                result.authenticated = True

                if request.operation == 'download':
                    if not self.lfs.exists(obj.oid):
                        raise BatchError(404, 'The object does not exist on the server')

                    result.actions = {
                        'download': self.lfs.prepare_download(obj.oid, obj.size)
                    }

                elif request.operation == 'upload':
                    result.actions = {
                        'upload': self.lfs.prepare_upload(obj.oid, obj.size)
                    }

                else:
                    raise HttpError(422, 'Unprocessable Entity')

            except BatchError as be:
                result.error = BatchResponse.ObjectLfs.Error(be.code, be.message)

            objects.append(result)

        return BatchResponse(transfer='basic', objects=objects)
