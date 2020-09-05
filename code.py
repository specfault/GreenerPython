#!/usr/bin/env python3


class Code:
    def __init__(self, name, test, source):
        self.name = name
        self.test = test
        self.source = source

    def with_changed_source(self, source):
        return Code(self.name, self.test, source)

    def with_changed_test(self, test):
        return Code(self.name, test, self.source)
