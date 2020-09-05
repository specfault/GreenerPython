#!/usr/bin/env python3
from utils import before_marker


class MissingImport:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        return code.with_changed_test(f'import {self.name}\n\n\n' + code.test)


def match_missing_import(line):
    # do not require the prefix NameError
    # you only get that when the unittest could be started!
    parts = line.split("' is not defined")
    if len(parts) != 2:
        return None
    name = before_marker(parts, start="name '")
    return MissingImport(name)
