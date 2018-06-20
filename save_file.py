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
    code = textwrap.dedent(f"""
        import unittest
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


class CurrentFile:
    def __init__(self, file):
        self.file = file
        self.content = file.read()

    def restore(self):
        self.file.write(self.content)

    def write(self, content):
        self.file.write(content)


class JustBroken:
    def __init__(self, file):
        self.file = CurrentFile(file)

    def fix(self):
        pass


class MissingImport:
    def __init__(self, name, file):
        self.name = name
        self.file = CurrentFile(file)

    def fix(self):
        self.file.write(f'import {issue.name}\n\n\n' + self.file.content)


class InvalidImport:
    def __init__(self, name, file):
        self.name = name
        self.file = CurrentFile(file)

    def fix(self):
        marker = f'import {self.name}\n'
        parts = self.file.content.split(marker)
        # otherwise it's some weird import and we're not sure how to fix it
        if len(parts) >= 2:
            self.file.write(''.join(parts))


class MissingVariable:
    def __init__(self, name, file):
        self.name = name
        source_name = get_source_name(file)
        self.file = CurrentFile(path.local(
            file.dirname).join('..').join(f'{source_name}.py'))

    def fix(self):
        self.file.write(f'{self.name} = None\n\n\n' + self.file.content)


def line_with(lines, text):
    for i in range(len(lines)):
        if text in lines[i]:
            return i
    return None


def line_with_class_definition(lines, class_name):
    return line_with(lines, f'class {class_name}')


def line_with_init(lines, class_name=''):
    index = line_with_class_definition(lines, class_name)
    if index is None:
        return None
    delta = line_with(lines[index:], '__init__')
    if delta is None:
        return None
    return index + delta


def indentation(line):
    return line[:len(line) - len(line.lstrip())]


class MissingAttribute:
    def __init__(self, class_name, attribute_name, file):
        self.class_name = class_name
        self.attribute_name = attribute_name
        source_name = get_source_name(file)
        self.file = CurrentFile(path.local(
            file.dirname).join('..').join(f'{source_name}.py'))

    def fix(self):
        lines = self.file.content.split('\n')
        index = line_with_init(lines, self.class_name)
        pos = index + 1  # insert attribute here
        indent = indentation(lines[pos])
        lines.insert(pos, f'{indent}self.{self.attribute_name} = None')
        self.file.write('\n'.join(lines))


def numeric_indentation(line):
    return len(indentation(line))


def find_dedent(lines):
    indent = numeric_indentation(lines[0])
    for i in range(len(lines)):
        if numeric_indentation(lines[i]) < indent:
            return i
    return None


class MissingFunction:
    method_marker = 'self.'

    def __init__(self, name, file):
        self.name = name
        source_name = get_source_name(file)
        self.file = CurrentFile(path.local(
            file.dirname).join('..').join(f'{source_name}.py'))

    def fix(self):
        variable_stub = f'{issue.name} = None\n'
        if variable_stub not in self.file.content:
            return
        parts = self.file.content.split(variable_stub)
        assert len(parts) == 2
        if parts[0].endswith(self.method_marker):
            return self.convert_to_method()
        function_stub = function_declaration(self.name) + "\n    pass\n"
        new_content = parts[0] + function_stub + parts[1]
        self.file.write(new_content)

    def convert_to_method(self):
        lines = self.file.content.split('\n')
        init_pos = line_with_init(lines)
        indent = indentation(lines[init_pos])
        start = init_pos + 1
        end_of_init = find_dedent(lines[start:]) + start
        lines[end_of_init:end_of_init] = [f'{indent}def {self.name}():',
                                          f'{indent}    pass']
        offending_line = line_with(lines, f'self.{issue.name} = None')
        del lines[offending_line]
        new_content = '\n'.join(lines)
        self.file.write(new_content)


class MissingClass:
    def __init__(self, name, file):
        self.name = name
        source_name = get_source_name(file)
        self.file = CurrentFile(path.local(
            file.dirname).join('..').join(f'{source_name}.py'))

    def fix(self):
        variable_stub = f'{issue.name} = None\n'
        if variable_stub not in self.file.content:
            return
        parts = self.file.content.split(variable_stub)
        assert len(parts) == 2
        class_stub = textwrap.dedent(f"""
            class {self.name}:
                def __init__(self):
                    pass
            """)
        new_content = parts[0] + class_stub + parts[1]
        self.file.write(new_content)


def starting_at(marker, text):
    return text[text.find(marker):]


class MissingArgument:
    arg_marker = '() takes '
    keyword_arg_marker = '() got an unexpected keyword argument '

    def __init__(self, name, file, args):
        self.name = name
        source_name = get_source_name(file)
        self.file = CurrentFile(path.local(
            file.dirname).join('..').join(f'{source_name}.py'))
        self.args = args

    def fix(self):
        stub = start_of_function_declaration(self.name)
        if stub not in self.file.content:
            return
        parts = self.file.content.split(stub)
        assert len(parts) == 2
        stub_with_arg = stub + ', '.join(self.args)
        new_content = parts[0] + stub_with_arg + starting_at('):', parts[1])
        self.file.write(new_content)


class MissingSelf:
    marker = '() got multiple values for argument'

    def __init__(self, name, file, args):
        self.name = name
        source_name = get_source_name(file)
        self.file = CurrentFile(path.local(
            file.dirname).join('..').join(f'{source_name}.py'))
        self.args = args

    def fix(self):
        stub = start_of_function_declaration(self.name)
        if stub not in self.file.content:
            return
        parts = self.file.content.split(stub)
        assert len(parts) == 2
        stub_with_arg = stub + ', '.join(self.args)
        new_content = parts[0] + stub_with_arg + starting_at('):', parts[1])
        self.file.write(new_content)


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
    res = []
    index = 0
    for el in args:
        if identifier(el) or keyword_argument(el):
            res.append(el)
        else:
            while f'arg{index}' in args:
                index += 1
            res.append(f'arg{index}')
    return res


def expected_number_of_args(message):
    expected = message.split('but ')[1].split(' ')
    expected = [el for el in expected if el]
    return int(expected[0])


def arg_marker_type(line):
    if MissingArgument.arg_marker in line:
        return MissingArgument.arg_marker
    if MissingArgument.keyword_arg_marker in line:
        return MissingArgument.keyword_arg_marker
    return None


def get_broken_line_number(code, line):
    # import was stripped -> increment line number
    return int(line.split('line ')[-1].split(',')[0]) + 1


def get_broken_line(code, line):
    return code.split('\n')[get_broken_line_number(code, line) - 1]


def problem(a_file):
    test_code = a_file.read()
    folder = a_file.dirname
    folder = path.local(folder).join('..')
    name = a_file.purebasename
    assert name.startswith('test_')
    name = name[len('test_'):]
    source_code = folder.join(name + '.py').read()
    error = check(name, source_code, test_code)
    if error is None:
        return None
    previous_line = ['']
    for line in error.split('\n'):
        marker = "' object has no attribute '"
        if marker in line:
            parts = line.split(marker)
            class_name = parts[0].split("'")[-1]
            attribute_name = parts[1].split("'")[0]
            return MissingAttribute(class_name, attribute_name, a_file)
        marker = "has no attribute '"
        if marker in line:
            parts = line.split(marker)
            return MissingVariable(parts[1].split("'")[0], a_file)
        marker = "NameError: name '"
        if marker in line:
            parts = line.split(marker)
            return MissingImport(parts[1].split("'")[0], a_file)
        marker = "No module named '"
        if marker in line:
            parts = line.split(marker)
            assert len(parts) == 2
            name = parts[1].split("'")[0]
            return InvalidImport(name, a_file)
        if 'object is not callable' in line:
            previous = get_broken_line(test_code, previous_line[0])
            tmp = previous.split('(')[-2]
            name = tmp.split('.')[-1]
            if name[0].isupper():
                return MissingClass(name, a_file)
            return MissingFunction(name, a_file)
        marker = arg_marker_type(line)
        if marker:
            parts = line.split(marker)
            tmp = parts[0]
            name = tmp.split(' ')[-1]
            is_init_call = (name == '__init__')
            before_args = '(' if is_init_call else name + '('
            expected = 0
            if marker == MissingArgument.arg_marker:
                expected += expected_number_of_args(parts[1])
            previous = get_broken_line(test_code, previous_line[0])
            parts = previous.split(before_args)
            assert len(parts) == 2
            arg_string = parts[1].split(')')[0]
            args = [el.strip() for el in arg_string.split(',')]
            args = [el for el in args if el]  # get rid of empty strings
            if expected > len(args):
                # method -> add self argument
                args.insert(0, 'self')
            return MissingArgument(name, a_file, fix_literals(args))
        marker = MissingSelf.marker
        if marker in line:
            parts = line.split(marker)
            tmp = parts[0]
            name = tmp.split(' ')[-1]
            is_init_call = (name == '__init__')
            before_args = '(' if is_init_call else name + '('
            previous = get_broken_line(test_code, previous_line[0])
            parts = previous.split(before_args)
            assert len(parts) == 2
            arg_string = parts[1].split(')')[0]
            args = [el.strip() for el in arg_string.split(',')]
            args = [el for el in args if el]  # get rid of empty strings
            # method -> add self argument
            args.insert(0, 'self')
            return MissingSelf(name, a_file, fix_literals(args))
        previous_line[0] = line
    return JustBroken(a_file)


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


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    source_name = get_source_name(file)
    issues = [problem(file)]
    while issues[0] and (type(issues[0]) != JustBroken):
        issue = issues[0]
        issue.fix()
        new_issue = problem(file)
        if not improved(issues[0], new_issue):
            # this didn't help
            # -> restore the previous content
            issue.file.restore()
            break
        issues[0] = new_issue
