#!/usr/bin/env python3
from utils import after_marker


class MissingVariable:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        return code.with_changed_source(f'{self.name} = None\n\n\n'
                                        + code.source)


def match_missing_variable(line):
    parts = line.split("has no attribute '")
    if len(parts) != 2:
        return None
    name = after_marker(parts)
    return MissingVariable(name)
