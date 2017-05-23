from baluster import Holder


class CompositeRoot(Holder):

    class params(Holder):

        @Holder.factory
        def debug(self, root):
            return root._params.get('env', {}).get('DEBUG', False)

    @Holder.factory(cache=False)
    def resource(self, root):
        if root.params.debug:
            return 'debug'
        else:
            return 'production'


class TestParams:

    def test_access_default_params(self):
        obj = CompositeRoot()

        assert obj.resource == 'production'

    def test_access_params(self):
        obj = CompositeRoot(env={'DEBUG': True})

        assert obj.resource == 'debug'

    def test_access_params_after_copy(self):
        obj = CompositeRoot(env={'DEBUG': True}).copy()

        assert obj.resource == 'debug'
