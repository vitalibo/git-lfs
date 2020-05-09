import unittest
import core


class CoreTestCase(unittest.TestCase):
    def test_process(self):
        actual = core.process()
        self.assertEqual(actual, "core")
