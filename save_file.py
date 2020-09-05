#!/usr/bin/env python3

import sys
from py import path
from code import Code
from fix_code import fixed_code


def get_source_name(test_file):
    filename = test_file.purebasename
    assert filename.startswith('test_')
    return filename[len('test_'):]


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
