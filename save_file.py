#!/usr/bin/env python3


import sys
import subprocess
from py import path
from collections import namedtuple
import ast
import textwrap


JUST_BROKEN = object()


MissingVariable = namedtuple('MissingVariable', ['name'])
MissingFunction = namedtuple('MissingFunction', ['name'])
MissingClass = namedtuple('MissingClass', ['name'])
MissingArgument = namedtuple('MissingArgument', ['name', 'args'])
InvalidImport = namedtuple('InvalidImport', ['name'])


class CurrentFile:
    def __init__(self, file):
        self.file = file
        self.content = file.read()

    def restore(self):
        self.file.write(self.content)

    def write(self, content):
        self.file.write(content)


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


def get_source_name(test_file):
    filename = '.'.join(test_file.basename.split('.')[:-1])
    assert filename.startswith('test_')
    return filename[len('test_'):]


def identifier(name):
    res = ast.parse(name)
    return type(res.body[0].value) == ast.Name


def fix_literals(args):
    """make up argument names for literals in call"""
    res = []
    index = 0
    for el in args:
        if identifier(el):
            res.append(el)
        else:
            while f'arg{index}' in args:
                index += 1
            res.append(f'arg{index}')
    return res


def problem(a_file):
    folder = a_file.dirname
    folder = path.local(folder).join('..')
    name = f'tests.{a_file.purebasename}'
    p = subprocess.Popen(
        ['python3', '-m', 'unittest', name],
        cwd=str(folder),
        stderr=subprocess.PIPE,
        stdout=subprocess.PIPE)
    (output, error) = p.communicate()
    if p.returncode == 0:
        return None
    previous_line = ['']
    for line in error.decode().split('\n'):
        marker = "has no attribute '"
        if marker in line:
            parts = line.split(marker)
            return MissingVariable(parts[1].split("'")[0])
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
            tmp = previous_line[0].split('(')[-2]
            name = tmp.split('.')[-1]
            if name[0].isupper():
                return MissingClass(name)
            return MissingFunction(name)
        marker = '() takes '
        if marker in line:
            parts = line.split(marker)
            tmp = parts[0]
            name = tmp.split(' ')[-1]

            parts = previous_line[0].split(name + '(')
            assert len(parts) == 2
            arg_string = parts[1].split(')')[0]
            args = [el.strip() for el in arg_string.split(',')]
            return MissingArgument(name, fix_literals(args))
        previous_line[0] = line
    return JUST_BROKEN


def improved(old_issue, new_issue):
    if (not new_issue) or (new_issue is JUST_BROKEN):
        return True
    if (type(old_issue) == MissingImport)\
            and (type(new_issue) == InvalidImport):
        return False
    if type(old_issue) != type(new_issue):
        return True
    return old_issue.name != new_issue.name


def function_declaration(name):
    return f'def {name}():'


def fixable_problem(issue):
    if (not issue) or (issue is JUST_BROKEN):
        return False
    return True


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    source_name = get_source_name(file)
    issues = [problem(file)]
    files = [None]
    while fixable_problem(issues[0]):
        issue = issues[0]
        # most fixes change the SUT so this is a sane default
        source_file = path.local(
            file.dirname).join('..').join(f'{source_name}.py')
        files[0] = CurrentFile(source_file)
        if type(issue) in (MissingImport, InvalidImport):
            files[0] = issue.file
            issue.fix()
        elif type(issue) == MissingVariable:
            source_file.write(f'{issue.name} = None\n\n\n' + files[0].content)
        elif type(issue) == MissingFunction:
            variable_stub = f'{issue.name} = None\n'
            if variable_stub not in files[0].content:
                break
            parts = files[0].content.split(variable_stub)
            assert len(parts) == 2
            function_stub = function_declaration(issue.name) + "\n    pass\n"
            new_content = parts[0] + function_stub + parts[1]
            source_file.write(new_content)
        elif type(issue) == MissingClass:
            variable_stub = f'{issue.name} = None\n'
            if variable_stub not in files[0].content:
                break
            parts = files[0].content.split(variable_stub)
            assert len(parts) == 2
            class_stub = textwrap.dedent(f"""
                class {issue.name}:
                    def __init__(self):
                        pass
                """)
            new_content = parts[0] + class_stub + parts[1]
            source_file.write(new_content)
        elif type(issue) == MissingArgument:
            stub = function_declaration(issue.name)
            if stub not in files[0].content:
                break
            parts = files[0].content.split(stub)
            assert len(parts) == 2
            stub_with_arg = f'def {issue.name}(' + ', '.join(issue.args) + '):'
            new_content = parts[0] + stub_with_arg + parts[1]
            source_file.write(new_content)
        new_issue = problem(file)
        if not improved(issues[0], new_issue):
            # this didn't help
            # -> restore the previous content
            files[0].restore()
            break
        issues[0] = new_issue
