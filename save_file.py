#!/usr/bin/env python


import sys
import subprocess
from py import path


MISSING_IMPORT = object()
MISSING_VARIABLE_X = object()
MISSING_VARIABLE_Y = object()


def problem(file):
    try:
        res = subprocess.check_output(['pytest', str(file)])
        return None
    except subprocess.CalledProcessError as e:
        if "'module' object has no attribute 'x'" in e.output:
            return MISSING_VARIABLE_X
        if "'module' object has no attribute 'y'" in e.output:
            return MISSING_VARIABLE_Y
        return MISSING_IMPORT


def passes(file):
    return problem(file) is None


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    filename = '.'.join(file.basename.split('.')[:-1])
    assert filename.startswith('test_')
    filename = filename[len('test_'):]
    issue = problem(file)
    if issue is MISSING_IMPORT:
        content = file.read()
        file.write('import ' + filename + '\n\n\n' + content)
        if not passes(file):
            # this didn't fix the problem
            # -> restore the previous content
            file.write(content)
    if issue is MISSING_VARIABLE_X:
        source_file = path.local(file.dirname).join('..').join(filename + '.py')
        content = source_file .read()
        source_file.write('x = None' + '\n\n\n' + content)
        if not passes(file):
            # this didn't fix the problem
            # -> restore the previous content
            source_file.write(content)
    if issue is MISSING_VARIABLE_Y:
        source_file = path.local(file.dirname).join('..').join(filename + '.py')
        content = source_file .read()
        source_file.write('y = None' + '\n\n\n' + content)
        if not passes(file):
            # this didn't fix the problem
            # -> restore the previous content
            source_file.write(content)
