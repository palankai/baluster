import pytest

from baluster import Holder, make, enter


class CompositeRootCase(Holder):

    _value = 0
    _closed = False

    @make
    def value(self, root):
        return self._value

    @make
    def value_plus_100(self, root):
        return self._value + 100

    @value.hook('dec')
    def _dec_value(self, root, amount=1):
        self._value -= amount

    @value.hook('close')
    def _close(self, root):
        self._closed = True

    @make(cache=False)
    def value_no_cache(self, root):
        self._value += 1
        return self._value

    @make(readonly=True)
    def value_readonly(self, root):
        return self._value

    @make(alias='alias')
    def value_alias(self, root):
        return 'as alias'


class TestHolder:

    def test_sanity(self):
        obj = CompositeRootCase()

        assert obj.value == 0

    def test_close(self):
        obj = CompositeRootCase()

        with enter(obj):
            pass

        assert obj._closed is True

    def test_hooks(self):
        obj = CompositeRootCase()

        obj('dec')
        assert obj._value == -1

        obj('dec', amount=2)
        assert obj._value == -3

    def test_alias(self):
        obj = CompositeRootCase()

        assert obj.value_alias == 'as alias'
        assert obj['alias'] == 'as alias'

    def test_alias_access(self):
        obj = CompositeRootCase()

        assert list(obj) == ['alias']

    def test_alias_if_set(self):
        obj = CompositeRootCase()

        obj.value_alias = 1
        assert obj['alias'] == 1

    def test_no_cahce(self):
        obj = CompositeRootCase()

        assert obj.value == 0
        assert obj.value_no_cache == 1
        assert obj.value_no_cache == 2
        assert obj.value == 0

    def test_set_new_value(self):
        obj = CompositeRootCase()

        obj.value = 3
        assert obj.value == 3
        assert obj.value_no_cache == 1
        with pytest.raises(AttributeError):
            obj.value = 5

    def test_readonly(self):
        obj = CompositeRootCase()

        with pytest.raises(AttributeError):
            obj.value_readonly = 3

    def test_cannot_be_deleted(self):
        obj = CompositeRootCase()

        with pytest.raises(AttributeError):
            del obj.value

    def test_copy(self):
        obj = CompositeRootCase()
        obj.value = 3
        assert obj.value == 3

        copy = obj.copy()
        assert copy.value == 0

    def test_copy_keep_values(self):
        obj = CompositeRootCase()
        obj.value = 3
        obj.value_plus_100 = 103
        assert obj.value == 3
        assert obj.value_plus_100 == 103

        copy = obj.copy('value')
        assert copy.value == 3
        assert copy.value_plus_100 == 100
