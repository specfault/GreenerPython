#!/usr/bin/env python3
import textwrap
from utils import name_of_called_object
from utils import function_declaration
from utils import line_with_init
from utils import indentation
from utils import find_dedent
from utils import line_with


def is_class_name(name):
    return name[0].isupper()


class MissingFunction:
    method_marker = 'self.'

    def __init__(self, name):
        self.name = name

    def fix(self, code):
        variable_stub = f'{self.name} = None\n'
        if variable_stub not in code.source:
            return code
        parts = code.source.split(variable_stub)
        assert len(parts) == 2
        if parts[0].endswith(self.method_marker):
            return self.convert_to_method(code)
        function_stub = function_declaration(self.name) + "\n    pass\n"
        new_content = parts[0] + function_stub + parts[1]
        return code.with_changed_source(new_content)

    def convert_to_method(self, code):
        lines = code.source.split('\n')
        init_pos = line_with_init(lines)
        indent = indentation(lines[init_pos])
        start = init_pos + 1
        end_of_init = find_dedent(lines[start:]) + start
        lines[end_of_init:end_of_init] = [f'{indent}def {self.name}():',
                                          f'{indent}    pass']
        offending_line = line_with(lines, f'self.{self.name} = None')
        del lines[offending_line]
        new_content = '\n'.join(lines)
        return code.with_changed_source(new_content)


class MissingClass:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        variable_stub = f'{self.name} = None\n'
        if variable_stub not in code.source:
            return code
        parts = code.source.split(variable_stub)
        assert len(parts) == 2
        class_stub = textwrap.dedent(f"""
            class {self.name}:
                def __init__(self):
                    pass
            """)
        new_content = parts[0] + class_stub + parts[1]
        return code.with_changed_source(new_content)


class MissingFunctionMatcher:
    def __init__(self, test):
        self.previous_line = ""
        self.test = test

    def __call__(self, line):
        if 'object is not callable' in line:
            name = name_of_called_object(self.test, self.previous_line)
            if is_class_name(name):
                return MissingClass(name)
            return MissingFunction(name)
        self.previous_line = line
        return None
