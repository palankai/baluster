from baluster import Baluster, placeholders


class CompositeRoot(Baluster):

    class params(Baluster):

        @placeholders.factory(args=['root', 'env'])
        def debug(self, root, env):
            if env is None:
                return None
            return env.get('DEBUG', False)

    @placeholders.factory(cache=False)
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
        obj = CompositeRoot(env={'DEBUG': True}).partial_copy()

        assert obj.resource == 'debug'
