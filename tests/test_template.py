import unittest
import template


class TestTemplate(unittest.TestCase):
    def test_create(self):
        name = "test_bla.py"
        res = template.create(name)
        self.assertIn("import unittest", res)
        self.assertIn("import bla", res)
        self.assertNotIn("import bla.py", res)
        self.assertIn("class TestBla", res)
        self.assertNotIn("class TestBla.py", res)
