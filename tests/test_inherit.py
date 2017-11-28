"""
Test application context case, when you have multiple
level of application context.
The first level understand the raw config and some part
of command line arguments.
The second level understand the rest of the arguments
"""
import datetime

import pytest

from baluster import Baluster, placeholders


class BaseContext(Baluster):

    def __init__(self, args):
        super().__init__(args=args)

    @placeholders.factory(args=['root', 'args'])
    def config(self, root, args):
        # Value come from the argument
        return args['raw_config']

    @placeholders.factory
    def daily_alignment(self, root):
        # Value is based on other piece
        return root.config['dailyAlignment']

    @placeholders.factory
    def simple_value(self, root):
        return 1


class Context(BaseContext):

    @placeholders.factory(args=['root', 'args'])
    def from_time(self, root, args):
        return datetime.datetime.strptime(
            args['from_time'], '%Y-%m-%d %H:%M:%S'
        )

    @placeholders.factory
    def from_time_aligned(self, root):
        # Value is combined
        return self.from_time + datetime.timedelta(hours=self.daily_alignment)


class TestInheritance:

    @pytest.fixture
    def ctx(self):
        args = {
            'raw_config': {'dailyAlignment': 12},
            'from_time': '2017-12-15 06:00:00'
        }
        return Context(args=args)

    def test_access_a_simple_value(self, ctx):
        assert ctx.simple_value == 1

    def test_access_param_based_value(self, ctx):
        assert ctx.daily_alignment == 12

    def test_second_level_value(self, ctx):
        expected = datetime.datetime(2017, 12, 15, 6, 0, 0)
        assert ctx.from_time == expected

    def test_combined_second_level_value(self, ctx):
        expected = datetime.datetime(2017, 12, 15, 18, 0, 0)
        assert ctx.from_time_aligned == expected
