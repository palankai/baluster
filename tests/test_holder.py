import pytest

from baluster import Holder


class CompositeRootCase(Holder):

    _value = 0
    _closed = False

    _closed_resources = None

    @Holder.factory
    def value(self, root):
        return self._value

    @Holder.factory
    def value_plus_100(self, root):
        return self._value + 100

    @Holder.factory(cache=False)
    def value_no_cache(self, root):
        self._value += 1
        return self._value

    @Holder.factory(readonly=True)
    def value_readonly(self, root):
        return self._value

    @Holder.factory
    def resource_1(self, root):
        return 1

    @resource_1.close
    def _close_resource_1(self, root, resource):
        if self._closed_resources is None:
            self._closed_resources = []
        self._closed_resources.append(resource)

    @Holder.factory(cache=False)
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
            with obj.enter():
                raise ZeroDivisionError()
        except ZeroDivisionError:
            exception_raised = True

        assert obj._closed_resources is None
        assert exception_raised is True

    def test_closed_with_invoke(self):
        obj = CompositeRootCase()
        exception_raised = False

        try:
            with obj.enter() as o:
                o.resource_1
                o.resource_2
                o.resource_2
                raise ZeroDivisionError()
        except ZeroDivisionError:
            exception_raised = True
        assert exception_raised is True

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

        copy = obj.partial_copy()
        assert copy.value == 0

    def test_copy_keep_values(self):
        obj = CompositeRootCase()
        obj.resource_1
        obj.resource_2

        copy = obj.partial_copy('resource_1', 'unknown')
        copy.close()
        assert copy._closed_resources is None
        assert obj._closed_resources is None

    def test_close_action_copy(self):
        root = CompositeRootCase()
        with root.enter() as obj:
            obj.resource_1
            obj.resource_2
        assert obj._closed_resources == [2, 1]
