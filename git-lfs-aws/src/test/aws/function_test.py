import json
import unittest

import aws.function


class FunctionTestCase(unittest.TestCase):
    def test_handler(self):
        actual = aws.function.handler(None, None)
        self.assertEqual(actual['statusCode'], 200)
        self.assertEqual(actual['headers']['foo'], 'bar')
        self.assertEqual(json.loads(actual['body'])['message'], "aws.core")
