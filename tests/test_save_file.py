import vim
import pytest
import subprocess
import textwrap
from collections import namedtuple


fake_variable_name = "bla"


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


def create_failing_test(dir, name, test='', source=''):
    pair = create_file_pair(dir, name, test, source)
    assert not passes(pair.test)
    return pair


@pytest.fixture()
def missing_import_of_SUT(tmpdir, a_filename):
    test_code = textwrap.dedent("""\
            def test_something():
                some_variable = """ + a_filename + '.' + fake_variable_name + """
            """)
    source_code = fake_variable_name + " = None\n"
    pair = create_failing_test(tmpdir, a_filename,
                               test=test_code,
                               source=source_code)
    return pair.test


def test_saving_fixes_missing_import_of_SUT(missing_import_of_SUT):
    """saving a test file should add the missing import of the SUT"""
    vim.save_file(missing_import_of_SUT)
    assert passes(missing_import_of_SUT)  # missing import was fixed


@pytest.fixture()
def missing_import_of_system_lib(tmpdir):
    test_code = textwrap.dedent("""\
            def test_something():
                Point = collections.namedtuple('Point', ['x', 'y'])
            """)
    pair = create_failing_test(tmpdir, 'bla',
                               test=test_code)
    return pair.test


def test_saving_fixes_missing_import_of_system_lib(missing_import_of_system_lib):
    """saving a test file should add the missing import of the SUT"""
    vim.save_file(missing_import_of_system_lib)
    assert passes(missing_import_of_system_lib)  # missing import was fixed


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
    test_code = textwrap.dedent("""\
            def test_something():
                bla = lalelu.x
            """)
    pair = create_failing_test(tmpdir,
                               'test_missing_import_of_nonexistent_file.py',
                               test=test_code)
    return pair.test


def test_saving_does_not_import_nonexistent_files(
        missing_import_of_nonexistent_file):
    """saving a test file should add the missing import of the SUT"""
    old_content = missing_import_of_nonexistent_file.read()
    vim.save_file(missing_import_of_nonexistent_file)
    new_content = missing_import_of_nonexistent_file.read()
    assert old_content == new_content


variable_names = ('x', 'y')


@pytest.fixture(params=variable_names)
def a_variable(request):
    return request.param


@pytest.fixture()
def missing_variable_in_source(tmpdir, a_variable):
    test_code = textwrap.dedent("""\
            import blubb
            
            
            def test_something():
                bla = blubb.""" + a_variable + """
            """)
    pair = create_failing_test(tmpdir, 'blubb', test=test_code)
    return pair.test


@pytest.fixture()
def several_missing_variable_in_source(tmpdir):
    test_code = textwrap.dedent("""\
            import blubb
            
            
            def test_something():
                bla = blubb.x
                bla = blubb.y
                bla = blubb.z
            """)
    pair = create_failing_test(tmpdir, 'blubb', test=test_code)
    return pair.test


@pytest.fixture()
def missing_import_and_variable(tmpdir):
    test_code = textwrap.dedent("""\
            def test_something():
                bla = blubb.x
            """)
    pair = create_failing_test(tmpdir, 'blubb', test=test_code)
    return pair.test


def test_saving_adds_variable_to_source(missing_variable_in_source):
    old_test = missing_variable_in_source.read()
    vim.save_file(missing_variable_in_source)
    new_test = missing_variable_in_source.read()
    assert passes(missing_variable_in_source)  # problem was fixed
    assert old_test == new_test  # must not 'fix' stuff by deleting tests


def test_saving_adds_several_variables_to_source(several_missing_variable_in_source):
    old_test = several_missing_variable_in_source.read()
    vim.save_file(several_missing_variable_in_source)
    new_test = several_missing_variable_in_source.read()
    assert passes(several_missing_variable_in_source)  # problem was fixed
    assert old_test == new_test  # must not 'fix' stuff by deleting tests


def test_saving_adds__import_and_variable(missing_import_and_variable):
    old_test = missing_import_and_variable.read()
    vim.save_file(missing_import_and_variable)
    new_test = missing_import_and_variable.read()
    assert passes(missing_import_and_variable)  # problem was fixed
    assert old_test in new_test  # must not 'fix' stuff by deleting tests
