import unittest
import azure


class AzureTestCase(unittest.TestCase):
    def test_process(self):
        actual = azure.process()
        self.assertEqual(actual, "azure.core")
