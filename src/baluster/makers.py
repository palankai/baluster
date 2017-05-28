from functools import partial

from .utils import make_caller, async_partial, Undefined


class BaseMaker:

    __slots__ = ('_name', '_mediator_factory')

    def __delete__(self, instance):
        raise AttributeError('Attribute cannot be deleted')

    def __set_name__(self, owner, name):
        self._name = name

    def get_mediator(self, instance):
        return self._mediator_factory(self._name, instance)

    def init(self, instance):
        pass

    def bind(self, mediator_factory):
        self._mediator_factory = mediator_factory


class ValueMaker(BaseMaker):

    __slots__ = ('_default', )

    def __init__(self, default=Undefined):
        self._name = None
        self._default = default

    def __get__(self, instance, owner):
        if instance is None:
            return self
        mediator = self.get_mediator(instance)
        if mediator.has():
            return mediator.get()
        if self._default == Undefined:
            raise AttributeError()
        if callable(self._default):
            value = self._default()
        else:
            value = self._default
        mediator.save(value)
        return value

    def __set__(self, instance, value):
        mediator = self.get_mediator(instance)
        if mediator.has():
            raise AttributeError(
                'The value `{name}` has already been set'.format(
                    name=self._name
                )
            )
        mediator.save(value)


class FactoryMaker(BaseMaker):

    __slots__ = (
        '_cache', '_readonly', '_inject', '_close_handler',
        '_invalidate_after_closed', '_args', '_func'
    )

    def __init__(
        self, func=None, *, cache=True, readonly=False, inject=None, args=None
    ):
        self._cache = cache
        self._readonly = readonly
        self._inject = inject
        self._close_handler = None
        self._invalidate_after_closed = False
        self._args = args or ['root']
        self._func = func

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._get(self.get_mediator(instance))

    def _get(self, mediator):
        if mediator.has():
            return mediator.get()
        value = self._get_func(mediator)
        return self._process_value(mediator, value)

    def _get_func(self, mediator):
        return self._func(*mediator.get_args(self._args))

    def _process_value(self, mediator, value):
        if self._invalidate_after_closed:
            mediator.add_close_handler(make_caller(mediator.invalidate))
        if self._close_handler:
            mediator.add_close_handler(self._close_handler, value)
        if self._cache:
            mediator.save(value)
        return value

    def __set__(self, instance, value):
        mediator = self.get_mediator(instance)
        if mediator.has():
            raise AttributeError(
                'The value `{name}` has already been set'.format(
                    name=self._name
                )
            )
        if self._readonly:
            raise AttributeError(
                'The value `{name}` is readonly'.format(
                    name=self._name
                )
            )
        mediator.save(value)

    def close(self, handler=None, *, invalidate=False):
        def inner(f):
            self._invalidate_after_closed = invalidate
            self._close_handler = f
            return f
        if handler is None:
            return inner
        return inner(handler)

    def get_injectable(self, mediator):
        return partial(self._get, mediator)

    def init(self, instance):
        super().init(instance)
        if self._inject is None:
            return
        mediator = self.get_mediator(instance)
        mediator.set_inject(self._inject, self.get_injectable(mediator))


class AsyncFactoryMaker(FactoryMaker):

    __slots__ = ()

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return self._get(self.get_mediator(instance))

    async def _get(self, mediator):
        if mediator.has():
            return mediator.get()
        value = await self._get_func(mediator)
        return self._process_value(mediator, value)

    def get_injectable(self, mediator):
        return async_partial(self._get, mediator)
