#!/usr/bin/env python


import sys
from py import path


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file = path.local(name)
    content = file.read()
    file.write("import bla\n\n\n" + content)
