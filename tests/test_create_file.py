from . import vim
from py import path
from tempfile import TemporaryDirectory


class TemporaryPath():
    def __init__(self):
        self.resource = TemporaryDirectory()
        self.path = path.local(self.resource.name)


def test_create_test_file_in_source_directory():
    """there's no 'tests' directory
    so the test file should be created next to the corresponding source file"""
    tmp = TemporaryPath()
    source_file = tmp.path.join("bla.py")
    vim.save(source_file)
    test_file = tmp.path.join("test_bla.py")
    assert test_file.check()  # check that file exists


def test_create_test_file_inside_test_directory():
    """test directory in the same folder as the source file"""
    tmp = TemporaryPath()
    test_dir = tmp.path.mkdir('tests')
    source_file = tmp.path.join("bla.py")
    vim.save(source_file)
    test_file = test_dir.join("test_bla.py")
    assert test_file.check()  # check that file exists


def test_create_test_file_inside_test_directory_further_up():
    """directory structure of source file should be duplicated inside tests"""
    tmp = TemporaryPath()
    source_dir = tmp.path.mkdir('blubb')
    test_dir = tmp.path.mkdir('tests')
    source_file = source_dir.join("bla.py")
    vim.save(source_file)
    test_file = test_dir.join('blubb').join("test_bla.py")
    assert test_file.check()  # check that file exists


def test_create_test_file_directly():
    """creating a test file should not create a test for the test"""
    tmp = TemporaryPath()
    test_dir = tmp.path.mkdir('tests')
    source_file = tmp.path.join("test_bla.py")
    vim.save(source_file)
    assert not test_dir.listdir()  # no test for the test


def test_create_magic_file():
    """don't create tests for magic files"""
    tmp = TemporaryPath()
    test_dir = tmp.path.mkdir('tests')
    source_file = tmp.path.join("__init__.py")
    vim.save(source_file)
    assert not test_dir.listdir()  # no test for the test
