import json

import core.facades
from aws.models import ProxyRequest, ProxyResponse
from core import logger


def handler(request, context):
    logger.debug('ProxyRequest: %s' % json.dumps(request))
    response = process(ProxyRequest(request), context).as_dict()
    logger.debug('ProxyResponse: %s' % json.dumps(response))
    return response


def process(request: ProxyRequest, context) -> ProxyResponse:
    return ProxyResponse(
        status_code=200,
        headers={
            "foo": "bar"
        },
        body={
            'message': 'aws.' + core.facades.process()
        }
    )
