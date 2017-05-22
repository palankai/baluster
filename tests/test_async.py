import pytest
from baluster import Holder, make


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


class SampleAsync(Holder):

    @make
    def connection(self, root):
        return SampleAsyncConnection()

    @make
    def sync_connection(self, root):
        return SampleSyncConnection()

    @make(alias='conn')
    async def connect(self, root):
        conn = root.connection
        await conn.connect()
        return conn

    @make(cache=False)
    async def fetch_some(self, root):
        conn = root.connection
        result = await conn.fetch_some()
        return result

    @connection.hook('close')
    async def disconnect(self, root):
        conn = root.connection
        await conn.disconnect()

    @make
    async def sync_connect(self, root):
        conn = root.sync_connection
        conn.connect()
        return conn

    @sync_connection.hook('close')
    def sync_disconnect(self, root):
        conn = root.sync_connection
        conn.disconnect()


class TestAsync:

    @pytest.mark.asyncio
    async def test_top_level_access(self):
        obj = SampleAsync()
        conn = obj.connection

        assert conn.state is None

        await conn.connect()
        assert conn.state == 'connected'

        res = await obj.fetch_some
        assert res == 'some'

        await conn.disconnect()
        assert conn.state == 'disconnected'

    @pytest.mark.asyncio
    async def test_coroutine_access(self):
        obj = SampleAsync()

        conn = await obj.connect
        assert conn.state == 'connected'

        conn = await obj.connect
        assert conn.state == 'connected'

    @pytest.mark.asyncio
    async def test_coroutine_access_by_alias(self):
        obj = SampleAsync()

        conn = await obj['conn']
        assert conn.state == 'connected'

        conn = await obj['conn']
        assert conn.state == 'connected'

    @pytest.mark.asyncio
    async def test_as_context_manager(self):
        obj = SampleAsync()
        conn = obj.connection
        assert conn.state is None

        async with conn:
            assert conn.state == 'connected'

        assert conn.state == 'disconnected'

    @pytest.mark.asyncio
    async def test_hooks(self):
        obj = SampleAsync()
        exception_raised = False

        try:
            async with obj:
                conn = obj.connection
                sync_conn = obj.sync_connection
                assert conn.state is None
                assert sync_conn.state is None
                await conn.connect()
                sync_conn.connect()
                assert conn.state == 'connected'
                assert sync_conn.state == 'connected'

                raise ZeroDivisionError()
        except ZeroDivisionError:
            exception_raised = True

        assert conn.state == 'disconnected'
        assert sync_conn.state == 'disconnected'
        assert exception_raised is True
