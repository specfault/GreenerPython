#!/usr/bin/env python


import sys
from py import path


def add_if_missing(file):
    """add empty file but don't overwrite existing files"""
    if not file.check():
        file.write('')


class FilePair(object):
    """a pair of source and test file
    the test file can be guessed based on the source file
    the reverse is currently not done because one source file might have several test files"""
    def __init__(self, file):
        basename = file.basename
        dirname = file.dirname
        if basename.startswith('test_'):
            # corresponding source file is ambiguous
            self.test_file = file
            self.source_file = None
        else:
            self.source_file = file
            self.test_file = path.local(dirname).join('test_' + basename)
    def create(self):
        if self.source_file != None:
            add_if_missing(self.source_file)
        if self.test_file != None:
            add_if_missing(self.test_file)


if __name__ == '__main__':
    assert len(sys.argv) == 2
    name = sys.argv[1]
    file_pair = FilePair(path.local(name))
    file_pair.create()
    print(file_pair.test_file)
