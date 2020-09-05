#!/usr/bin/env python3


def before_marker(parts, start="'"):
    return parts[0].split(start)[-1]


def after_marker(parts):
    return parts[1].split("'")[0]
