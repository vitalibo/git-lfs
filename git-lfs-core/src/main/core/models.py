from dataclasses import dataclass, asdict
from typing import List, Dict


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
    transfers: List[str]
    ref: RefSpec
    objects: List[ObjectLfs]


@dataclass
class BatchResponse:
    @dataclass
    class ObjectLfs:
        @dataclass(init=False)
        class Action:
            href: str
            header: Dict[str, str]
            expires_in: int
            expires_at: str

            def __init__(self, href,
                         header: Dict[str, str] = None, expires_in: int = None, expires_at: str = None):
                self.href = href
                self.header = header
                self.expires_in = expires_in
                self.expires_at = expires_at

        @dataclass
        class Error:
            code: int
            message: str

        oid: str
        size: int
        authenticated: bool
        actions: Dict[str, Action]
        error: Error

        def __init__(self, oid: str, size: int,
                     authenticated: bool = False,
                     actions: Dict[str, Action] = None, error: Error = None):
            self.oid = oid
            self.size = size
            self.authenticated = authenticated
            self.actions = actions
            self.error = error

    transfer: str
    objects: List[ObjectLfs]

    def as_dict(self):
        return asdict(self)


class BatchError(Exception):

    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message
