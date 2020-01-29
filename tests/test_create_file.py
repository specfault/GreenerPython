from . import vim
import unittest
from py import path
from tempfile import TemporaryDirectory


class TestCreateFile(unittest.TestCase):
    def setUp(self):
        self.resource = TemporaryDirectory()
        self.path = path.local(self.resource.name)

    def test_create_file_in_source_directory(self):
        """there's no 'tests' directory
        so the test file should be created
        next to the corresponding source file"""
        source_file = self.path.join("bla.py")
        test_file = self.path.join("test_bla.py")
        vim.save(test_file)
        self.assertTrue(source_file.check())  # check that file exists

    def test_create_file_in_test_directory(self):
        """test directory in the same folder as the source file"""
        test_dir = self.path.mkdir('tests')
        source_file = self.path.join("bla.py")
        test_file = test_dir.join("test_bla.py")
        vim.save(test_file)
        self.assertTrue(source_file.check())  # check that file exists

    def test_create_test_file_in_nested_test_directory(self):
        """directory structure of source file
        should be duplicated inside tests"""
        source_dir = self.path.join('blubb')
        test_dir = self.path.mkdir('tests')
        source_file = source_dir.join("bla.py")
        test_file = test_dir.mkdir('blubb').join("test_bla.py")
        vim.save(test_file)
        self.assertTrue(source_file.check())  # check that file exists
