from .makers import ValueMaker, FactoryMaker


def value(*args, **kwargs):
    return ValueMaker(*args, **kwargs)


def factory(func=None, **kwargs):
    def inner(f):
        return FactoryMaker(f, **kwargs)
    if func is None:
        return inner
    return inner(func)
