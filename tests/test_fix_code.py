import textwrap
from tests.framework import AbstractFilePair
from tests.framework import in_test_function
from tests.framework import standard_test_spec
from tests.framework import SavingFixesCombination
from tests.framework import SavingFixesSUT
from tests.framework import SavingDoesNotTouchBrokenStuff
from tests.framework import add_tests


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


class TestSavingFixesCombination(SavingFixesCombination):
    pass


add_tests(TestSavingFixesCombination, fixable_combinations)


various_argument_lists = [[], ['arg'], ['arg1', 'arg2']]


def missing_function_in_source(argument_list):
    # having the import is important:
    # it allows us to check that the test wasn't touched
    lines = [arg + ' = None' for arg in argument_list]
    lines += ['bla = blubb.random_function(' + ', '.join(argument_list) + ')']
    test_code = in_test_function('\n'.join(lines))
    return AbstractFilePair('blubb', test=test_code)


missing_function_specs = [
    # create object of missing class with nullary constructor
    standard_test_spec("a = blubb.Something()"),
    standard_test_spec("a = blubb.fun()")]


# SUT is broken but fixable
fixable_SUTs = [
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
    standard_test_spec(  # argument names might clash with generated names
        """
        arg0 = 1
        arg1 = 1
        arg4 = 1
        bla = blubb.some_function(arg4, arg0, 42, arg1)
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
    ] + [missing_function_in_source(args) for args in various_argument_lists]\
      + missing_function_specs


class TestSavingFixesSUT(SavingFixesSUT):
    pass


add_tests(TestSavingFixesSUT, fixable_SUTs)


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


class TestSavingDoesNotTouchBrokenStuff(SavingDoesNotTouchBrokenStuff):
    pass


add_tests(TestSavingDoesNotTouchBrokenStuff, broken_pairs)
