import pytest

from baluster import Holder


class CompositeRoot(Holder):

    class params(Holder):

        @Holder.factory(args=['root', 'env'])
        def debug(self, root, env):
            if env is None:
                return None
            return env.get('DEBUG', False)

    @Holder.factory(cache=False)
    def resource(self, root):
        if root.params.debug:
            return 'debug'
        else:
            return 'production'

    @Holder.factory
    def value(self, root):
        return 'initial value'


class TestManager:

    def test_sanity(self):
        root = CompositeRoot()

        assert root.resource == 'production'
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

            assert ctx.resource == 'production'
            assert ctx.value == 'new value'
