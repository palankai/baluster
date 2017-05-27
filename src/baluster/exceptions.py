class MultipleExceptions(Exception):

    def __init__(self, exceptions):
        self._exceptions = exceptions
        super().__init__('Multiple exceptions occured')

    @property
    def exceptions(self):
        return self._exceptions


class ContextManagerReusedError(Exception):
    pass
