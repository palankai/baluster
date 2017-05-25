from asyncio import iscoroutinefunction, coroutine
from collections import defaultdict
from functools import partial
from inspect import isclass
import re


class ValueStoreProxy:

    def __init__(self, name, instance, func):
        self._instance = instance
        self._root = instance._root
        self._name = name
        self._key = instance._get_member_name(name)
        self._func = partial(func, self._instance)

    @property
    def func(self):
        return self._func

    @property
    def root(self):
        return self._root

    def get(self):
        return self._root._resources[self._key]

    def save(self, value):
        self._root._resources[self._key] = value

    def has(self):
        return self._key in self._root._resources

    def add_close_handler(self, handler, resource):
        self._root._close_handlers.append((self._key, handler, resource))

    def get_args(self, args):
        params = []
        for name in args:
            if name == 'root':
                params.append(self.root)
            else:
                params.append(self.root._params.get(name))
        return params


class Maker:

    def __init__(
        self, func=None, *, cache=True, readonly=False, inject=None, args=None
    ):
        self._owner = None
        self._name = None
        self._cache = cache
        self._readonly = readonly
        self._inject = inject
        self._close_handler = None
        self._args = args or ['root']
        if func is not None:
            self(func)

    def __call__(self, func):
        self._func = func
        return self

    def __get__(self, instance, owner):
        if instance is None:
            return self
        getter = self._is_async and self._async_get or self._get
        return getter(self._get_proxy(instance))

    def _get(self, proxy):
        if proxy.has():
            return proxy.get()
        value = proxy.func(*proxy.get_args(self._args))
        if self._close_handler:
            proxy.add_close_handler(self._close_handler, value)
        if self._cache:
            proxy.save(value)
        return value

    async def _async_get(self, proxy):
        if proxy.has():
            return proxy.get()
        value = await proxy.func(*proxy.get_args(self._args))
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
    def _is_async(self):
        return iscoroutinefunction(self._func)

    def close(self, handler):
        self._close_handler = handler
        return handler

    def setup(self, instance):
        if self._inject is None:
            return
        proxy = self._get_proxy(instance)
        if self._is_async:
            _getter = coroutine(partial(self._async_get, proxy))
        else:
            _getter = partial(self._get, proxy)
        instance._root._inject[self._inject] = _getter


class BaseHolder:

    def __init__(
        self, _parent=None, _name=None, _resources=None, _inject=None,
        _close_handlers=None, **params
    ):
        self._parent = _parent
        if _parent is not None:
            self._root = _parent._root
            self._name = self._parent._get_member_name(_name)
        else:
            self._root = self
            self._name = None
            self._resources = _resources or dict()
            self._inject = _inject or dict()
            self._close_handlers = _close_handlers or []
            self._params = params

    def _join_name(self, *names):
        return '.'.join(names)

    def _get_member_name(self, name):
        if self._name is None:
            return name
        return self._join_name(self._name, name)

    def _get_instance_by_name(self, name):
        instance = self
        for part in name.split('.')[:-1]:
            instance = getattr(instance, part)
        return instance

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def close(self):
        exceptions = []
        for key, handler, resource in reversed(self._close_handlers):
            instance = self._get_instance_by_name(key)
            try:
                handler(instance, self, resource)
            except Exception as ex:
                exceptions.append(ex)
        if exceptions:
            raise MultipleExceptions(exceptions)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.aclose()

    async def aclose(self):
        exceptions = []
        for key, handler, resource in reversed(self._close_handlers):
            instance = self._get_instance_by_name(key)
            try:
                if iscoroutinefunction(handler):
                    await handler(instance, self, resource)
                else:
                    handler(instance, self, resource)
            except Exception as ex:
                exceptions.append(ex)
        if exceptions:
            raise MultipleExceptions(exceptions)

    def partial_copy(self, *names):
        _inject = self._inject
        _resources = dict()
        _close_handlers = []
        for key, value in self._resources.items():
            for name in names:
                if re.match('^{}$'.format(name), key):
                    _resources[key] = value
        for key, handler, resource in self._close_handlers:
            for name in names:
                if re.match('^{}$'.format(name), key):
                    _close_handlers.append((key, handler, resource))
        return self.__class__(
            _inject=_inject, _resources=_resources,
            _close_handlers=_close_handlers, **self._params
        )

    @staticmethod
    def factory(func=None, **kwargs):
        return Maker(func, **kwargs)

    def inject_config(self, binder):
        def get_lambda(maker):
            return lambda: maker()
        for key, maker in self._inject.items():
            binder.bind_to_provider(key, get_lambda(maker))


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
            maker.setup(self)


class MultipleExceptions(Exception):

    def __init__(self, exceptions):
        self._exceptions = exceptions
        super().__init__('Multiple exceptions occured')

    @property
    def exceptions(self):
        return self._exceptions
