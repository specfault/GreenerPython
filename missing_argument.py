#!/usr/bin/env python3
import ast
from utils import get_broken_line
from utils import start_of_function_declaration
from utils import line_with
from utils import find_dedent


def parses(text):
    try:
        ast.parse(text)
        return True
    except:  # noqa: E722
        return False


def function_name(line, marker):
    parts = line.split(marker)
    tmp = parts[0]
    return tmp.split(' ')[-1]


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


def print_keyword_argument(arg):
    # XXX should use arg.value as the default instead of 1
    # XXX but arg.value is an AST node and we have no function to print it
    return f"{arg.arg}=1"


def get_arguments(function_name, broken_line):
    res = ast.parse(extract_relevant_call(function_name, broken_line))
    body = res.body[0]
    args = body.value.args
    keywords = body.value.keywords
    return [el.id if type(el) is ast.Name else "1" for el in args] +\
           [print_keyword_argument(el) for el in keywords]


def is_method(name, source):
    stub = start_of_function_declaration(name)
    lines = source.split('\n')
    pos = line_with(lines, stub)
    pos = pos - find_dedent(lines[pos::-1])
    if pos < 0:
        # cannot be part of a class because we've run out of code
        return False
    return lines[pos].lstrip().startswith('class')


def starting_at(marker, text):
    return text[text.find(marker):]


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


def arg_marker_type(line):
    for m in MissingArgument.markers:
        if m in line:
            return m
    return None


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
