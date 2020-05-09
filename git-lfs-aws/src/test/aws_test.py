import unittest
import aws


class AwsTestCase(unittest.TestCase):
    def test_process(self):
        actual = aws.process()
        self.assertEqual(actual, "aws.core")
