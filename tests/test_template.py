import unittest
import template


class TestTemplate(unittest.TestCase):
    def test_create(self):
        name = "test_bla"
        res = template.create(name)
        self.assertIn("import unittest", res)
        self.assertIn("import bla", res)
        self.assertIn("class TestBla", res)
