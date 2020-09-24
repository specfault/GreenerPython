import fix_code
import textwrap
from code import Code


def in_memory_passes(pair):
    code = Code(pair.name, pair.test, pair.source)
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


def standard_test_spec(test, source='', name='blubb'):
    return AbstractFilePair(
        name,
        in_test_function(test),
        textwrap.dedent(source))


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


def failing_test_gets_fixed(spec):
    """saving fixes the test without touching the SUT"""
    fail = create_test_fail(spec)

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


def a_fixable_SUT(a_fixable_SUT_spec):
    # XXX catching errors early is nice and all
    # XXX but it causes problems:
    # XXX we get errors even when we don't actually run the tests!
    assert not in_memory_passes(a_fixable_SUT_spec)
    return a_fixable_SUT_spec


def failing_SUT_gets_fixed(spec):
    """saving fixes the SUT without touching the test"""
    def fun(self):
        pair = VirtualSourceTestPair(a_fixable_SUT(spec))
        pair.save()
        self.assertTrue(pair.test_unchanged())
        assert pair.passes()
        # saving a second time shouldn't change anything
        pair.save()
        self.assertTrue(pair.unchanged())
    return fun


def a_fixable_combination(a_fixable_combination_spec):
    assert not in_memory_passes(a_fixable_combination_spec)
    return a_fixable_combination_spec


def failing_combination_gets_fixed(spec):
    """saving fixes SUT and test"""
    def fun(self):
        pair = VirtualSourceTestPair(a_fixable_combination(spec))
        pair.save()
        self.assertTrue(pair.passes())
        # saving a second time shouldn't change anything
        pair.save()
        self.assertTrue(pair.unchanged())
    return fun


def a_broken_pair(a_broken_pair_spec):
    assert not in_memory_passes(a_broken_pair_spec)
    return a_broken_pair_spec


def broken_stuff_is_not_touched(spec):
    """saving only changes files that it can (partially) fix"""
    def fun(self):
        pair = VirtualSourceTestPair(a_broken_pair(spec))
        pair.save()
        pair.assert_unchanged()
    return fun
