import textwrap


def create(test_name):
    prefix = "test_"
    assert test_name.startswith(prefix)
    name = test_name[len(prefix):]
    return textwrap.dedent(f"""
        import unittest
        import {name}

        class Test{name.capitalize()}(unittest.TestCase):
            pass""")
