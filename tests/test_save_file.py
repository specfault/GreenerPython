from . import vim
from tempfile import TemporaryDirectory
from py import path
import unittest
import subprocess
import textwrap
import save_file


fake_variable_name = "bla"


def save(file):
    subprocess.check_output(['save_file.py', str(file)])


def passes(file):
    return save_file.problem(file) is None


class AbstractFilePair:
    def __init__(self, name, test='', source=''):
        self.name = name
        self.test = test
        self.source = source


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
            import unittest


            class TestSomething(unittest.TestCase):
                def test_something(self):
                    some_variable = """ + filename + '.' + fake_variable_name + """
            """)
    source_code = fake_variable_name + " = None\n"
    return AbstractFilePair(filename, test=test_code, source=source_code)


filenames = ('bla', 'blubb')


def standard_test_spec(test, source='', name='blubb'):
    return AbstractFilePair(
        name,
        in_test_function(test),
        textwrap.dedent(source))


failing_test_specs = [
        standard_test_spec(  # missing import of lib
            "Point = collections.namedtuple('Point', ['x', 'y'])"),
        AbstractFilePair(  # broken import
            'blubb',
            'import lalelu\n' + in_test_function('self.assertTrue(True)')),
        AbstractFilePair(  # multiple broken imports
            'blubb',
            'import lalelu\nimport lalelu\n'
            + in_test_function('self.assertTrue(True)')),
        ] + [missing_import_of_SUT(name) for name in filenames]


def create_test_fail(a_failing_test_spec):
    pair = FilePair(TemporaryDirectory(), a_failing_test_spec)
    assert not passes(pair.test)
    return pair


class SourceTestPair:
    def __init__(self, pair):
        self.pair = pair
        self.source = None
        self.test = None

    def save(self):
        self.old_test = self.pair.test.read()
        self.old_source = self.pair.source.read()
        save(self.pair.test)

    def test_unchanged(self):
        return self.old_test == self.pair.test.read()

    def assert_test_unchanged(self):
        assert self.old_test == self.pair.test.read()

    def source_unchanged(self):
        return self.old_source == self.pair.source.read()

    def assert_source_unchanged(self):
        assert self.old_source == self.pair.source.read()

    def unchanged(self):
        return self.source_unchanged() and self.test_unchanged()

    def assert_unchanged(self):
        self.assert_test_unchanged()
        self.assert_source_unchanged()

    def passes(self):
        return passes(self.pair.test)


def failing_test_gets_fixed(fail):
    """saving fixes the test without touching the SUT"""
    def fun(self):
        pair = SourceTestPair(fail)
        pair.save()
        self.assertTrue(pair.source_unchanged())
        self.assertTrue(pair.passes())  # missing import was fixed
        # saving a second time shouldn't change anything
        pair.save()
        self.assertTrue(pair.source_unchanged())
        self.assertTrue(pair.test_unchanged())
    return fun


class TestSavingFixesTest(unittest.TestCase):
    pass


i = 0
for spec in failing_test_specs:
    fun = failing_test_gets_fixed(create_test_fail(spec))
    setattr(TestSavingFixesTest, f"test_{i}", fun)
    i += 1


# both, test and SUT, are broken but fixable
fixable_combinations = [
    AbstractFilePair(  # missing import in test, missing variable in SUT
        'blubb',
        textwrap.dedent("""\
            import unittest


            class TestSomething(unittest.TestCase):
                def test_something(self):
                    bla = blubb.x
            """))
    ]


def a_fixable_combination(a_fixable_combination_spec):
    pair = FilePair(TemporaryDirectory(), a_fixable_combination_spec)
    assert not passes(pair.test)
    return pair


def failing_combination_gets_fixed(a_fixable_combination):
    """saving fixes SUT and test"""
    def fun(self):
        pair = SourceTestPair(a_fixable_combination)
        pair.save()
        self.assertTrue(pair.passes())
        # saving a second time shouldn't change anything
        pair.save()
        self.assertTrue(pair.unchanged())
    return fun


class TestSavingFixesCombination(unittest.TestCase):
    pass


i = 0
for spec in fixable_combinations:
    fun = failing_combination_gets_fixed(a_fixable_combination(spec))
    setattr(TestSavingFixesCombination, f"test_{i}", fun)
    i += 1


def test_vim():
    """an end to end test:
    - vim correctly invokes the plugin
    - the plugin fixes SUT and test
    - saving a second time doesn't break anything"""
    spec = AbstractFilePair(  # missing import in test, missing variable in SUT
        'blubb',
        textwrap.dedent("""\
            import unittest


            class TestSomething(unittest.TestCase):
                def test_something(self):
                    bla = blubb.x
            """))
    file_pair = FilePair(TemporaryDirectory(), spec)
    assert not passes(file_pair.test)  # code needs fixing
    vim.save(file_pair.test)
    assert passes(file_pair.test)  # code was actually fixed
    # saving a second time shouldn't change anything
    old_test = file_pair.test.read()
    old_source = file_pair.source.read()
    vim.save(file_pair.test)
    new_test = file_pair.test.read()
    new_source = file_pair.source.read()
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
    standard_test_spec(  # add several variables to SUT
        """
        bla = blubb.x
        bla = blubb.y
        bla = blubb.z"""),
    standard_test_spec(  # call missing function with literal argument
        """
        arg = 1
        bla = blubb.some_function(arg, 42)
        """),
    standard_test_spec(  # missing function with default argument
        """
        arg = 1
        bla = blubb.some_function(a=42)
        bla = blubb.some_function(arg)
        """),
    standard_test_spec(  # missing function with normal and default argument
        """
        arg = 1
        bla = blubb.some_function(arg, a=42)
        bla = blubb.some_function(arg)
        """),
    standard_test_spec(  # argument names might clash with generated names
        """
        arg0 = 1
        arg1 = 1
        arg4 = 1
        bla = blubb.some_function(arg4, arg0, 42, arg1)
        """),
    standard_test_spec(  # create object of missing class
        """
        a = blubb.Something()
        """),
    standard_test_spec(  # create object of missing class with attribute
        """
        a = blubb.Something()
        b = a.attribute
        """),
    standard_test_spec(  # create object of missing class with function
        """
        a = blubb.Something()
        b = a.fun()
        """),
    standard_test_spec(  # create object of missing class with 1 argument
        """
        a = blubb.Something(42)
        """)
    ] + [missing_variable_in_source(name) for name in variable_names]\
      + [missing_function_in_source(args) for args in various_argument_lists]


def a_fixable_SUT(a_fixable_SUT_spec):
    pair = FilePair(TemporaryDirectory(), a_fixable_SUT_spec)
    assert not passes(pair.test)
    return pair


def failing_SUT_gets_fixed(a_fixable_SUT):
    """saving fixes the SUT without touching the test"""
    def fun(self):
        pair = SourceTestPair(a_fixable_SUT)
        pair.save()
        self.assertTrue(pair.test_unchanged())
        assert pair.passes()
        # saving a second time shouldn't change anything
        pair.save()
        self.assertTrue(pair.unchanged())
    return fun


class TestSavingFixesSUT(unittest.TestCase):
    pass


i = 0
for spec in fixable_SUTs:
    fun = failing_SUT_gets_fixed(a_fixable_SUT(spec))
    setattr(TestSavingFixesSUT, f"test_{i}", fun)
    i += 1


# SUT and test are broken beyond repair
broken_pairs = [
    standard_test_spec(  # different number of function arguments
        """
        bla = blubb.random_function(42)
        aaa = blubb.random_function(42, 37)
        """,
        """
        def random_function():
            pass
        """),
    standard_test_spec(  # using non-existent lib
        'bla = lalelu.x'),
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
    # adding strings and numbers is broken beyond repair
    # this should test return code JUST_BROKEN
    standard_test_spec(
        'a = 3 + "lol"'),
    standard_test_spec(  # broken function definition (missing colon)
        'bla = blubb.random_function(42)',
        """
        def random_function()
            pass
        """)
        ]


def a_broken_pair(a_broken_pair_spec):
    pair = FilePair(TemporaryDirectory(), a_broken_pair_spec)
    assert not passes(pair.test)
    return pair


def broken_stuff_is_not_touched(a_broken_pair):
    """saving only changes files that it can (partially) fix"""
    def fun(self):
        pair = SourceTestPair(a_broken_pair)
        pair.save()
        pair.assert_unchanged()
    return fun


class TestSavingDoesNotTouchBrokenStuff(unittest.TestCase):
    pass


i = 0
for spec in broken_pairs:
    fun = broken_stuff_is_not_touched(a_broken_pair(spec))
    setattr(TestSavingDoesNotTouchBrokenStuff, f"test_{i}", fun)
    i += 1
