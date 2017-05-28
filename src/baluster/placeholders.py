from .makers import ValueMaker, FactoryMaker, AsyncFactoryMaker
from asyncio import iscoroutinefunction


def value(*args, **kwargs):
    return ValueMaker(*args, **kwargs)


def factory(func=None, **kwargs):
    def inner(f):
        factory_maker = {
            True: AsyncFactoryMaker,
            False: FactoryMaker
        }[iscoroutinefunction(f)]
        return factory_maker(f, **kwargs)
    if func is None:
        return inner
    return inner(func)
