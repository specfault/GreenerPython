from tests.framework import standard_test_spec
from tests.framework import SavingFixesSUT
from tests.framework import fixing_test


@fixing_test
class TestSavingFixesMissingFunction(SavingFixesSUT):
    tests = [
        # create object of missing class with nullary constructor
        standard_test_spec("a = blubb.Something()"),
        standard_test_spec("a = blubb.fun()")]
