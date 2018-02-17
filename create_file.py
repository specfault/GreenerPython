#!/usr/bin/env python3


import sys
from py import path


def add_if_missing(file):
    """add empty file but don't overwrite existing files"""
    if not file.check():
        file.write('', ensure=True)


def join_directories(base, directories):
    """join base directory of type py.path
    with a list of sub directories (strings)"""
    res = base
    for dir in directories:
        res = res.join(dir)
    return res


def test_directory(source_file):
    """find the test directory for a given source file"""
    dir = path.local(source_file.dirname)
    root = path.local('/')
    subdirectories = []
    while not dir.samefile(root):
        test_dir = dir.join('tests')
        if test_dir.check():
            return join_directories(test_dir, subdirectories)
        subdirectories = [dir.basename] + subdirectories
        dir = dir.join('..')
    # no tests directory found -> just put the test next to the source file
    return path.local(source_file.dirname)


def test_file_name(source_file):
    return test_directory(source_file).join('test_' + source_file.basename)


class FilePair(object):
    """a pair of source and test file
    the test file can be guessed based on the source file
    the reverse is currently not done because one source file
    might have several test files"""
    def __init__(self, file):
        basename = file.basename
        if basename.startswith('test_'):
            # corresponding source file is ambiguous
            self.test_file = file
            self.source_file = None
        elif basename.startswith('__'):
            # magic file
            self.test_file = None
            self.source_file = file
        else:
            self.source_file = file
            self.test_file = test_file_name(self.source_file)

    def create(self):
        if self.source_file is not None:
            add_if_missing(self.source_file)
        if self.test_file is not None:
            add_if_missing(self.test_file)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file_pair = FilePair(path.local(name))
    file_pair.create()
    if file_pair.test_file:
        print(file_pair.test_file)
    else:
        print(file_pair.source_file)
