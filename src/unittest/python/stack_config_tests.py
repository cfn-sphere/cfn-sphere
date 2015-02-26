__author__ = 'mhoyer'

import unittest2
import __builtin__
from cfn_sphere.stack_config import StackConfig
from mock import patch, mock_open


class StackConfigTests(unittest2.TestCase):

    STACK_CONFIG = """
stacks:
    stack_a:
        template: foo.json
        region: foo-region
"""

    def setUp(self):
        with patch.object(__builtin__, 'open', mock_open(read_data=self.STACK_CONFIG)) as self.mock:
            self.config = StackConfig("/tmp/foo.yml")

    def test_stack_config_creation(self):
        self.mock.assert_called_once_with('/tmp/foo.yml', 'r')