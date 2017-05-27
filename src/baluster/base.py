from asyncio import iscoroutinefunction
from functools import partial
from inspect import isclass

from .manager import Manager
from .state import State
from .utils import (
    capture_exceptions, as_async, make_caller, get_member_name,
    find_instance, async_partial
)


class ValueStoreProxy:

    __slots__ = ('_root', '_state', '_name', '_key', '_func')

    def __init__(self, name, instance, func):
        self._root = instance._root
        self._state = self._root._state
        self._name = name
        self._key = get_member_name(instance._name, name)
        self._func = partial(func, instance)

    @property
    def func(self):
        return self._func

    @property
    def root(self):
        return self._root

    def get(self):
        return self._state.get_resource(self._key)

    def save(self, value):
        return self._state.set_resource(self._key, value)

    def has(self):
        return self._state.has_resource(self._key)

    def invalidate(self):
        self._state.del_resource(self._key)

    def add_close_handler(self, handler, resource=None):
        return self._state.add_close_handler(self._key, handler, resource)

    def get_args(self, args):
        return tuple(self.root._state.get_args(args, root=self._root))


class Maker:

    __slots__ = (
        '_owner', '_name', '_cache', '_readonly', '_inject', '_close_handler',
        '_invalidate_after_closed', '_args', '_func'
    )

    def __init__(
        self, func=None, *, cache=True, readonly=False, inject=None, args=None
    ):
        self._owner = None
        self._name = None
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
        getter = self.is_async and self._async_get or self._get
        return getter(self._get_proxy(instance))

    def _get(self, proxy):
        if proxy.has():
            return proxy.get()
        value = self._get_func(proxy)
        return self._process_value(proxy, value)

    async def _async_get(self, proxy):
        if proxy.has():
            return proxy.get()
        value = await self._get_func(proxy)
        return self._process_value(proxy, value)

    def _get_func(self, proxy):
        return proxy.func(*proxy.get_args(self._args))

    def _process_value(self, proxy, value):
        if self._invalidate_after_closed:
            proxy.add_close_handler(make_caller(proxy.invalidate))
        if self._close_handler:
            proxy.add_close_handler(self._close_handler, value)
        if self._cache:
            proxy.save(value)
        return value

    def __set__(self, instance, value):
        proxy = self._get_proxy(instance)
        if proxy.has():
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
        proxy.save(value)

    def _get_proxy(self, instance):
        return ValueStoreProxy(self._name, instance, self._func)

    def __delete__(self, instance):
        raise AttributeError('Attribute cannot be deleted')

    def __set_name__(self, owner, name):
        self._name = name
        self._owner = owner

    @property
    def is_async(self):
        return iscoroutinefunction(self._func)

    def close(self, handler=None, *, invalidate=False):
        def inner(f):
            self._invalidate_after_closed = invalidate
            self._close_handler = f
            return f
        if handler is None:
            return inner
        return inner(handler)

    def get_injectable(self, instance):
        proxy = self._get_proxy(instance)
        if self.is_async:
            return async_partial(self._async_get, proxy)
        return partial(self._get, proxy)

    def setup(self, instance, state):
        if self._inject is None:
            return
        state.set_inject(self._inject, self.get_injectable(instance))


class BaseHolder:

    def __init__(self, _state=None, _parent=None, _name=None, **params):
        self._parent = _parent
        if _parent is not None:
            self._root = _parent._root
            self._name = get_member_name(self._parent._name, _name)
        else:
            self._root = self
            self._name = None
            self._state = _state or State(params=params)

    def __getitem__(self, name):
        return self._state.get_data(name)

    def __setitem__(self, name, value):
        self._state.set_data(name, value)

    def __delitem__(self, name):
        self._state.del_data(name)

    def __contains__(self, name):
        return self._state.has_data(name)

    def enter(self):
        return Manager(self.__class__(self._state.new_child()))

    def close(self):
        handlers = self._state.get_close_handlers()
        with capture_exceptions() as capture:
            for key, handler, resource in handlers:
                instance = find_instance(self, key)
                with capture():
                    handler(instance, self, resource)
            self._state.clear_close_handlers()

    async def aclose(self):
        handlers = self._state.get_close_handlers()
        with capture_exceptions() as capture:
            for key, handler, resource in handlers:
                instance = find_instance(self, key)
                with capture():
                    await as_async(handler, instance, self, resource)
            self._state.clear_close_handlers()

    def partial_copy(self, *names):
        return self.__class__(self._state.partial_copy(names))

    @staticmethod
    def factory(func=None, **kwargs):
        def inner(f):
            return Maker(f, **kwargs)
        if func is None:
            return inner
        return inner(func)

    def inject_config(self, binder):
        self._state.map_inject_providers(binder.bind_to_provider)


class HolderType(type):

    def __new__(cls, name, bases, defined_members):
        makers = []
        nested = []
        members = dict()

        for k, v in defined_members.items():
            if isinstance(v, Maker):
                makers.append(v)
            if isclass(v) and issubclass(v, BaseHolder):
                nested.append((k, v))
            members[k] = v

        members['_makers'] = tuple(makers)
        members['_nested'] = tuple(nested)
        return super().__new__(cls, name, bases, members)


class Holder(BaseHolder, metaclass=HolderType):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, nested in self._nested:
            setattr(self, name, nested(_parent=self, _name=name))
        for maker in self._makers:
            maker.setup(self, self._root._state)
