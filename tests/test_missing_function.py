from tests.framework import standard_test_spec
from tests.framework import SavingFixesSUT
from tests.framework import add_tests


missing_function_specs = [
    # create object of missing class with nullary constructor
    standard_test_spec("a = blubb.Something()"),
    standard_test_spec("a = blubb.fun()")]


class TestSavingFixesMissingFunction(SavingFixesSUT):
    pass


add_tests(TestSavingFixesMissingFunction, missing_function_specs)
