#!/usr/bin/env python3


import sys
from py import path
import ast
import textwrap


source = [None]
source_name2 = [None]
test = [None]


g = globals()
local_variables = locals()


def check(name, source_code, test_code):
    tmp = test_code.split("\n")
    SUT_import = f"import {name}"
    contains_SUT_import = True in [SUT_import in el for el in tmp]
    tmp = [el for el in tmp if SUT_import not in el]
    test[0] = '\n'.join(tmp)
    source[0] = source_code
    source_name2.insert(0, name)
    local_variables.pop(source_name2[0], None)
    # make sure you don't include unittest
    # this way, we notice if the test code forgets to include it
    # I couldn't find a way to unittest this
    # probably because unittest is imported practically  everywhere
    # also, imports seem to leak like crazy
    # apparently, I haven't fully understood Python's module system
    code = textwrap.dedent(f"""
        from types import ModuleType

        """)
    if contains_SUT_import:
        code += textwrap.dedent(f"""
            {source_name2[0]} = ModuleType(source_name2[0])
            exec(source[0], globals(), {source_name2[0]}.__dict__)
            """)
    code += textwrap.dedent(f"""
        exec(test[0], globals(), locals())
        suite = unittest.defaultTestLoader.loadTestsFromModule(
            sys.modules[__name__])
        res = unittest.TestResult()
        suite.run(res)
        """)
    try:
        exec(code, g, local_variables)
    except Exception as e:
        return str(e)
    tmp = local_variables['res'].errors
    if tmp:
        return tmp[0][1]
    return None


class JustBroken:
    def __init__(self):
        pass


class MissingImport:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        return code.with_changed_test(f'import {self.name}\n\n\n' + code.test)


class InvalidImport:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        marker = f'import {self.name}\n'
        parts = code.test.split(marker)
        # otherwise it's some weird import and we're not sure how to fix it
        if len(parts) >= 2:
            return code.with_changed_test(''.join(parts))
        return code


class MissingVariable:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        return code.with_changed_source(f'{self.name} = None\n\n\n'
                                        + code.source)


def line_with(lines, text):
    for i in range(len(lines)):
        if text in lines[i]:
            return i
    return len(lines)


def line_with_class_definition(lines, class_name):
    return line_with(lines, f'class {class_name}')


def line_with_init(lines, class_name=''):
    index = line_with_class_definition(lines, class_name)
    delta = line_with(lines[index:], '__init__')
    return index + delta


def indentation(line):
    return line[:len(line) - len(line.lstrip())]


class MissingAttribute:
    def __init__(self, class_name, attribute_name):
        self.class_name = class_name
        self.attribute_name = attribute_name

    def fix(self, code):
        lines = code.source.split('\n')
        index = line_with_init(lines, self.class_name)
        pos = index + 1  # insert attribute here
        indent = indentation(lines[pos])
        lines.insert(pos, f'{indent}self.{self.attribute_name} = None')
        return code.with_changed_source('\n'.join(lines))


def numeric_indentation(line):
    return len(indentation(line))


def find_dedent(lines):
    indent = numeric_indentation(lines[0])
    for i in range(len(lines)):
        # ignore empty lines
        if lines[i] and (numeric_indentation(lines[i]) < indent):
            return i
    return len(lines)


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


def starting_at(marker, text):
    return text[text.find(marker):]


def is_method(name, source):
    stub = start_of_function_declaration(name)
    lines = source.split('\n')
    pos = line_with(lines, stub)
    pos = pos - find_dedent(lines[pos::-1])
    if pos < 0:
        # cannot be part of a class because we've run out of code
        return False
    return lines[pos].lstrip().startswith('class')


class MissingArgument:
    markers = ('() takes ',
               '() got an unexpected keyword argument ',
               '() got multiple values for argument')

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def fix(self, code):
        if is_method(self.name, code.source):
            # method -> add self argument
            self.args.insert(0, 'self')
        stub = start_of_function_declaration(self.name)
        if stub not in code.source:
            return code
        parts = code.source.split(stub)
        assert len(parts) == 2
        stub_with_arg = stub + ', '.join(self.args)
        new_content = parts[0] + stub_with_arg + starting_at('):', parts[1])
        return code.with_changed_source(new_content)


def get_source_name(test_file):
    filename = test_file.purebasename
    assert filename.startswith('test_')
    return filename[len('test_'):]


def identifier(name):
    res = ast.parse(name)
    return type(res.body[0].value) == ast.Name


def keyword_argument(name):
    return '=' in name


def fix_literals(args):
    """make up argument names for literals in call"""
    res = args[:]
    index = 0
    for i, el in enumerate(res):
        if not (identifier(el) or keyword_argument(el)):
            while f'arg{index}' in res:
                index += 1
            res[i] = f'arg{index}'
    return res


def arg_marker_type(line):
    for m in MissingArgument.markers:
        if m in line:
            return m
    return None


def get_broken_line_number(code, line):
    # import was stripped -> increment line number
    return int(line.split('line ')[-1].split(',')[0]) + 1


def get_broken_line(code, line):
    return code.split('\n')[get_broken_line_number(code, line) - 1]


def function_name(line, marker):
    parts = line.split(marker)
    tmp = parts[0]
    return tmp.split(' ')[-1]


def get_arguments(test_code, message):
    before_args = '('
    previous = get_broken_line(test_code, message)
    parts = previous.split(before_args)
    s = '('.join(parts[1:])
    arg_string = s.split(')')[0]
    args = [el.strip() for el in arg_string.split(',')]
    return [el for el in args if el]  # get rid of empty strings


def match_missing_attribute(line):
    marker = "' object has no attribute '"
    if marker in line:
        parts = line.split(marker)
        class_name = parts[0].split("'")[-1]
        attribute_name = parts[1].split("'")[0]
        return MissingAttribute(class_name, attribute_name)
    return None


def match_missing_variable(line):
    marker = "has no attribute '"
    if marker in line:
        parts = line.split(marker)
        return MissingVariable(parts[1].split("'")[0])
    return None


def match_missing_import(line):
    # do not require the prefix NameError
    # you only get that when the unittest could be started!
    marker = "name '"
    if (marker in line) and ("' is not defined" in line):
        parts = line.split(marker)
        return MissingImport(parts[1].split("'")[0])
    return None


def problem(code):
    error = check(code.name, code.source, code.test)
    if error is None:
        return None
    previous_line = ''
    for line in error.split('\n'):
        match = match_missing_attribute(line)
        if match:
            return match
        match = match_missing_variable(line)
        if match:
            return match
        match = match_missing_import(line)
        if match:
            return match
        marker = "No module named '"
        if marker in line:
            parts = line.split(marker)
            assert len(parts) == 2
            name = parts[1].split("'")[0]
            return InvalidImport(name)
        if 'object is not callable' in line:
            previous = get_broken_line(code.test, previous_line)
            tmp = previous.split('(')[-2]
            name = tmp.split('.')[-1]
            if name[0].isupper():
                return MissingClass(name)
            return MissingFunction(name)
        marker = arg_marker_type(line)
        if marker:
            name = function_name(line, marker)
            args = get_arguments(code.test, previous_line)
            return MissingArgument(name, fix_literals(args))
        previous_line = line
    return JustBroken()


def improved(old_issue, new_issue):
    if (not new_issue):
        return True
    if (type(old_issue) == MissingImport)\
            and (type(new_issue) == InvalidImport):
        return False
    if type(old_issue) != type(new_issue):
        return True
    return old_issue.name != new_issue.name


def start_of_function_declaration(name):
    return f'def {name}('


def function_declaration(name):
    return start_of_function_declaration(name) + '):'


class Code:
    def __init__(self, name, test, source):
        self.name = name
        self.test = test
        self.source = source

    def with_changed_source(self, source):
        return Code(self.name, self.test, source)

    def with_changed_test(self, test):
        return Code(self.name, test, self.source)


def fixed_code(broken_code):
    code = broken_code
    issues = problem(code)
    while issues and (type(issues) != JustBroken):
        issue = issues
        new_code = issue.fix(code)
        new_issue = problem(new_code)
        if not improved(issues, new_issue):
            break
        code = new_code
        issues = new_issue
    return code


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    source_name = get_source_name(file)
    folder = file.dirname
    folder = path.local(folder).join('..')
    name = get_source_name(file)
    source_file = folder.join(name + '.py')
    res = fixed_code(Code(name, file.read(), source_file.read()))
    file.write(res.test)
    source_file.write(res.source)
