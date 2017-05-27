from asyncio import iscoroutinefunction
from contextlib import contextmanager
import re

from .exceptions import MultipleExceptions


def make_if_none(obj, default):
    if obj is not None:
        return obj
    return default


def dict_partial_copy(source, patterns):
    keys = _find_matches(patterns, source.keys())
    return dict(filter(lambda i: i[0] in keys, source.items()))


@contextmanager
def capture_exceptions():
    exceptions = []

    @contextmanager
    def capture():
        try:
            yield
        except Exception as ex:
            exceptions.append(ex)

    try:
        yield capture
    finally:
        if exceptions:
            if len(exceptions) == 1:
                raise exceptions[0]
            raise MultipleExceptions(exceptions)


async def as_async(func, *args, **kwargs):
    if iscoroutinefunction(func):
        return await func(*args, **kwargs)
    return func(*args, **kwargs)


def make_caller(what_to_call):
    return lambda *a, **k: what_to_call()


def join_names(*names):
    return '.'.join(names)


def get_member_name(own_name, name):
    if own_name is None:
        return name
    return join_names(own_name, name)


def find_instance(tree, name):
    instance = tree
    for part in name.split('.')[:-1]:
        instance = getattr(instance, part)
    return instance


def _find_matches(patterns, candidates):
    pts = list(map(_compile_regex, patterns))
    return list(filter(
        lambda c: any(map(lambda p: p.match(c), pts)),
        candidates
    ))


def _compile_regex(name):
    return re.compile('^{}(\..*)?$'.format(name))
