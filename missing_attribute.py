#!/usr/bin/env python3
from utils import before_marker
from utils import after_marker
from utils import line_with_init
from utils import indentation


class MissingAttribute:
    def __init__(self, class_name, attribute_name):
        self.class_name = class_name
        self.attribute_name = attribute_name

    def fix(self, code):
        lines = code.source.split('\n')
        index = line_with_init(lines, self.class_name)
        pos = index + 1  # insert attribute here
        indent = indentation(lines[pos])
        lines.insert(pos, f'{indent}self.{self.attribute_name} = None')
        return code.with_changed_source('\n'.join(lines))


def match_missing_attribute(line):
    parts = line.split("' object has no attribute '")
    if len(parts) != 2:
        return None
    class_name = before_marker(parts)
    attribute_name = after_marker(parts)
    return MissingAttribute(class_name, attribute_name)
