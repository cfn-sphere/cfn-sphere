__author__ = 'mhoyer'

import unittest2
from cfn_sphere.stack_config import StackConfig
from mock import patch, mock_open


class StackConfigTests(unittest2.TestCase):

    def setUp(self):
        self.config = StackConfig("/tmp/foo.yml")

    def test_get_returns_valid_config(self):
        with patch('cfn_sphere.stack_config.open', mock_open(read_data='bibble'), create=True) as mock:
            self.config.get()
        print mock.mock_calls