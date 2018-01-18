#!/usr/bin/env python


import sys
import subprocess
from py import path
from collections import namedtuple


MISSING_IMPORT = object()
JUST_BROKEN = object()


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
            if "NameError: global name '" in line:
                return MISSING_IMPORT
        return JUST_BROKEN


def passes(file):
    return problem(file) is None


def improved(old_issue, new_issue):
    if old_issue is new_issue:
        return False
    return True


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    filename = '.'.join(file.basename.split('.')[:-1])
    assert filename.startswith('test_')
    filename = filename[len('test_'):]
    while True:
        issue = problem(file)
        if not issue:
            break
        if issue is JUST_BROKEN:
            break
        if issue is MISSING_IMPORT:
            content = file.read()
            file.write('import ' + filename + '\n\n\n' + content)
            new_issue = problem(file)
            if not improved(issue, new_issue):
                # this didn't help
                # -> restore the previous content
                file.write(content)
                break
        if type(issue) == MissingVariable:
            source_file = path.local(file.dirname).join('..').join(filename + '.py')
            content = source_file .read()
            source_file.write(issue.name + ' = None' + '\n\n\n' + content)
