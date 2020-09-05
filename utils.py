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


def get_broken_line(code, line):
    line_number = int(line.split('line ')[-1].split(',')[0])
    return code.split('\n')[line_number]


def name_of_called_object(test, message_with_line_number):
    previous = get_broken_line(test, message_with_line_number)
    tmp = previous.split('(')[-2]
    return tmp.split('.')[-1]


def start_of_function_declaration(name):
    return f'def {name}('


def function_declaration(name):
    return start_of_function_declaration(name) + '):'


def numeric_indentation(line):
    return len(indentation(line))


def find_dedent(lines):
    indent = numeric_indentation(lines[0])
    for i in range(len(lines)):
        # ignore empty lines
        if lines[i] and (numeric_indentation(lines[i]) < indent):
            return i
    return len(lines)
