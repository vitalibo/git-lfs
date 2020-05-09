import json

import core.facades


def handler(event, context):
    return {
        'statusCode': 200,
        'headers': {
            "foo": "bar"
        },
        'body': json.dumps({
            'message': 'aws.' + core.facades.process()
        })
    }
