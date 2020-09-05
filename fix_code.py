#!/usr/bin/env python3

import run_code
import ast
import textwrap
import missing_import
import invalid_import
import missing_variable
import missing_attribute
from utils import line_with
from utils import line_with_init
from utils import indentation


class JustBroken:
    def __init__(self):
        pass


def numeric_indentation(line):
    return len(indentation(line))


def find_dedent(lines):
    indent = numeric_indentation(lines[0])
    for i in range(len(lines)):
        # ignore empty lines
        if lines[i] and (numeric_indentation(lines[i]) < indent):
            return i
    return len(lines)


class MissingFunction:
    method_marker = 'self.'

    def __init__(self, name):
        self.name = name

    def fix(self, code):
        variable_stub = f'{self.name} = None\n'
        if variable_stub not in code.source:
            return code
        parts = code.source.split(variable_stub)
        assert len(parts) == 2
        if parts[0].endswith(self.method_marker):
            return self.convert_to_method(code)
        function_stub = function_declaration(self.name) + "\n    pass\n"
        new_content = parts[0] + function_stub + parts[1]
        return code.with_changed_source(new_content)

    def convert_to_method(self, code):
        lines = code.source.split('\n')
        init_pos = line_with_init(lines)
        indent = indentation(lines[init_pos])
        start = init_pos + 1
        end_of_init = find_dedent(lines[start:]) + start
        lines[end_of_init:end_of_init] = [f'{indent}def {self.name}():',
                                          f'{indent}    pass']
        offending_line = line_with(lines, f'self.{self.name} = None')
        del lines[offending_line]
        new_content = '\n'.join(lines)
        return code.with_changed_source(new_content)


class MissingClass:
    def __init__(self, name):
        self.name = name

    def fix(self, code):
        variable_stub = f'{self.name} = None\n'
        if variable_stub not in code.source:
            return code
        parts = code.source.split(variable_stub)
        assert len(parts) == 2
        class_stub = textwrap.dedent(f"""
            class {self.name}:
                def __init__(self):
                    pass
            """)
        new_content = parts[0] + class_stub + parts[1]
        return code.with_changed_source(new_content)


def starting_at(marker, text):
    return text[text.find(marker):]


def is_method(name, source):
    stub = start_of_function_declaration(name)
    lines = source.split('\n')
    pos = line_with(lines, stub)
    pos = pos - find_dedent(lines[pos::-1])
    if pos < 0:
        # cannot be part of a class because we've run out of code
        return False
    return lines[pos].lstrip().startswith('class')


class MissingArgument:
    markers = ('() takes ',
               '() got an unexpected keyword argument ',
               '() got multiple values for argument')

    def __init__(self, name, args):
        self.name = name
        self.args = args

    def fix(self, code):
        if is_method(self.name, code.source):
            # method -> add self argument
            self.args.insert(0, 'self')
        stub = start_of_function_declaration(self.name)
        if stub not in code.source:
            return code
        parts = code.source.split(stub)
        assert len(parts) == 2
        stub_with_arg = stub + ', '.join(self.args)
        new_content = parts[0] + stub_with_arg + starting_at('):', parts[1])
        return code.with_changed_source(new_content)


def identifier(name):
    res = ast.parse(name)
    return type(res.body[0].value) == ast.Name


def keyword_argument(name):
    return '=' in name


def fix_literals(args):
    """make up argument names for literals in call"""
    res = args[:]
    index = 0
    for i, el in enumerate(res):
        if not (identifier(el) or keyword_argument(el)):
            while f'arg{index}' in res:
                index += 1
            res[i] = f'arg{index}'
    return res


def arg_marker_type(line):
    for m in MissingArgument.markers:
        if m in line:
            return m
    return None


def get_broken_line(code, line):
    line_number = int(line.split('line ')[-1].split(',')[0])
    return code.split('\n')[line_number]


def function_name(line, marker):
    parts = line.split(marker)
    tmp = parts[0]
    return tmp.split(' ')[-1]


def print_keyword_argument(arg):
    # XXX should use arg.value as the default instead of 1
    # XXX but arg.value is an AST node and we have no function to print it
    return f"{arg.arg}=1"


def parses(text):
    try:
        ast.parse(text)
        return True
    except:  # noqa: E722
        return False


def extract_relevant_call(function_name, broken_line):
    # required to unpack stuff like this:
    # self.assertEqual(fun(args), x)
    parts = broken_line.split(function_name)
    # assert len(parts) == 2
    if len(parts) != 2:
        # we're probably dealing with a constructor call
        # in this case, the call contains the name of the class
        # the error message, however, complains about __init__
        # let's just strip the leading whitespace and hope that's enough...
        return broken_line.lstrip()
    res = parts[1]
    # now res should be something like
    # (args), x)
    assert res[0] == '('
    # prepend function name to turn it back into a function call
    # we could also parse it as a list but that might spell trouble
    # consider corner cases like (1) which evaluates to 1, not to (1,)
    res = function_name + res
    # we still have to get rid of the trailing
    # , x)
    # which may be arbitrarily complex
    # to get rid of it, we simlpy check substrings of increasing length
    # - until we find one that parses
    # we start with "fun(", which should fail to parse
    n = len(function_name) + 1
    while not parses(res[:n]):
        n += 1
    return res[:n]


def get_arguments(function_name, broken_line):
    res = ast.parse(extract_relevant_call(function_name, broken_line))
    body = res.body[0]
    args = body.value.args
    keywords = body.value.keywords
    return [el.id if type(el) is ast.Name else "1" for el in args] +\
           [print_keyword_argument(el) for el in keywords]


def is_class_name(name):
    return name[0].isupper()


def name_of_called_object(test, message_with_line_number):
    previous = get_broken_line(test, message_with_line_number)
    tmp = previous.split('(')[-2]
    return tmp.split('.')[-1]


class MissingFunctionMatcher:
    def __init__(self, test):
        self.previous_line = ""
        self.test = test

    def __call__(self, line):
        if 'object is not callable' in line:
            name = name_of_called_object(self.test, self.previous_line)
            if is_class_name(name):
                return MissingClass(name)
            return MissingFunction(name)
        self.previous_line = line
        return None


class MissingArgumentMatcher:
    def __init__(self, test):
        self.previous_line = ""
        self.test = test

    def __call__(self, line):
        marker = arg_marker_type(line)
        if marker:
            name = function_name(line, marker)
            broken_line = get_broken_line(self.test, self.previous_line)
            args = get_arguments(name, broken_line)
            return MissingArgument(name, fix_literals(args))
        self.previous_line = line
        return None


def problem(code):
    error = run_code.check(code.name, code.source, code.test)
    if not error:
        return None
    # the first function that matches the error message
    # determines the result
    match_functions = [missing_attribute.match_missing_attribute,
                       missing_variable.match_missing_variable,
                       missing_import.match_missing_import,
                       invalid_import.match_invalid_import,
                       MissingFunctionMatcher(code.test),
                       MissingArgumentMatcher(code.test)]
    for line in error.split('\n'):
        for fun in match_functions:
            match = fun(line)
            if match:
                return match
    return JustBroken()


def improved(old_issue, new_issue):
    if (not new_issue):
        return True
    if (type(old_issue) == missing_import.MissingImport)\
            and (type(new_issue) == invalid_import.InvalidImport):
        return False
    if type(old_issue) != type(new_issue):
        return True
    return old_issue.name != new_issue.name


def start_of_function_declaration(name):
    return f'def {name}('


def function_declaration(name):
    return start_of_function_declaration(name) + '):'


def fixed_code(broken_code):
    code = broken_code
    issues = problem(code)
    while issues and (type(issues) != JustBroken):
        issue = issues
        new_code = issue.fix(code)
        new_issue = problem(new_code)
        if not improved(issues, new_issue):
            break
        code = new_code
        issues = new_issue
    return code
