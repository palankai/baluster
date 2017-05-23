import pytest

from baluster import Holder


class CompositeRoot(Holder):

    _counter = 0

    @Holder.factory(cache=False, alias='resource')
    def resource(self, root):
        self._counter += 1
        return self._counter

    @Holder.factory(cache=False, alias='resource2')
    def resource2(self, root):
        self._counter += 1
        return self._counter * 3

    @Holder.factory(cache=False, alias='async_resource')
    async def async_resource(self, root):
        self._counter += 1
        return self._counter * 5

    class level1(Holder):

        class level2(Holder):

            @Holder.factory(cache=False, alias='deep_resource')
            def resource(self, root):
                root._counter += 1
                return root._counter * 7


class FakeBinder:

    def __init__(self):
        self.bindings = dict()

    def bind_to_provider(self, key, value):
        self.bindings[key] = value


class TestInjectBind:

    def test_calling_binder(self):
        obj = CompositeRoot()

        fake_binder = FakeBinder()
        obj.inject_config(fake_binder)

        assert 'resource' in fake_binder.bindings
        assert 'resource2' in fake_binder.bindings
        assert 'async_resource' in fake_binder.bindings
        assert 'deep_resource' in fake_binder.bindings

        assert fake_binder.bindings['resource']() == 1
        assert fake_binder.bindings['resource']() == 2
        assert fake_binder.bindings['resource2']() == 9
        assert fake_binder.bindings['resource']() == 4

    def test_calling_binder_for_nested_instance(self):
        obj = CompositeRoot()

        fake_binder = FakeBinder()
        obj.inject_config(fake_binder)

        assert fake_binder.bindings['resource']() == 1
        assert fake_binder.bindings['deep_resource']() == 14

    @pytest.mark.asyncio
    async def test_calling_binder_async(self):
        obj = CompositeRoot()

        fake_binder = FakeBinder()
        obj.inject_config(fake_binder)

        assert fake_binder.bindings['resource']() == 1

        v = await fake_binder.bindings['async_resource']()

        assert v == 10
