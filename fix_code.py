#!/usr/bin/env python3

import run_code
import missing_import
import invalid_import
import missing_variable
import missing_attribute
import missing_function
import missing_argument


class JustBroken:
    def __init__(self):
        pass


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
                       missing_function.MissingFunctionMatcher(code.test),
                       missing_argument.MissingArgumentMatcher(code.test)]
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
