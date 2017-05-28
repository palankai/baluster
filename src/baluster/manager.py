from .exceptions import ContextManagerReusedError


class Manager:

    __slots__ = ('_managed', '_active')

    def __init__(self, managed):
        self._managed = managed
        self._active = False

    def __enter__(self):
        if self._active is True:
            raise ContextManagerReusedError()
        self._active = True
        return self._managed

    def __exit__(self, exc_type, exc_value, traceback):
        self._active = False
        self._managed.close()


class AsyncManager(Manager):

    __slots__ = ()

    async def __aenter__(self):
        return self._managed

    async def __aexit__(self, exc_type, exc_value, traceback):
        await self._managed.aclose()
