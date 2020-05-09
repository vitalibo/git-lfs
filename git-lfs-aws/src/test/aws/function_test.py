import unittest
import aws.function


class FunctionTestCase(unittest.TestCase):
    def test_handler(self):
        actual = aws.function.handler(None, None)
        self.assertEqual(actual['message'], "aws.core")
