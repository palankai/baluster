import pytest

from baluster import Holder


class Resource:

    def __init__(self):
        self.connected = None

    def connect(self):
        self.connected = True

    def disconnect(self):
        self.connected = False


class CompositeRoot(Holder):

    class params(Holder):

        @Holder.factory(args=['root', 'env'])
        def debug(self, root, env):
            if env is None:
                return None
            return env.get('DEBUG', False)

    @Holder.factory(cache=False)
    def param_access(self, root):
        if root.params.debug:
            return 'debug'
        else:
            return 'production'

    @Holder.factory
    def resource(self, root):
        res = Resource()
        return res

    @resource.close
    def close_resource(self, root, resource):
        resource.disconnect()

    @Holder.factory
    def value(self, root):
        return 'initial value'


class TestManager:

    def test_sanity(self):
        root = CompositeRoot()

        assert root.param_access == 'production'
        assert root.value == 'initial value'

    def test_delete_on_proxy(self):
        root = CompositeRoot()

        with root.enter() as ctx:
            with pytest.raises(AttributeError):
                del ctx.value

            with pytest.raises(AttributeError):
                del ctx._manager

    def test_entering_context(self):

        root = CompositeRoot()

        with root.enter() as ctx:
            ctx.value = 'new value'

            assert ctx.param_access == 'production'
            assert ctx.value == 'new value'

    def test_non_closing_resource(self):

        root = CompositeRoot()

        root.resource.connect()
        assert root.resource.connected is True

        with root.enter() as ctx:
            assert root.resource.connected is True
            assert ctx.resource.connected is True

        assert root.resource.connected is True

    def test_closing_resource(self):

        root = CompositeRoot()

        with root.enter() as ctx:
            ctx.resource.connect()
            assert ctx.resource.connected is True
            assert root.resource.connected is None

        assert ctx.resource.connected is False
