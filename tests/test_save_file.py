import vim
import pytest
import subprocess
import textwrap
from collections import namedtuple


fake_variable_name = "bla"


def code_with_missing_import_of_SUT(name):
    return textwrap.dedent("""\
            def test_something():
                some_variable = """ + name + '.' + fake_variable_name + """
            """)


source_file_with_variable = fake_variable_name + " = None\n"


def passes(file):
    res = subprocess.call(['pytest', str(file)])
    return res == 0


filenames = ('bla', 'blubb')


@pytest.fixture(params=filenames)
def a_filename(request):
    return request.param


FilePair = namedtuple('FilePair', ['source', 'test'])


def create_file_pair(dir, name, test='', source=''):
    base_dir = dir.mkdir(name)
    test_dir = base_dir.mkdir('tests')
    source_file = base_dir.join(name + '.py')
    source_file.write(source)
    init_file = base_dir.join('__init__.py')
    init_file.write('from ' + name + ' import *')
    test_file = test_dir.join('test_' + name + '.py')
    test_file.write(test)
    init_file = test_dir.join('__init__.py')
    init_file.write('')  # empty init prevents weird name clashes
    return FilePair(source=source_file, test=test_file)


@pytest.fixture()
def missing_import_of_SUT(tmpdir, a_filename):
    pair = create_file_pair(tmpdir, a_filename,
                            test=code_with_missing_import_of_SUT(a_filename),
                            source=source_file_with_variable)
    assert not passes(pair.test)  # catches the missing import
    return pair.test


def test_saving_fixes_missing_import_of_SUT(missing_import_of_SUT):
    """saving a test file should add the missing import of the SUT"""
    vim.save_file(missing_import_of_SUT)
    assert passes(missing_import_of_SUT)  # missing import was fixed


def test_saving_a_second_time_leaves_file_unchanged(missing_import_of_SUT):
    """the saving routine should apply all fixes the first time it's run
    afterwards the file is either
    a) correct
    b) broken in an unfixable way
    Therefore, the second run shouldn't change anything"""
    vim.save_file(missing_import_of_SUT)
    old_content = missing_import_of_SUT.read()
    vim.save_file(missing_import_of_SUT)
    new_content = missing_import_of_SUT.read()
    assert old_content == new_content


@pytest.fixture()
def missing_import_of_nonexistent_file(tmpdir):
    test_file = tmpdir.join('test_missing_import_of_nonexistent_file.py')
    test_file.write(textwrap.dedent("""\
            def test_something():
                bla = lalelu.x
            """))
    assert not passes(test_file)  # catches the missing import
    return test_file


def test_saving_does_not_import_nonexistent_files(
        missing_import_of_nonexistent_file):
    """saving a test file should add the missing import of the SUT"""
    old_content = missing_import_of_nonexistent_file.read()
    vim.save_file(missing_import_of_nonexistent_file)
    new_content = missing_import_of_nonexistent_file.read()
    assert old_content == new_content
