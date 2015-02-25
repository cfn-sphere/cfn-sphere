__author__ = 'mhoyer'

import unittest2
import os
from cfn_sphere.stack_handler import StackHandler


class CreateStacksTest(object):

    def test_sync_creates_stacks(self):
        test_resources_dir = os.path.join(os.path.dirname(__file__), '../resources')
        stack_handler = StackHandler(os.path.join(test_resources_dir, "stacks.yml"), test_resources_dir)
        stack_handler.sync()


if __name__ == "__main__":
    test = CreateStacksTest()
    test.test_sync_creates_stacks()