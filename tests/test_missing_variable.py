from tests.framework import AbstractFilePair
from tests.framework import in_test_function
from tests.framework import standard_test_spec
from tests.framework import SavingFixesSUT
from tests.framework import fixing_test


variable_names = ('x', 'y')


def missing_variable_in_source(variable_name):
    test_code = in_test_function('bla = blubb.' + variable_name)
    return AbstractFilePair('blubb', test=test_code)


@fixing_test
class TestSavingFixesMissingVariables(SavingFixesSUT):
    tests = [
        standard_test_spec(  # add several variables to SUT
            """
            bla = blubb.x
            bla = blubb.y
            bla = blubb.z""")
        ] + [missing_variable_in_source(name) for name in variable_names]
