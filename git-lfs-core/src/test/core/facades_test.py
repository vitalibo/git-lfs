import unittest
import core.facades


class CoreTestCase(unittest.TestCase):
    def test_process(self):
        actual = core.facades.process()
        self.assertEqual(actual, "core")
