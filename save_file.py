#!/usr/bin/env python


import sys
import subprocess
from py import path
from collections import namedtuple


MISSING_IMPORT = object()


MissingVariable = namedtuple('MissingVariable', ['name'])


def problem(file):
    try:
        res = subprocess.check_output(['pytest', str(file)])
        return None
    except subprocess.CalledProcessError as e:
        lines = e.output.split('\n')
        for line in lines:
            marker = "'module' object has no attribute '"
            if marker in line:
                parts = line.split(marker)
                return MissingVariable(parts[1].split("'")[0])
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
    if type(issue) == MissingVariable:
        source_file = path.local(file.dirname).join('..').join(filename + '.py')
        content = source_file .read()
        source_file.write(issue.name + ' = None' + '\n\n\n' + content)
        if not passes(file):
            # this didn't fix the problem
            # -> restore the previous content
            source_file.write(content)
