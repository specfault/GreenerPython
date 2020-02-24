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

    def test_create_long_file_name(self):
        name = "test_long_file_name.py"
        res = template.create(name)
        self.assertIn("import long_file_name", res)
        self.assertNotIn("import long_file_name.py", res)
        self.assertNotIn("import test_long_file_name", res)
