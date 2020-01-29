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


def source_directory(test_file):
    """find the source directory for a given test file"""
    dir = path.local(test_file.dirname)
    root = path.local('/')
    subdirectories = []
    while not dir.samefile(root):
        test_dir = dir.join('tests')
        if test_dir.check():
            # the last subdirectory is tests itself, so skip it
            return join_directories(dir, subdirectories[1:])
        subdirectories = [dir.basename] + subdirectories
        dir = dir.join('..')
    # no tests directory found -> just put the test next to the source file
    return path.local(test_file.dirname)


def source_file_name(file):
    basename = file.basename
    prefix = 'test_'
    assert basename.startswith(prefix)
    return source_directory(file).join(file.basename[len(prefix):])


class FilePair(object):
    """a pair of source and test file
    the test file can be guessed based on the source file
    the reverse is currently not done because one source file
    might have several test files"""
    def __init__(self, file):
        self.test_file = file
        self.source_file = source_file_name(file)

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
    print(file_pair.test_file)
