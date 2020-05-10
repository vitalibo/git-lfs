import json
import unittest

from aws.models import ProxyRequest, ProxyResponse


class ProxyRequestTestCase(unittest.TestCase):
    def test_init(self):
        with open('../resources/proxy_request.json', 'r') as f:
            proxy_request = json.loads(f.read())

        actual = ProxyRequest(proxy_request)

        self.assertEqual(actual.resource, '/{proxy+}')
        self.assertEqual(actual.path, '/hello/world')
        self.assertEqual(actual.http_method, 'POST')
        self.assertEqual(actual.headers['Accept'], '*/*')
        self.assertEqual(actual.multi_value_headers['Accept-Encoding'], ['gzip, deflate', ])
        self.assertEqual(actual.query_string_parameters['name'], 'me')
        self.assertEqual(actual.multi_value_query_string_parameters['multivalueName'], ['you', 'me'])
        self.assertEqual(actual.path_parameters['proxy'], 'hello/world')
        self.assertEqual(actual.stage_variables['stageVariableName'], 'stageVariableValue')
        self.assertEqual(actual.request_context['accountId'], '12345678912')
        self.assertEqual(actual.body, '{\r\n\t"a": 1\r\n}')
        self.assertEqual(actual.is_base64_encoded, False)


class ProxyResponseTestCase(unittest.TestCase):
    def test_as_dict(self):
        with open('../resources/proxy_response.json', 'r') as f:
            expected = json.loads(f.read())
            response = ProxyResponse(
                is_base64_encoded=True,
                status_code=200,
                headers={"Cache-Control": "max-age=60"},
                multi_value_headers={"multiValueName": ["you", "me"]},
                body={"message": "Hello World!"})

        actual = response.as_dict()

        self.assertEqual(actual, expected)
