from baluster import Holder


class CompositeRoot(Holder):

    @Holder.factory
    def value(self, root):
        return 2

    class subns(Holder):

        _closed = False

        @Holder.factory
        def value(self, root):
            return 1

        @value.close
        def close_value(self, root, resource):
            self._closed = True

    class subns_2(Holder):

        @Holder.factory
        def value(self, root):
            return root.subns.value + 3


class TestNested:

    def test_sanity(self):
        obj = CompositeRoot()

        assert obj.value == 2
        assert obj.subns.value == 1

    def test_cross_access(self):
        obj = CompositeRoot()
        obj.subns.value = 3

        assert obj.subns_2.value == 6

    def test_nested_close(self):
        obj = CompositeRoot()
        obj.subns.value
        obj.close()

        assert obj.subns._closed is True

    def test_nested_copy(self):
        obj = CompositeRoot()
        copyA = obj.copy('subns.value')

        obj.subns.value = 3
        copyB = obj.copy('subns.value')

        assert copyA.subns_2.value == 4
        assert copyB.subns_2.value == 6
