#!/usr/bin/env python


import sys
import subprocess
from py import path


def passes(file):
    res = subprocess.call(['pytest', str(file)])
    return res == 0


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    filename = '.'.join(file.basename.split('.')[:-1])
    assert filename.startswith('test_')
    filename = filename[len('test_'):]
    if not passes(file):
        content = file.read()
        file.write('import ' + filename + '\n\n\n' + content)
