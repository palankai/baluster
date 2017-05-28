from baluster import Holder, placeholders


class Root(Holder):

    def __init__(self, *args, **kwargs):
        self._called = []
        super().__init__(*args, **kwargs)

    class foo(Holder):

        @placeholders.factory
        def foo(self, root):
            root._called.append('foo.foo')
            return 1

        @placeholders.factory
        def bar(self, root):
            root._called.append('foo.bar')
            return 1

    class foobar(Holder):

        @placeholders.factory
        def bar(self, root):
            root._called.append('foobar.bar')
            return 1


class TestPartialCopy:

    def test_without_argument(self):
        root = Root()
        root.foo.foo
        root.foo.bar
        root.foobar.bar
        root.foo.foo

        assert root._called == ['foo.foo', 'foo.bar', 'foobar.bar']

        copy = root.partial_copy()

        copy.foo.foo
        copy.foo.bar
        copy.foobar.bar
        copy.foo.foo

        assert copy._called == ['foo.foo', 'foo.bar', 'foobar.bar']

    def test_with_explicit_names(self):
        root = Root()
        root.foo.foo
        root.foo.bar
        root.foobar.bar
        root.foo.foo

        assert root._called == ['foo.foo', 'foo.bar', 'foobar.bar']

        copy = root.partial_copy('foo.foo', 'foo.bar')

        copy.foo.foo
        copy.foo.bar
        copy.foobar.bar
        copy.foo.foo

        assert copy._called == ['foobar.bar']

    def test_with_implicit_names(self):
        root = Root()
        root.foo.foo
        root.foo.bar
        root.foobar.bar
        root.foo.foo

        assert root._called == ['foo.foo', 'foo.bar', 'foobar.bar']

        copy = root.partial_copy('foo')

        copy.foo.foo
        copy.foo.bar
        copy.foobar.bar
        copy.foo.foo

        assert copy._called == ['foobar.bar']

    def test_with_wrong_name(self):
        root = Root()
        root.foo.foo
        root.foo.bar
        root.foobar.bar

        copy = root.partial_copy('fo', 'fooo.bar', 'foo.ba', 'foo.')

        copy.foo.foo
        copy.foo.bar
        copy.foobar.bar

        assert copy._called == ['foo.foo', 'foo.bar', 'foobar.bar']
