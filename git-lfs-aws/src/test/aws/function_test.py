import json
import unittest

import aws.function


class FunctionTestCase(unittest.TestCase):
    def test_handler(self):
        with open('../resources/proxy_request.json', 'r') as f:
            data = f.read()

        actual = aws.function.handler(json.loads(data), None)

        self.assertEqual(actual['statusCode'], 200)
        self.assertEqual(actual['headers']['foo'], 'bar')
        self.assertEqual(json.loads(actual['body'])['message'], "aws.core")
