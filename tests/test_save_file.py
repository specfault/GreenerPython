from . import vim
from tempfile import TemporaryDirectory
from py import path
import unittest
import textwrap
# save_file is used indirectly
# TODO: split this file into
#  - test_fix_code.py (the actual unit tests)
#  - some file with test utility functions
#  - only end-to-end tests should stay here
# import save_file
from tests.test_fix_code import AbstractFilePair
from tests.test_fix_code import passes


class FilePair:
    def __init__(self, dir, file_pair):
        # keep the directory alive, even without pytest's tmpdir magic
        self.dir = dir
        base_dir = path.local(dir.name).mkdir(file_pair.name)
        test_dir = base_dir.mkdir('tests')

        self.source = base_dir.join(file_pair.name + '.py')
        self.source.write(file_pair.source)

        init_file = base_dir.join('__init__.py')
        init_file.write('from ' + file_pair.name + ' import *')
        init_file = test_dir.join('__init__.py')
        init_file.write('')  # empty init prevents weird name clashes

        self.test = test_dir.join('test_' + file_pair.name + '.py')
        self.test.write(file_pair.test)


class TestVim(unittest.TestCase):
    def broken_code(self):
        # the main point of these tests is that they're end-to-end
        # the exact way in which the code is broken doesn't really matter
        # missing import in test, missing variable in SUT
        return AbstractFilePair(
            'blubb',
            textwrap.dedent("""\
                import unittest


                class TestSomething(unittest.TestCase):
                    def test_something(self):
                        bla = blubb.x
                """))

    def test_vim(self):
        """an end to end test:
        - vim correctly invokes the plugin
        - the plugin fixes SUT and test
        - saving a second time doesn't break anything"""
        file_pair = FilePair(TemporaryDirectory(), self.broken_code())
        self.assertFalse(passes(file_pair))  # code needs fixing
        vim.save(file_pair.test)
        self.assertTrue(passes(file_pair))  # code was actually fixed
        # saving a second time shouldn't change anything
        old_test = file_pair.test.read()
        old_source = file_pair.source.read()
        vim.save(file_pair.test)
        new_test = file_pair.test.read()
        new_source = file_pair.source.read()
        self.assertEqual(new_source, old_source)
        self.assertEqual(new_test, old_test)

    def test_whitespace_in_directory_name(self):
        """an end to end test:
        - vim correctly invokes the plugin
        - the plugin fixes SUT and test
        - saving a second time doesn't break anything"""
        file_pair = FilePair(TemporaryDirectory(suffix="white space"),
                             self.broken_code())
        self.assertFalse(passes(file_pair))  # code needs fixing
        vim.save(file_pair.test)
        self.assertTrue(passes(file_pair))  # code was actually fixed
