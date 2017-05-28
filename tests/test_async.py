import pytest
from baluster import Baluster, placeholders


class SampleAsyncConnection:

    def __init__(self):
        self._state = None

    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self.disconnect()

    @property
    def state(self):
        return self._state

    async def connect(self):
        assert self._state != 'connected'
        self._state = 'connected'
        return self

    async def disconnect(self):
        self._state = 'disconnected'
        return self

    async def fetch_some(self):
        return 'some'


class SampleSyncConnection:

    def __init__(self):
        self._state = None

    @property
    def state(self):
        return self._state

    def connect(self):
        assert self._state != 'connected'
        self._state = 'connected'
        return self

    def disconnect(self):
        self._state = 'disconnected'
        return self


class SampleAsync(Baluster):

    _closed_resources = None

    @placeholders.factory
    def async_connection(self, root):
        return SampleAsyncConnection()

    @placeholders.factory
    def sync_connection(self, root):
        return SampleSyncConnection()

    @placeholders.factory
    async def async_connect(self, root):
        conn = root.async_connection
        await conn.connect()
        return conn

    @placeholders.factory(cache=False)
    async def async_fetch_some(self, root):
        conn = root.async_connection
        result = await conn.fetch_some()
        return result

    @placeholders.factory
    def sync_connect(self, root):
        conn = root.sync_connection
        conn.connect()
        return conn

    @placeholders.factory
    def resource(self, root):
        return 'sync'

    @resource.close
    def _close_resource(self, root, resource):
        if self._closed_resources is None:
            self._closed_resources = []
        self._closed_resources.append(resource)

    @placeholders.factory(cache=False)
    async def async_resource(self, root):
        return 'async'

    @async_resource.close
    async def _close_async_resource(self, root, resource):
        if self._closed_resources is None:
            self._closed_resources = []
        self._closed_resources.append(resource)


class TestAsync:

    @pytest.mark.asyncio
    async def test_top_level_access(self):
        obj = SampleAsync()
        conn = obj.async_connection

        assert conn.state is None

        await conn.connect()
        assert conn.state == 'connected'

        res = await obj.async_fetch_some
        assert res == 'some'

        await conn.disconnect()
        assert conn.state == 'disconnected'

    @pytest.mark.asyncio
    async def test_coroutine_access(self):
        obj = SampleAsync()

        conn = await obj.async_connect
        assert conn.state == 'connected'

        conn = await obj.async_connect
        assert conn.state == 'connected'

    @pytest.mark.asyncio
    async def test_as_context_manager(self):
        obj = SampleAsync()
        conn = obj.async_connection
        assert conn.state is None

        async with conn:
            assert conn.state == 'connected'

        assert conn.state == 'disconnected'

    @pytest.mark.asyncio
    async def test_closed_without_invoke(self):
        root = SampleAsync()
        exception_raised = False

        try:
            async with root.enter() as obj:
                raise ZeroDivisionError()
        except ZeroDivisionError:
            exception_raised = True

        assert obj._closed_resources is None
        assert exception_raised is True

    @pytest.mark.asyncio
    async def test_closed_with_invoke(self):
        root = SampleAsync()
        exception_raised = False

        try:
            async with root.enter() as obj:
                obj.resource
                await obj.async_resource
                await obj.async_resource
                raise ZeroDivisionError()
        except ZeroDivisionError:
            exception_raised = True

        assert obj._closed_resources == ['async', 'async', 'sync']
        assert exception_raised is True
