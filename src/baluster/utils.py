import re


def make_if_none(obj, default):
    if obj is not None:
        return obj
    return default


def dict_partial_copy(source, patterns):
    keys = _find_matches(patterns, source.keys())
    return dict(filter(lambda i: i[0] in keys, source.items()))


def _find_matches(patterns, candidates):
    pts = list(map(_compile_regex, patterns))
    return list(filter(
        lambda c: any(map(lambda p: p.match(c), pts)),
        candidates
    ))


def _compile_regex(name):
    return re.compile('^{}(\..*)?$'.format(name))
