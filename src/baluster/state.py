from collections import ChainMap
import re

from .utils import make_if_none


class State:

    def __init__(
        self, resources=None, close_handlers=None, inject=None, params=None,
        data=None
    ):
        self._resources = make_if_none(resources, dict())
        self._close_handlers = make_if_none(close_handlers, [])
        self._inject = make_if_none(inject, dict())
        self._params = make_if_none(params, dict())
        self._data = make_if_none(data, ChainMap(dict()))

    def get_resource(self, key):
        return self._resources[key]

    def set_resource(self, key, value):
        self._resources[key] = value

    def has_resource(self, key):
        return key in self._resources

    def del_resource(self, key):
        del self._resources[key]

    def get_data(self, name):
        return self._data.get(name)

    def set_data(self, name, value):
        self._data[name] = value

    @property
    def close_handlers(self):
        return self._close_handlers

    def add_close_handler(self, key, handler, resource):
        self._close_handlers.append((key, handler, resource))

    def clear_close_handlers(self):
        self._close_handlers = []

    @property
    def inject(self):
        return self._inject

    @property
    def params(self):
        return self._params

    def new_child(
        self, resources=None
    ):
        if resources is None:
            resources = dict(self._resources)
        return self.__class__(
            resources=resources,
            close_handlers=[],
            inject=self._inject,
            params=self._params,
            data=self._data.new_child()
        )

    def partial_copy(self, include):
        resources = dict()
        for key, value in self._resources.items():
            for name in include:
                if re.match('^{}$'.format(name), key):
                    resources[key] = value
        return self.new_child(resources)
