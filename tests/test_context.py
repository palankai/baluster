from baluster import Holder


class Root(Holder):
    pass


class TestContextData:

    def test_set_and_get_value(self):
        root = Root()

        root['value'] = True
        assert root['value'] is True

        with root.enter() as ctx:
            ctx['value'] = True
            assert ctx['value'] is True

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
            ctx['value'] = 2
            assert ctx['value'] == 2
        assert root['value'] == 1

    def test_access_from_outer_scope(self):
        root = Root()

        with root.enter() as ctx:
            assert ctx['value'] is None
            ctx['value'] = 2
            assert ctx['value'] == 2
        assert root['value'] is None
