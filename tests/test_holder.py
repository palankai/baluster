import pytest

from baluster import Holder, make


class CompositeRootCase(Holder):

    _value = 0
    _closed = False

    _closed_resources = None

    @make
    def value(self, root):
        return self._value

    @make
    def value_plus_100(self, root):
        return self._value + 100

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

    @make
    def resource_1(self, root):
        return 1

    @resource_1.close
    def _close_resource_1(self, root, resource):
        if self._closed_resources is None:
            self._closed_resources = []
        self._closed_resources.append(resource)

    @make(cache=False)
    def resource_2(self, root):
        return 2

    @resource_2.close
    def _close_resource_2(self, root, resource):
        if self._closed_resources is None:
            self._closed_resources = []
        self._closed_resources.append(resource)


class TestHolder:

    def test_sanity(self):
        obj = CompositeRootCase()

        assert obj.value == 0

    def test_class_level_access(self):
        assert CompositeRootCase.value._name == 'value'

    def test_closed_without_invoke(self):
        obj = CompositeRootCase()
        exception_raised = False

        try:
            with obj:
                raise ZeroDivisionError()
        except ZeroDivisionError:
            exception_raised = True

        assert obj._closed_resources is None
        assert exception_raised is True

    def test_closed_with_invoke(self):
        obj = CompositeRootCase()
        exception_raised = False

        try:
            with obj:
                obj.resource_1
                obj.resource_2
                obj.resource_2
                raise ZeroDivisionError()
        except ZeroDivisionError:
            exception_raised = True
        assert exception_raised is True

        assert obj._closed_resources == [2, 2, 1]

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

    def test_close_action_copy(self):
        obj = CompositeRootCase()
        with obj:
            obj.resource_1
            obj.resource_2
            copy = obj.copy('resource_1')
        assert obj._closed_resources == [2, 1]

        with copy:
            pass
        assert copy._closed_resources == [1]