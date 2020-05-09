import unittest
import azure.function


class FunctionTestCase(unittest.TestCase):
    def test_handler(self):
        actual = azure.function.handler(None, None)
        self.assertEqual(actual['message'], "azure.core")
