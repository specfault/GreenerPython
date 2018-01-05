import pytest
import subprocess
from py import path


def executing_file():
    return path.local(__file__)


def directory_of_executing_file():
    return path.local(executing_file().dirname)


def create_file(file):
    dir = path.local(file.dirname)
    script = dir.join('vimsrcipt.txt')
    script.write(":e " + str(file) + "\n" + ":wq\n")
    test_dir = directory_of_executing_file()
    vimrc = test_dir.join('.vimrc')
    command = ['vim', '-u', str(vimrc), '-s', str(script)]
    print(command)
    res = subprocess.call(command)
    assert res == 0


save_file = create_file


missing_import = """def test_bla():
    blubb = bla.bla"""


source_file_with_variable = """bla = None"""


def passes(file):
    res = subprocess.call(['pytest', str(file)])
    return res == 0


@pytest.fixture()
def file_with_missing_import(tmpdir):
    base_dir = tmpdir.mkdir('bla')
    test_dir = base_dir.mkdir('tests')
    source_file = base_dir.join("bla.py")
    source_file.write(source_file_with_variable)
    init_file = base_dir.join('__init__.py')
    init_file.write('from bla import *')
    test_file = test_dir.join("test_bla.py")
    test_file.write(missing_import)
    init_file = test_dir.join('__init__.py')
    init_file.write('')  # empty init prevents weird name clashes
    assert not passes(test_file)  # catches the missing import
    return test_file


def test_saving_fixes_missing_import(file_with_missing_import):
    """saving a test file should add the missing import of the source file"""
    save_file(file_with_missing_import)
    assert passes(file_with_missing_import)  # missing import was fixed


def test_saving_a_second_time_leaves_file_unchanged(file_with_missing_import):
    """the saving routine should apply all fixes the first time it's run
    afterwards the file is either
    a) correct
    b) broken in an unfixable way
    Therefore, the second run shouldn't change anything"""
    save_file(file_with_missing_import)
    old_content = file_with_missing_import.read()
    save_file(file_with_missing_import)
    new_content = file_with_missing_import.read()
    assert old_content == new_content
