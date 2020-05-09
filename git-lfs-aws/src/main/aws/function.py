import core.facades


def handler(event, context):
    return {
        'message': "aws." + core.facades.process()
    }
