import pytest
from ns.base import NS, make


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


class SampleAsyncNS(NS):

    @make
    def connection(self, root):
        return SampleAsyncConnection()

    @make(alias='conn')
    async def connect(self, root):
        conn = root.connection
        await conn.connect()
        return conn

    @connection.hook('close')
    async def disconnect(self, root):
        conn = root.connection
        await conn.disconnect()


class TestAsyncNS:

    @pytest.mark.asyncio
    async def test_top_level_access(self):
        obj = SampleAsyncNS()
        conn = obj.connection

        assert conn.state is None

        await conn.connect()
        assert conn.state == 'connected'

        await conn.disconnect()
        assert conn.state == 'disconnected'

    @pytest.mark.asyncio
    async def test_coroutine_access(self):
        obj = SampleAsyncNS()

        conn = await obj.connect
        assert conn.state == 'connected'

        conn = await obj.connect
        assert conn.state == 'connected'

    @pytest.mark.asyncio
    async def test_coroutine_access_by_alias(self):
        obj = SampleAsyncNS()

        conn = await obj['conn']
        assert conn.state == 'connected'

        conn = await obj['conn']
        assert conn.state == 'connected'

    @pytest.mark.asyncio
    async def test_as_context_manager(self):
        obj = SampleAsyncNS()
        conn = obj.connection
        assert conn.state is None

        async with conn:
            assert conn.state == 'connected'

        assert conn.state == 'disconnected'

    @pytest.mark.asyncio
    async def test_hooks(self):
        obj = SampleAsyncNS()

        async with obj:
            conn = obj.connection
            assert conn.state is None
            await conn.connect()
            assert conn.state == 'connected'

        assert conn.state == 'disconnected'
