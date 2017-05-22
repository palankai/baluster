import asyncio
import re
from collections import defaultdict
from contextlib import contextmanager
from inspect import isclass
from functools import partial


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
        if asyncio.iscoroutinefunction(self._func):
            return self._async_get(instance)
        return self._get(instance)

    def __set__(self, instance, value):
        root = instance._root
        name = instance._get_member_name(self._name)
        if root._has(name):
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
        root._set(name, value)

    def __delete__(self, instance):
        raise AttributeError('Attribute cannot be deleted')

    def __set_name__(self, owner, name):
        self._name = name
        self._owner = owner

    def _get(self, instance):
        root = instance._root
        name = instance._get_member_name(self._name)
        if root._has(name):
            return root._get(name)
        value = self._func(instance, root)
        if self._cache:
            root._set(name, value)
        return value

    async def _async_get(self, instance):
        root = instance._root
        name = instance._get_member_name(self._name)
        if root._has(name):
            return root._get(name)
        value = await self._func(instance, root)
        if self._cache:
            root._set(name, value)
        return value

    def hook(self, name):
        def inner(f):
            self._hooks.append((name, f))
            return f
        return inner

    def setup(self, instance):
        root = instance._root
        if self._alias is not None:
            if asyncio.iscoroutinefunction(self._func):
                root._set_alias(
                    self._alias,
                    asyncio.coroutine(partial(self._async_get, instance))
                )
            else:
                root._set_alias(self._alias, partial(self._get, instance))
        for name, handler in self._hooks:
            if asyncio.iscoroutinefunction(handler):
                async def f(**kwargs):
                    return await handler(instance, root, **kwargs)
                root._add_handler(name, f)
            else:
                root._add_handler(name, partial(handler, instance, root))


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

    def _set(self, name, value):
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

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        for handler in self._handlers['close']:
            if asyncio.iscoroutinefunction(handler):
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


@contextmanager
def enter(holder, finish='close', **kwargs):
    try:
        yield holder
    finally:
        holder(finish, **kwargs)
