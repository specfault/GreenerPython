import textwrap


def create(test_name):
    prefix = "test_"
    file_ending = ".py"
    assert test_name.startswith(prefix)
    assert test_name.endswith(file_ending)
    name = test_name[len(prefix):]
    name = name[:-len(file_ending)]
    return textwrap.dedent(f"""\
        import unittest
        import {name}

        class Test{name.capitalize()}(unittest.TestCase):
            pass
        """)
