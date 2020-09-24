import unittest
from missing_argument import get_arguments


class TestGetArguments(unittest.TestCase):
    def test_no_arguments(self):
        self.assertEqual(get_arguments("fun", "\tfun()"),
                         [])

    def test_numbers(self):
        # numbers get replaced with dummy values
        self.assertEqual(get_arguments("fun", "\tfun(1, 2, 3)"),
                         ["1", "1", "1"])

    def test_variables(self):
        self.assertEqual(get_arguments("fun", "\tfun(x, yy, zzz)"),
                         ["x", "yy", "zzz"])

    def test_keyword_arguments(self):
        # the names of the keyword arguments are respected
        # the values are replaced with a dummy value
        self.assertEqual(get_arguments("fun", "\tfun(x=1, yy=2)"),
                         ["x=1", "yy=1"])

    def test_arrays(self):
        # complex expressions get replaced with dummy values
        self.assertEqual(get_arguments("fun", "\tfun([], [1, 2])"),
                         ["1", "1"])

    def test_lists(self):
        # complex expressions get replaced with dummy values
        self.assertEqual(get_arguments("fun", "\tfun((), (1, 2))"),
                         ["1", "1"])

    def test_nested_function_calls(self):
        # must pick out the arguments to fun, not the arguments to assertEqual
        self.assertEqual(get_arguments("fun", "\tbla(fun(), 0)"),
                         [])
