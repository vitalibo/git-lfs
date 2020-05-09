import core.facades


def handler(event, context):
    return {
        'message': "azure." + core.facades.process()
    }
