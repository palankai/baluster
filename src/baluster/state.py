from collections import ChainMap

from .utils import make_if_none, dict_partial_copy, make_caller, merge_dicts


class InjectState:

    def __init__(self, *, inject=None, **kwargs):
        self._inject = make_if_none(inject, dict())

    def set_inject(self, name, provider):
        self._inject[name] = make_caller(provider)

    def map_inject_providers(self, function):
        for args in self._inject.items():
            function(*args)

    def new_child_data(self, **kwargs):
        return dict(inject=self._inject)


class DataState:

    def __init__(self, *, data=None, **kwargs):
        self._data = make_if_none(data, ChainMap(dict()))

    def get_data(self, name):
        return self._data[name]

    def set_data(self, name, value):
        self._data[name] = value

    def del_data(self, name):
        del self._data[name]

    def has_data(self, name):
        return name in self._data

    def new_child_data(self, **kwargs):
        return dict(data=self._data.new_child())


class ResourceState:

    def __init__(self, *, resources=None, **kwargs):
        self._resources = make_if_none(resources, dict())

    def get_resource(self, key):
        return self._resources[key]

    def set_resource(self, key, value):
        self._resources[key] = value

    def has_resource(self, key):
        return key in self._resources

    def del_resource(self, key):
        del self._resources[key]

    def new_child_data(self, *, resources=None, **kwargs):
        if resources is None:
            resources = dict(self._resources)
        return dict(resources=resources)

    def filter_resources(self, patterns):
        return dict_partial_copy(self._resources, patterns)


class CloseHandlersState:

    def __init__(self, *, close_handlers=None, **kwargs):
        self._close_handlers = make_if_none(close_handlers, [])

    def add_close_handler(self, key, handler, resource):
        self._close_handlers.append((key, handler, resource))

    def get_close_handlers(self):
        return reversed(self._close_handlers)

    def clear_close_handlers(self):
        self._close_handlers = []

    def new_child_data(self, **kwargs):
        return dict(close_handlers=[])


class ParamsState:

    def __init__(self, *, params=None, **kwargs):
        self._params = make_if_none(params, dict())

    def get_args(self, names, **extra):
        return [self._params.get(n) or extra.get(n) for n in names]

    def new_child_data(self, **kwargs):
        return dict(params=self._params)


mixtures = (
    InjectState, DataState, ResourceState, CloseHandlersState, ParamsState
)


class State(*mixtures):

    def __init__(self, **kwargs):
        for mixture in mixtures:
            mixture.__init__(self, **kwargs)

    def new_child(self, **kwargs):
        return self.__class__(**merge_dicts(
            m.new_child_data(self, **kwargs) for m in mixtures
        ))

    def partial_copy(self, patterns):
        return self.new_child(resources=self.filter_resources(patterns))
