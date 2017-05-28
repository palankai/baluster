import pytest

from baluster import Baluster


class Root(Baluster):
    pass


class TestContextData:

    def test_set_and_get_value(self):
        root = Root()

        root['value'] = True
        assert root['value'] is True
        assert 'value' in root

        with pytest.raises(KeyError):
            root['unknown']

        with root.enter() as ctx:
            ctx['value'] = True
            assert ctx['value'] is True
            assert 'value' in ctx

    def test_access_root_inside_context(self):
        root = Root()

        root['value'] = 1

        with root.enter() as ctx:
            assert ctx['value'] == 1

    def test_reassign_value(self):
        root = Root()

        root['value'] = 1

        with root.enter() as ctx:
            assert ctx['value'] == 1
            assert 'value' in ctx
            ctx['value'] = 2
            assert ctx['value'] == 2
        assert root['value'] == 1

    def test_access_from_outer_scope(self):
        root = Root()

        with root.enter() as ctx:
            ctx['value'] = 2
            assert ctx['value'] == 2

        with pytest.raises(KeyError):
            root['value']

    def test_deleting_values(self):
        root = Root()
        root['value'] = 1

        del root['value']

        assert 'value' not in root

        with pytest.raises(KeyError):
            del root['value']

    def test_deleting_values_from_different_scope(self):
        root = Root()
        root['a'] = 1

        with root.enter() as ctx:
            assert ctx['a'] == 1
            with pytest.raises(KeyError):
                del ctx['a']
            assert ctx['a'] == 1
