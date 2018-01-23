#!/usr/bin/env python


import sys
import textwrap
import subprocess
from py import path
from collections import namedtuple
import tokenize
import re


JUST_BROKEN = object()


MissingVariable = namedtuple('MissingVariable', ['name'])
MissingFunction = namedtuple('MissingFunction', ['name'])
MissingArgument = namedtuple('MissingArgument', ['name', 'args'])
MissingImport = namedtuple('MissingImport', ['name'])
InvalidImport = namedtuple('InvalidImport', ['name'])


def get_source_name(test_file):
    filename = '.'.join(test_file.basename.split('.')[:-1])
    assert filename.startswith('test_')
    return filename[len('test_'):]


def literal(name):
    return not re.match(tokenize.Name, name)


def fix_literals(args):
    """make up argument names for literals in call"""
    res = []
    index = 0
    for el in args:
        if not literal(el):
            res.append(el)
        else:
            while "arg" + str(index) in args:
                index += 1
            name = "arg" + str(index)
            res.append(name)
    return res


def problem(file):
    try:
        res = subprocess.check_output(['pytest', str(file)])
        return None
    except subprocess.CalledProcessError as e:
        lines = e.output.split('\n')
        previous_line = ['']
        for line in lines:
            marker = "'module' object has no attribute '"
            if marker in line:
                parts = line.split(marker)
                return MissingVariable(parts[1].split("'")[0])
            marker = "NameError: global name '"
            if marker in line:
                parts = line.split(marker)
                return MissingImport(parts[1].split("'")[0])
            marker = "ImportError: No module named "
            if marker in line:
                parts = line.split(marker)
                assert len(parts) == 2
                return InvalidImport(parts[1])
            if 'object is not callable' in line:
                tmp = previous_line[0].split('(')[-2]
                name = tmp.split('.')[-1]
                return MissingFunction(name)
            if 'takes no arguments' in line:
                parts = line.split('(')
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
    if (type(old_issue) == MissingImport) and (type(new_issue) == InvalidImport):
        return False
    if type(old_issue) != type(new_issue):
        return True
    return old_issue.name != new_issue.name


def function_declaration(name):
    return 'def ' + name + '():'


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    source_name = get_source_name(file)
    while True:
        issue = problem(file)
        if not issue:
            break
        if issue is JUST_BROKEN:
            break
        if type(issue) == MissingImport:
            content = file.read()
            file.write('import ' + issue.name + '\n\n\n' + content)
            new_issue = problem(file)
            if not improved(issue, new_issue):
                # this didn't help
                # -> restore the previous content
                file.write(content)
                break
        if type(issue) == InvalidImport:
            content = file.read()
            marker = 'import ' + issue.name + '\n'
            parts = content.split(marker)
            if len(parts) < 2:
                break
            file.write(''.join(parts))
            new_issue = problem(file)
        if type(issue) == MissingVariable:
            source_file = path.local(file.dirname).join('..').join(source_name + '.py')
            content = source_file .read()
            source_file.write(issue.name + ' = None' + '\n\n\n' + content)
            new_issue = problem(file)
            if not improved(issue, new_issue):
                # this didn't help
                # -> restore the previous content
                source_file.write(content)
                break
        if type(issue) == MissingFunction:
            source_file = path.local(file.dirname).join('..').join(source_name + '.py')
            content = source_file .read()
            variable_stub = issue.name + ' = None\n'
            if variable_stub not in content:
                break
            parts = content.split(variable_stub)
            assert len(parts) == 2
            function_stub = function_declaration(issue.name) + "\n    pass\n"
            new_content = parts[0] + function_stub + parts[1]
            source_file.write(new_content)
            new_issue = problem(file)
            if not improved(issue, new_issue):
                # this didn't help
                # -> restore the previous content
                source_file.write(content)
                break
        if type(issue) == MissingArgument:
            source_file = path.local(file.dirname).join('..').join(source_name + '.py')
            content = source_file .read()
            stub = function_declaration(issue.name)
            if stub not in content:
                break
            parts = content.split(stub)
            assert len(parts) == 2
            stub_with_arg = 'def ' + issue.name + '(' + ', '.join(issue.args) + '):'
            new_content = parts[0] + stub_with_arg  + parts[1]
            source_file.write(new_content)
            new_issue = problem(file)
            if not improved(issue, new_issue):
                # this didn't help
                # -> restore the previous content
                source_file.write(content)
                break
