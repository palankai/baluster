from baluster import Holder, make


class CompositeRoot(Holder):

    @make
    def value(self, root):
        return 2

    class subns(Holder):

        @make
        def value(self, root):
            return 1

    class subns_2(Holder):

        @make(alias='subns_2_value')
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
        assert obj['subns_2_value'] == 6
