import pytest

from baluster import Holder, MultipleExceptions


class CompositeRoot(Holder):

    resource_closed = False
    async_resource_closed = False

    @Holder.factory
    def buggy_resource(self, root):
        return True

    @buggy_resource.close
    def close_buggy_resource(self, root, resource):
        raise NotImplementedError()

    @Holder.factory
    def other_buggy_resource(self, root):
        return True

    @other_buggy_resource.close
    def close_other_buggy_resource(self, root, resource):
        raise NotImplementedError()

    @Holder.factory
    def resource(self, root):
        return True

    @resource.close
    def close_resource(self, root, resource):
        self.resource_closed = True

    @Holder.factory
    async def buggy_async_resource(self, root):
        return True

    @buggy_async_resource.close
    async def close_buggy_async_resource(self, root, resource):
        raise NotImplementedError()

    @Holder.factory
    async def async_resource(self, root):
        return True

    @async_resource.close
    async def close_async_resource(self, root, resource):
        self.async_resource_closed = True


class TestClosingResource:

    def test_closing_sync_resource_raises_single_exception(self):
        root = CompositeRoot()

        with pytest.raises(NotImplementedError):
            with root.enter() as obj:
                obj.buggy_resource
                obj.resource
        assert obj.resource_closed is True

    def test_closing_sync_resource_raises_multiple_exceptions(self):
        root = CompositeRoot()

        with pytest.raises(MultipleExceptions) as excinfo:
            with root.enter() as obj:
                obj.other_buggy_resource
                obj.resource
                obj.buggy_resource

        exceptions = excinfo.value.exceptions
        assert len(exceptions) == 2
        assert isinstance(exceptions[0], NotImplementedError)
        assert isinstance(exceptions[1], NotImplementedError)
        assert obj.resource_closed is True

    @pytest.mark.asyncio
    async def test_closing_async_resource_single_exception(self):
        root = CompositeRoot()

        with pytest.raises(NotImplementedError):
            async with root.enter() as obj:
                obj.resource
                await obj.async_resource
                await obj.buggy_async_resource

        assert obj.resource_closed is True
        assert obj.async_resource_closed is True

    @pytest.mark.asyncio
    async def test_closing_async_resource(self):
        root = CompositeRoot()

        with pytest.raises(MultipleExceptions) as excinfo:
            async with root.enter() as obj:
                obj.resource
                obj.buggy_resource
                await obj.async_resource
                await obj.buggy_async_resource

        exceptions = excinfo.value.exceptions

        assert len(exceptions) == 2
        assert isinstance(exceptions[0], NotImplementedError)
        assert isinstance(exceptions[1], NotImplementedError)
        assert obj.resource_closed is True
        assert obj.async_resource_closed is True
