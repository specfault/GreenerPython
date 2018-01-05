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
    if not passes(file):
        content = file.read()
        file.write("import bla\n\n\n" + content)
