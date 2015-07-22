__author__ = 'mhoyer'

import unittest2
from cfn_sphere.stack_config import StackConfig
from mock import patch, mock_open


class StackConfigTests(unittest2.TestCase):

    STACK_CONFIG = """
stacks:
    stack_a:
        template: foo.json
        region: foo-region
"""
