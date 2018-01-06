import vim
import pytest
import subprocess


def missing_import(name):
    return 'def test_something():\n    some_variable = ' + name + '.bla'


source_file_with_variable = """bla = None"""


def passes(file):
    res = subprocess.call(['pytest', str(file)])
    return res == 0


filenames = ('bla', 'blubb')


@pytest.fixture(params=filenames)
def a_filename(request):
    return request.param


@pytest.fixture()
def file_with_missing_import(tmpdir, a_filename):
    base_dir = tmpdir.mkdir(a_filename)
    test_dir = base_dir.mkdir('tests')
    source_file = base_dir.join(a_filename + '.py')
    source_file.write(source_file_with_variable)
    init_file = base_dir.join('__init__.py')
    init_file.write('from ' + a_filename + ' import *')
    test_file = test_dir.join('test_' + a_filename + '.py')
    test_file.write(missing_import(a_filename))
    init_file = test_dir.join('__init__.py')
    init_file.write('')  # empty init prevents weird name clashes
    assert not passes(test_file)  # catches the missing import
    return test_file


def test_saving_fixes_missing_import(file_with_missing_import):
    """saving a test file should add the missing import of the source file"""
    vim.save_file(file_with_missing_import)
    assert passes(file_with_missing_import)  # missing import was fixed


def test_saving_a_second_time_leaves_file_unchanged(file_with_missing_import):
    """the saving routine should apply all fixes the first time it's run
    afterwards the file is either
    a) correct
    b) broken in an unfixable way
    Therefore, the second run shouldn't change anything"""
    vim.save_file(file_with_missing_import)
    old_content = file_with_missing_import.read()
    vim.save_file(file_with_missing_import)
    new_content = file_with_missing_import.read()
    assert old_content == new_content
