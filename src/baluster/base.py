from asyncio import iscoroutinefunction, coroutine
import re
from collections import defaultdict
from inspect import isclass
from functools import partial


class ValueStoreProxy:

    def __init__(self, name, instance, func):
        self._instance = instance
        self._root = instance._root
        self._name = name
        self._key = instance._get_member_name(name)
        self._func = partial(func, self._instance, self._root)

    @property
    def func(self):
        return self._func

    def get(self):
        return self._root._get(self._key)

    def save(self, value):
        self._root._save(self._key, value)

    def has(self):
        return self._root._has(self._key)


class Maker:

    def __init__(
        self, func=None, *, cache=True, readonly=False, alias=None
    ):
        self._owner = None
        self._name = None
        self._cache = cache
        self._readonly = readonly
        self._alias = alias
        self._hooks = []
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
        value = proxy.func()
        if self._cache:
            proxy.save(value)
        return value

    async def _async_get(self, proxy):
        if proxy.has():
            return proxy.get()
        value = await proxy.func()
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

    def hook(self, name):
        def inner(f):
            self._hooks.append((name, f))
            return f
        return inner

    def setup(self, instance):
        self._setup_alias(instance)
        self._setup_handlers(instance)

    def _setup_alias(self, instance):
        if self._alias is None:
            return
        proxy = self._get_proxy(instance)
        if self._is_async:
            _getter = coroutine(partial(self._async_get, proxy))
        else:
            _getter = partial(self._get, proxy)
        instance._root._set_alias(self._alias, _getter)

    def _setup_handlers(self, instance):
        root = instance._root
        for name, handler in self._hooks:
            _handler = partial(handler, instance, root)
            if iscoroutinefunction(handler):
                _handler = coroutine(_handler)
            root._add_handler(name, _handler)


def make(func=None, **kwargs):
    return Maker(func, **kwargs)


class BaseHolder:

    def __init__(
        self, parent=None, name=None, _vars=None, _alias=None, _handlers=None
    ):
        self._parent = parent
        if parent is not None:
            self._root = parent._root
            self._name = self._parent._get_member_name(name)
        else:
            self._root = self
            self._name = None
            self._vars = _vars or dict()
            self._alias = _alias or dict()
            self._handlers = _handlers or defaultdict(list)

    def _join_name(self, *names):
        return '.'.join(names)

    def _get_member_name(self, name):
        if self._name is None:
            return name
        return self._join_name(self._name, name)

    def __getitem__(self, name):
        maker = self._alias[name]
        return maker()

    def __iter__(self):
        for alias in self._alias:
            yield alias

    def _save(self, name, value):
        self._vars[name] = value

    def _get(self, name):
        return self._vars[name]

    def _has(self, name):
        return name in self._vars

    def _set_alias(self, name, handler):
        self._alias[name] = handler

    def _add_handler(self, name, handler):
        self._handlers[name].append(handler)

    def __call__(self, name, **kwargs):
        for handler in self._handlers[name]:
            handler(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        for handler in self._handlers['close']:
            handler()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        for handler in self._handlers['close']:
            if iscoroutinefunction(handler):
                await handler()
            else:
                handler()

    def copy(self, *names):
        _alias = self._alias
        _handlers = self._handlers
        _vars = dict()
        for key, value in self._vars.items():
            for name in names:
                if re.match('^{}$'.format(name), key):
                    _vars[key] = value
        return self.__class__(
            _alias=_alias, _handlers=_handlers, _vars=_vars
        )


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
            setattr(self, name, nested(parent=self, name=name))
        for maker in self._makers:
            maker.setup(self)
