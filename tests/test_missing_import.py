import textwrap
from tests.framework import AbstractFilePair
from tests.framework import standard_test_spec
from tests.framework import FailingTestGetsFixed
from tests.framework import add_tests


def missing_import_of_SUT(filename):
    fake_variable_name = "bla"
    test_code = textwrap.dedent("""\
            import unittest


            class TestSomething(unittest.TestCase):
                def test_something(self):
                    some_variable = """ + filename + '.' + fake_variable_name + """
            """)
    source_code = fake_variable_name + " = None\n"
    return AbstractFilePair(filename, test=test_code, source=source_code)


filenames = ('bla', 'blubb')


missing_import_specs = [
        standard_test_spec(  # missing import of lib
            "Point = collections.namedtuple('Point', ['x', 'y'])")
        ] + [missing_import_of_SUT(name) for name in filenames]


class TestSavingFixesMissingImport(FailingTestGetsFixed):
    pass


add_tests(TestSavingFixesMissingImport, missing_import_specs)
