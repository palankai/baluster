from .base import ValueMaker


def placeholder(*args, **kwargs):
    return ValueMaker(*args, **kwargs)
