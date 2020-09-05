import unittest
import textwrap
import fix_code
from code import Code


fake_variable_name = "bla"


def in_memory_passes(pair):
    code = Code(pair.name, pair.test, pair.source)
    return fix_code.problem(code) is None


def passes(file_pair):
    name = file_pair.source.purebasename
    code = Code(name, file_pair.test.read(), file_pair.source.read())
    return fix_code.problem(code) is None


class AbstractFilePair(Code):
    def __init__(self, name, test='', source=''):
        self.name = name
        self.test = test
        self.source = source


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
    assert not in_memory_passes(a_failing_test_spec)
    return a_failing_test_spec


class VirtualSourceTestPair:
    def __init__(self, code):
        self.old_code = None
        self.code = code

    def save(self):
        self.old_code = self.code
        self.code = fix_code.fixed_code(self.code)

    def test_unchanged(self):
        return self.code.test == self.old_code.test

    def assert_test_unchanged(self):
        assert self.code.test == self.old_code.test

    def source_unchanged(self):
        return self.code.source == self.old_code.source

    def assert_source_unchanged(self):
        assert self.code.source == self.old_code.source

    def unchanged(self):
        return self.source_unchanged() and self.test_unchanged()

    def assert_unchanged(self):
        self.assert_test_unchanged()
        self.assert_source_unchanged()

    def passes(self):
        return fix_code.problem(self.code) is None


def failing_test_gets_fixed(fail):
    """saving fixes the test without touching the SUT"""
    def fun(self):
        pair = VirtualSourceTestPair(fail)
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
    assert not in_memory_passes(a_fixable_combination_spec)
    return a_fixable_combination_spec


def failing_combination_gets_fixed(a_fixable_combination):
    """saving fixes SUT and test"""
    def fun(self):
        pair = VirtualSourceTestPair(a_fixable_combination)
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
    standard_test_spec(  # call missing function with two literal arguments
        """
        bla = blubb.some_function(41, 42)
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
    standard_test_spec(  # add new argument before default argument
        """
        bla = blubb.some_function(1, a=42)
        """,
        """
        def some_function(a=42):
            pass
        """),
    standard_test_spec(  # argument names might clash with generated names
        """
        arg0 = 1
        arg1 = 1
        arg4 = 1
        bla = blubb.some_function(arg4, arg0, 42, arg1)
        """),
    # create object of missing class with nullary constructor
    standard_test_spec(
        """
        a = blubb.Something()
        """),
    # create object of missing class with unary constructor
    standard_test_spec(
        """
        a = blubb.Something(17)
        """),
    standard_test_spec(  # create object of missing class with attribute
        """
        a = blubb.Something()
        b = a.attribute
        """),
    standard_test_spec(  # create object of missing class with nullary method
        """
        a = blubb.Something()
        b = a.fun()
        """),
    standard_test_spec(  # create object of missing class with unary method
        """
        a = blubb.Something(42)
        """),
    standard_test_spec(  # fix missing self
        """
        a = blubb.Blubb()
        b = a.some_method(x = 3)
        """,
        """
        class Blubb:
            def __init__(self):
                pass
            def some_method(x = 13):
                pass
        """)
    ] + [missing_variable_in_source(name) for name in variable_names]\
      + [missing_function_in_source(args) for args in various_argument_lists]


def a_fixable_SUT(a_fixable_SUT_spec):
    # XXX catching errors early is nice and all
    # XXX but it causes problems:
    # XXX we get errors even when we don't actually run the tests!
    assert not in_memory_passes(a_fixable_SUT_spec)
    return a_fixable_SUT_spec


def failing_SUT_gets_fixed(a_fixable_SUT):
    """saving fixes the SUT without touching the test"""
    def fun(self):
        pair = VirtualSourceTestPair(a_fixable_SUT)
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
    assert not in_memory_passes(a_broken_pair_spec)
    return a_broken_pair_spec


def broken_stuff_is_not_touched(a_broken_pair):
    """saving only changes files that it can (partially) fix"""
    def fun(self):
        pair = VirtualSourceTestPair(a_broken_pair)
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


class TestGetArguments(unittest.TestCase):
    def test_no_arguments(self):
        self.assertEqual(fix_code.get_arguments("fun", "\tfun()"),
                         [])

    def test_numbers(self):
        # numbers get replaced with dummy values
        self.assertEqual(fix_code.get_arguments("fun", "\tfun(1, 2, 3)"),
                         ["1", "1", "1"])

    def test_variables(self):
        self.assertEqual(fix_code.get_arguments("fun", "\tfun(x, yy, zzz)"),
                         ["x", "yy", "zzz"])

    def test_keyword_arguments(self):
        # the names of the keyword arguments are respected
        # the values are replaced with a dummy value
        self.assertEqual(fix_code.get_arguments("fun", "\tfun(x=1, yy=2)"),
                         ["x=1", "yy=1"])

    def test_arrays(self):
        # complex expressions get replaced with dummy values
        self.assertEqual(fix_code.get_arguments("fun", "\tfun([], [1, 2])"),
                         ["1", "1"])

    def test_lists(self):
        # complex expressions get replaced with dummy values
        self.assertEqual(fix_code.get_arguments("fun", "\tfun((), (1, 2))"),
                         ["1", "1"])

    def test_nested_function_calls(self):
        # must pick out the arguments to fun, not the arguments to assertEqual
        self.assertEqual(fix_code.get_arguments("fun", "\tbla(fun(), 0)"),
                         [])
