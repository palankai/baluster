import pytest

from ns.base import NS, make, enter


class CompositeRoot(NS):

    @make
    def value(self, root):
        return 2

    class subns(NS):

        @make
        def value(self, root):
            return 1

    class subns_2(NS):

        @make(alias='subns_2_value')
        def value(self, root):
            return root.subns.value + 3


class TestNestedNS:

    def test_sanity(self):
        obj = CompositeRoot()

        assert obj.value == 2
        assert obj.subns.value == 1

    def test_cross_access(self):
        obj = CompositeRoot()
        obj.subns.value = 3

        assert obj.subns_2.value == 6
        assert obj['subns_2_value'] == 6
