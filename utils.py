#!/usr/bin/env python3


def before_marker(parts, start="'"):
    return parts[0].split(start)[-1]


def after_marker(parts):
    return parts[1].split("'")[0]


def line_with(lines, text):
    for i in range(len(lines)):
        if text in lines[i]:
            return i
    return len(lines)


def line_with_class_definition(lines, class_name):
    return line_with(lines, f'class {class_name}')


def line_with_init(lines, class_name=''):
    index = line_with_class_definition(lines, class_name)
    delta = line_with(lines[index:], '__init__')
    return index + delta


def indentation(line):
    return line[:len(line) - len(line.lstrip())]
