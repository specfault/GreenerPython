#!/usr/bin/env python3
from utils import after_marker


class InvalidImport:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        marker = f'import {self.name}\n'
        parts = code.test.split(marker)
        # otherwise it's some weird import and we're not sure how to fix it
        if len(parts) >= 2:
            return code.with_changed_test(''.join(parts))
        return code


def match_invalid_import(line):
    parts = line.split("No module named '")
    if len(parts) != 2:
        return None
    name = after_marker(parts)
    return InvalidImport(name)
