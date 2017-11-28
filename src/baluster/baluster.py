from inspect import isclass

from .manager import Manager, AsyncManager
from .state import State
from .mediator import Mediator
from .makers import BaseMaker
from .utils import (
    capture_exceptions, as_async, get_member_name, find_instance
)


class BaseBaluster:

    def __init__(self, _state=None, _parent=None, **params):
        self._parent = _parent
        if _parent is not None:
            self._root = _parent._root
            self._name = get_member_name(
                self._parent._name,
                self.__class__.__name__
            )
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


class BalusterType(type):

    def __new__(cls, name, bases, defined_members):
        makers = []
        nested = []
        members = dict()

        for base in bases:
            if hasattr(base, '_makers'):
                makers += base._makers
            if hasattr(base, '_nested'):
                nested += base._nested

        for k, v in defined_members.items():
            if isinstance(v, BaseMaker):
                makers.append(v)
            if isclass(v) and issubclass(v, BaseBaluster):
                nested.append((k, v))
            members[k] = v

        members['_makers'] = tuple(makers)
        members['_nested'] = tuple(nested)
        return super().__new__(cls, name, bases, members)


class Baluster(BaseBaluster, metaclass=BalusterType):

    def __new__(cls, *args, **kwargs):

        def mediator_factory(name, instance):
            return Mediator(
                name, instance,
                lambda i: (i._root, i._root._state, i._name)
            )

        for maker in cls._makers:
            maker.bind(mediator_factory)
        return super(Baluster, cls).__new__(cls)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, nested in self._nested:
            setattr(self, name, nested(_parent=self))
        for maker in self._makers:
            maker.init(self)

    def partial_copy(self, *names):
        return self.__class__(self._state.partial_copy(names))

    def inject_config(self, binder):
        self._state.map_inject_providers(binder.bind_to_provider)

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


class AsyncBaluster(Baluster):

    def enter(self):
        return AsyncManager(self.__class__(self._state.new_child()))

    async def aclose(self):
        handlers = self._state.get_close_handlers()
        with capture_exceptions() as capture:
            for key, handler, resource in handlers:
                instance = find_instance(self, key)
                with capture():
                    await as_async(handler, instance, self, resource)
            self._state.clear_close_handlers()
