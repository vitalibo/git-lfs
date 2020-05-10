import json
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass(init=False)
class ProxyRequest:
    """
    Class the stores Api Gateway proxy request.

    https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format
    """

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


@dataclass(init=False)
class ProxyResponse:
    """
    Class the stores Api Gateway proxy response.

    https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-output-format
    """

    is_base64_encoded: bool
    status_code: int
    headers: Dict[str, str]
    multi_value_headers: Dict[str, List[str]]
    body: str

    def __init__(self, body, is_base64_encoded: bool = False, status_code: int = 200,
                 headers: Dict[str, str] = None, multi_value_headers: Dict[str, List[str]] = None):
        self.body = (body if type(body) == str else json.dumps(body))
        self.is_base64_encoded = is_base64_encoded
        self.status_code = status_code
        self.headers = headers if headers else dict()
        self.multi_value_headers = multi_value_headers if multi_value_headers else dict()

    def as_dict(self):
        return {
            'isBase64Encoded': self.is_base64_encoded,
            'statusCode': self.status_code,
            'headers': self.headers,
            'multiValueHeaders': self.multi_value_headers,
            'body': self.body
        }
