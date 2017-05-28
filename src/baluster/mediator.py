from .utils import get_member_name


class Mediator:

    __slots__ = ('_instance', '_root', '_state', '_name', '_key')

    def __init__(self, name, instance, extract):
        root, state, parent_name = extract(instance)
        self._name = name
        self._instance = instance
        self._root = root
        self._state = state
        self._key = get_member_name(parent_name, name)

    @property
    def root(self):
        return self._root

    @property
    def instance(self):
        return self._instance

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
        return (
            (self.instance,) +
            tuple(self.root._state.get_args(args, root=self._root))
        )

    def set_inject(self, name, injectable):
        self._state.set_inject(name, injectable)
