import vim
import pytest
import subprocess
import textwrap


fake_variable_name = "bla"


def passes(file):
    res = subprocess.call(['pytest', str(file)])
    return res == 0


filenames = ('bla', 'blubb')


@pytest.fixture(params=filenames)
def a_filename(request):
    return request.param


class AbstractFilePair:
    def __init__(self, name, test='', source=''):
        self.name = name
        self.test = test
        self.source = source


class FilePair:
    def __init__(self, dir, file_pair):
        base_dir = dir.mkdir(file_pair.name)
        test_dir = base_dir.mkdir('tests')

        self.source = base_dir.join(file_pair.name + '.py')
        self.source.write(file_pair.source)

        init_file = base_dir.join('__init__.py')
        init_file.write('from ' + file_pair.name + ' import *')
        init_file = test_dir.join('__init__.py')
        init_file.write('')  # empty init prevents weird name clashes

        self.test = test_dir.join('test_' + file_pair.name + '.py')
        self.test.write(file_pair.test)


def create_failing_test(dir, name, test='', source=''):
    pair = FilePair(dir, AbstractFilePair(name, test, source))
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


failing_test_specs = [
        AbstractFilePair(
            'bla',
            textwrap.dedent(
                """\
                    def test_something():
                        Point = collections.namedtuple('Point', ['x', 'y'])
                """))
        ]


@pytest.fixture(params=failing_test_specs)
def a_failing_test_spec(request):
    return request.param


@pytest.fixture()
def a_failing_test(tmpdir, a_failing_test_spec):
    pair = FilePair(tmpdir, a_failing_test_spec)
    assert not passes(pair.test)
    return pair


def test_saving_fixes_test(a_failing_test):
    """saving fixes the test without touching the SUT"""
    old_source = a_failing_test.source.read()
    vim.save_file(a_failing_test.test)
    new_source = a_failing_test.source.read()
    assert new_source == old_source  # didn't touch the SUT
    assert passes(a_failing_test.test)  # missing import was fixed


@pytest.fixture()
def missing_variable_in_lib(tmpdir):
    test_code = textwrap.dedent("""\
            def test_something():
                Point = collections.random_typo
            """)
    pair = create_failing_test(tmpdir, 'bla',
                               test=test_code)
    return pair


@pytest.fixture()
def abusing_variable_as_function_in_lib(tmpdir):
    test_code = textwrap.dedent("""\
            def test_something():
                Point = math.pi()
            """)
    pair = create_failing_test(tmpdir, 'bla',
                               test=test_code)
    return pair


@pytest.fixture()
def same_name_in_lib_and_SUT(tmpdir):
    test_code = textwrap.dedent("""\
            import math


            def test_something():
                Point = math.pi()
            """)
    source_code = textwrap.dedent("""\
            pi = None
            """)
    pair = create_failing_test(tmpdir, 'bla',
                               test=test_code,
                               source=source_code)
    return pair


@pytest.fixture()
def invalid_import(tmpdir):
    test_code = textwrap.dedent("""\
            import lalelu


            def test_something():
                assert(True)
            """)
    pair = create_failing_test(tmpdir, 'bla',
                               test=test_code)
    return pair


def test_saving_removes_invalid_import(
        invalid_import):
    """saving a test file should remove inalid imports
    it should not touch the source file"""
    SUT_old = invalid_import.source.read()
    vim.save_file(invalid_import.test)
    SUT_new = invalid_import.source.read()
    assert SUT_old == SUT_new
    assert passes(invalid_import.test)


@pytest.fixture()
def repeated_invalid_import(tmpdir):
    test_code = textwrap.dedent("""\
            import lalelu
            import lalelu


            def test_something():
                assert(True)
            """)
    pair = create_failing_test(tmpdir, 'bla',
                               test=test_code)
    return pair


def test_saving_fixes_multiple_invalid_imports(
        repeated_invalid_import):
    SUT_old = repeated_invalid_import.source.read()
    vim.save_file(repeated_invalid_import.test)
    SUT_new = repeated_invalid_import.source.read()
    assert SUT_old == SUT_new
    assert passes(repeated_invalid_import.test)


@pytest.fixture()
def complex_invalid_import(tmpdir):
    test_code = textwrap.dedent("""\
            from lalelu import *


            def test_something():
                assert(True)
            """)
    pair = create_failing_test(tmpdir, 'bla',
                               test=test_code)
    return pair


def test_saving_copes_with_complex_invalid_import(
        complex_invalid_import):
    """a kind of include that the program doesn't understand
    it shouldn't touch anything
    NOTE: Split in two when the program handles this:
    a) success test
    b) a more complex failure case"""
    SUT_old = complex_invalid_import.source.read()
    test_old = complex_invalid_import.test.read()
    vim.save_file(complex_invalid_import.test)
    SUT_new = complex_invalid_import.source.read()
    test_new = complex_invalid_import.test.read()
    assert SUT_old == SUT_new
    assert test_old == test_new


def test_saving_does_not_add_missing_variables_for_libs(
        missing_variable_in_lib):
    """saving a test file should not add missing variables of libs to the SUT
    for example, using collections.random_typo in test_SUT
    should not add random_typo to the SUT"""
    SUT_old = missing_variable_in_lib.source.read()
    vim.save_file(missing_variable_in_lib.test)
    SUT_new = missing_variable_in_lib.source.read()
    assert SUT_old == SUT_new


def test_saving_does_not_turn_variable_into_function_in_lib(
        abusing_variable_as_function_in_lib):
    """saving a test file should not add missing variables of libs to the SUT
    for example, using collections.random_typo in test_SUT
    should not add random_typo to the SUT"""
    SUT_old = abusing_variable_as_function_in_lib.source.read()
    vim.save_file(abusing_variable_as_function_in_lib.test)
    SUT_new = abusing_variable_as_function_in_lib.source.read()
    assert SUT_old == SUT_new


def test_saving_does_not_confuse_variables_in_lib_and_SUT(
        same_name_in_lib_and_SUT):
    SUT_old = same_name_in_lib_and_SUT.source.read()
    vim.save_file(same_name_in_lib_and_SUT.test)
    SUT_new = same_name_in_lib_and_SUT.source.read()
    assert SUT_old == SUT_new


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
                               'bla',
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


various_argument_lists = [[], ['arg'], ['arg1', 'arg2']]


@pytest.fixture(params=various_argument_lists)
def an_argument_list(request):
    return request.param


@pytest.fixture()
def missing_function_in_source(tmpdir, an_argument_list):
    # having the import is important:
    # it allows us to check that the test wasn't touched
    test_code = 'import blubb\n\n\ndef test_something():\n' +\
            '\n'.join(['    ' + arg + ' = None' for arg in an_argument_list])\
            + '\n    bla = blubb.random_function('\
            + ', '.join(an_argument_list) + ')\n'
    pair = create_failing_test(tmpdir, 'blubb', test=test_code)
    return pair.test


@pytest.fixture()
def strangely_formatted_function(tmpdir):
    """test handling of unrecognized functions
    for now an extra space inside the parens is enough"""
    # it allows us to check that the test wasn't touched
    test_code = textwrap.dedent("""\
            import blubb


            def test_something():
                bla = blubb.random_function(42)
            """)
    source_code = textwrap.dedent("""\
            def random_function( ):
                pass
            """)
    pair = create_failing_test(tmpdir, 'blubb',
                               test=test_code, source=source_code)
    return pair


@pytest.fixture()
def varying_number_of_args(tmpdir):
    """test handling of unrecognized functions
    for now an extra space inside the parens is enough"""
    # it allows us to check that the test wasn't touched
    test_code = textwrap.dedent("""\
            import blubb


            def test_something():
                bla = blubb.random_function(42)
                aaa = blubb.random_function(42, 37)
            """)
    source_code = textwrap.dedent("""\
            def random_function():
                pass
            """)
    pair = create_failing_test(tmpdir, 'blubb',
                               test=test_code, source=source_code)
    return pair


@pytest.fixture()
def missing_function_with_literals_in_call(tmpdir):
    # having the import is important:
    # it allows us to check that the test wasn't touched
    test_code = textwrap.dedent("""\
            import blubb


            def test_something():
                arg = 1
                bla = blubb.some_function(arg, 42)
            """)
    pair = create_failing_test(tmpdir, 'blubb', test=test_code)
    return pair.test


@pytest.fixture()
def literals_and_confusing_argument_names_in_call(
        tmpdir):
    """argument names look like autogenerated names
    makes things more interesting"""
    # having the import is important:
    # it allows us to check that the test wasn't touched
    test_code = textwrap.dedent("""\
            import blubb


            def test_something():
                arg0 = 1
                arg1 = 1
                arg4 = 1
                bla = blubb.some_function(arg4, arg0, 42, arg1)
            """)
    pair = create_failing_test(tmpdir, 'blubb', test=test_code)
    return pair.test


@pytest.fixture()
def several_missing_variables_in_source(tmpdir):
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


def test_saving_adds_function_to_source(missing_function_in_source):
    old_test = missing_function_in_source.read()
    vim.save_file(missing_function_in_source)
    new_test = missing_function_in_source.read()
    assert passes(missing_function_in_source)  # problem was fixed
    assert old_test == new_test  # must not 'fix' stuff by deleting tests


def test_saving_copes_with_strangely_formatted_function(
        strangely_formatted_function):
    old_test = strangely_formatted_function.test.read()
    old_source = strangely_formatted_function.source.read()
    vim.save_file(strangely_formatted_function.test)
    new_test = strangely_formatted_function.test.read()
    new_source = strangely_formatted_function.source.read()
    # should not touch stuff it doesn't understand
    assert old_test == new_test
    assert old_source == new_source


def test_saving_copes_with_variable_number_of_args(
        varying_number_of_args):
    old_test = varying_number_of_args.test.read()
    old_source = varying_number_of_args.source.read()
    vim.save_file(varying_number_of_args.test)
    new_test = varying_number_of_args.test.read()
    new_source = varying_number_of_args.source.read()
    # should not touch stuff it doesn't understand
    assert old_test == new_test
    assert old_source == new_source


def test_saving_copes_with_literals_in_function_call(
        missing_function_with_literals_in_call):
    old_test = missing_function_with_literals_in_call.read()
    vim.save_file(missing_function_with_literals_in_call)
    new_test = missing_function_with_literals_in_call.read()
    assert passes(missing_function_with_literals_in_call)  # problem was fixed
    assert old_test == new_test  # must not 'fix' stuff by deleting tests


def test_literals_and_confusing_argument_names_in_function_call(
        literals_and_confusing_argument_names_in_call):
    old_test = literals_and_confusing_argument_names_in_call.read()
    vim.save_file(literals_and_confusing_argument_names_in_call)
    new_test = literals_and_confusing_argument_names_in_call.read()
    # problem was fixed
    assert passes(literals_and_confusing_argument_names_in_call)
    assert old_test == new_test  # must not 'fix' stuff by deleting tests


def test_saving_adds_several_variables_to_source(
        several_missing_variables_in_source):
    old_test = several_missing_variables_in_source.read()
    vim.save_file(several_missing_variables_in_source)
    new_test = several_missing_variables_in_source.read()
    assert passes(several_missing_variables_in_source)  # problem was fixed
    assert old_test == new_test  # must not 'fix' stuff by deleting tests


def test_saving_adds_import_and_variable(missing_import_and_variable):
    old_test = missing_import_and_variable.read()
    vim.save_file(missing_import_and_variable)
    new_test = missing_import_and_variable.read()
    assert passes(missing_import_and_variable)  # problem was fixed
    assert old_test in new_test  # must not 'fix' stuff by deleting tests
