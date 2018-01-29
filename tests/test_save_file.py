import vim
import pytest
import subprocess
import textwrap


fake_variable_name = "bla"


def passes(file):
    res = subprocess.call(['pytest', str(file)])
    return res == 0


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


def in_test_function(code, name='blubb'):
    res = 'import ' + name
    res += textwrap.dedent("""
        import unittest


        class TestSomething(unittest.TestCase):
            def test_something(self):
        """)
    code = textwrap.dedent(code)
    code_lines = code.split('\n')
    res += '\n'.join(['        ' + line for line in code_lines])
    return res + '\n'


def missing_import_of_SUT(filename):
    test_code = textwrap.dedent("""\
            def test_something():
                some_variable = """ + filename + '.' + fake_variable_name + """
            """)
    source_code = fake_variable_name + " = None\n"
    return AbstractFilePair(filename, test=test_code, source=source_code)


filenames = ('bla', 'blubb')


failing_test_specs = [
        AbstractFilePair(  # missing import of lib
            'blubb',
            in_test_function("""
                Point = collections.namedtuple('Point', ['x', 'y'])
                """)),
        AbstractFilePair(  # broken import
            'bla',
            'import lalelu\n' + in_test_function('self.assertTrue(True)')),
        AbstractFilePair(  # multiple broken imports
            'bla',
            'import lalelu\nimport lalelu\n'
            + in_test_function('self.assertTrue(True)'))
        ] + [missing_import_of_SUT(name) for name in filenames]


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
    vim.save(a_failing_test.test)
    new_source = a_failing_test.source.read()
    assert new_source == old_source  # didn't touch the SUT
    assert passes(a_failing_test.test)  # missing import was fixed
    # saving a second time shouldn't change anything
    old_test = a_failing_test.test.read()
    vim.save(a_failing_test.test)
    new_source = a_failing_test.source.read()
    new_test = a_failing_test.test.read()
    assert new_source == old_source
    assert new_test == old_test


# both, test and SUT, are broken but fixable
fixable_combinations = [
    AbstractFilePair(  # missing import in test, missing variable in SUT
        'blubb',
        textwrap.dedent("""\
            def test_something():
                bla = blubb.x
            """))
    ]


@pytest.fixture(params=fixable_combinations)
def a_fixable_combination_spec(request):
    return request.param


@pytest.fixture()
def a_fixable_combination(tmpdir, a_fixable_combination_spec):
    pair = FilePair(tmpdir, a_fixable_combination_spec)
    assert not passes(pair.test)
    return pair


def test_saving_fixes_combination(a_fixable_combination):
    """saving fixes SUT and test"""
    vim.save(a_fixable_combination.test)
    assert passes(a_fixable_combination.test)  # missing import was fixed
    # saving a second time shouldn't change anything
    old_test = a_fixable_combination.test.read()
    old_source = a_fixable_combination.source.read()
    vim.save(a_fixable_combination.test)
    new_test = a_fixable_combination.test.read()
    new_source = a_fixable_combination.source.read()
    assert new_source == old_source
    assert new_test == old_test


variable_names = ('x', 'y')


def missing_variable_in_source(variable_name):
    test_code = in_test_function('bla = blubb.' + variable_name)
    return AbstractFilePair('blubb', test=test_code)


various_argument_lists = [[], ['arg'], ['arg1', 'arg2']]


def missing_function_in_source(argument_list):
    # having the import is important:
    # it allows us to check that the test wasn't touched
    lines = [arg + ' = None' for arg in argument_list]
    lines += ['bla = blubb.random_function(' + ', '.join(argument_list) + ')']
    test_code = in_test_function('\n'.join(lines))
    return AbstractFilePair('blubb', test=test_code)


# SUT is broken but fixable
fixable_SUTs = [
    AbstractFilePair(  # add several variables to SUT
        'blubb',
        in_test_function("""
            bla = blubb.x
            bla = blubb.y
            bla = blubb.z""")),
    AbstractFilePair(  # call missing function with literal argument
        'blubb',
        in_test_function("""
            arg = 1
            bla = blubb.some_function(arg, 42)
            """)),
    AbstractFilePair(  # argument names might clash with generated names
        'blubb',
        in_test_function("""
            arg0 = 1
            arg1 = 1
            arg4 = 1
            bla = blubb.some_function(arg4, arg0, 42, arg1)
            """))
    ] + [missing_variable_in_source(name) for name in variable_names]\
        + [missing_function_in_source(args) for args in various_argument_lists]


@pytest.fixture(params=fixable_SUTs)
def a_fixable_SUT_spec(request):
    return request.param


@pytest.fixture()
def a_fixable_SUT(tmpdir, a_fixable_SUT_spec):
    pair = FilePair(tmpdir, a_fixable_SUT_spec)
    assert not passes(pair.test)
    return pair


def test_saving_fixes_SUT(a_fixable_SUT):
    """saving fixes the SUT without touching the test"""
    old_test = a_fixable_SUT.test.read()
    vim.save(a_fixable_SUT.test)
    new_test = a_fixable_SUT.test.read()
    assert new_test == old_test  # only SUT was touched
    assert passes(a_fixable_SUT.test)  # errors were fixed
    # saving a second time shouldn't change anything
    old_test = a_fixable_SUT.test.read()
    old_source = a_fixable_SUT.source.read()
    vim.save(a_fixable_SUT.test)
    new_test = a_fixable_SUT.test.read()
    new_source = a_fixable_SUT.source.read()
    assert new_source == old_source
    assert new_test == old_test


# SUT and test are broken beyond repair
broken_pairs = [
    AbstractFilePair(  # different number of function arguments
        'blubb',
        in_test_function("""
            bla = blubb.random_function(42)
            aaa = blubb.random_function(42, 37)
            """),
        textwrap.dedent("""\
            def random_function():
                pass
            """)),
    AbstractFilePair(  # using non-existent lib
        'blubb',
        in_test_function('bla = lalelu.x')),
    # using nonexistent lib variable
    AbstractFilePair(
        'blubb',
        'import collections\n'
        + in_test_function('Point = collections.random_typo')),
    # using lib variable as function
    AbstractFilePair(
        'blubb',
        'import math\n' + in_test_function('Point = math.pi()')),
    # using lib variable as function
    # SUT having same variable name makes the problem harder
    AbstractFilePair(
        'blubb',
        'import math\n' + in_test_function('Point = math.pi()'),
        'pi = None\n'),
    # cryptic and broken import
    # (doesn't yet deal with wildcards)
    AbstractFilePair(
        'blubb',
        'from lalelu import *\n' + in_test_function('self.assertTrue(True)')),
    AbstractFilePair(  # broken function definition (extra space)
        'blubb',
        in_test_function('bla = blubb.random_function(42)'),
        textwrap.dedent("""\
            def random_function( ):
                pass
            """))
        ]


@pytest.fixture(params=broken_pairs)
def a_broken_pair_spec(request):
    return request.param


@pytest.fixture()
def a_broken_pair(tmpdir, a_broken_pair_spec):
    pair = FilePair(tmpdir, a_broken_pair_spec)
    assert not passes(pair.test)
    return pair


def test_saving_copes_with_broken_pair(a_broken_pair):
    """saving only changes files that it can (partially) fix"""
    old_test = a_broken_pair.test.read()
    old_source = a_broken_pair.source.read()
    vim.save(a_broken_pair.test)
    new_test = a_broken_pair.test.read()
    new_source = a_broken_pair.source.read()
    assert new_source == old_source
    assert new_test == old_test
