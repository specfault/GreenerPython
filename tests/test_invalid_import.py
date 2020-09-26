from tests.framework import AbstractFilePair
from tests.framework import in_test_function
from tests.framework import FailingTestGetsFixed
from tests.framework import add_tests


invalid_import_specs = [
        AbstractFilePair(  # broken import
            'blubb',
            'import lalelu\n' + in_test_function('self.assertTrue(True)')),
        AbstractFilePair(  # multiple broken imports
            'blubb',
            'import lalelu\nimport lalelu\n'
            + in_test_function('self.assertTrue(True)'))]


class TestSavingFixesInvalidImport(FailingTestGetsFixed):
    pass


add_tests(TestSavingFixesInvalidImport, invalid_import_specs)
