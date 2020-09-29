from tests.framework import AbstractFilePair
from tests.framework import in_test_function
from tests.framework import FailingTestGetsFixed
from tests.framework import fixing_test


@fixing_test
class TestSavingFixesInvalidImport(FailingTestGetsFixed):
    tests = [AbstractFilePair(  # broken import
                 'blubb',
                 'import lalelu\n'
                 + in_test_function('self.assertTrue(True)')),
             AbstractFilePair(  # multiple broken imports
                 'blubb',
                 'import lalelu\nimport lalelu\n'
                 + in_test_function('self.assertTrue(True)'))]
