__author__ = 'mhoyer'

import os
from cfn_sphere.main import StackActionHandler
from cfn_sphere.config import Config


# class CreateStacksTest(object):
#
#     def test_sync_creates_stacks(self):
#         test_resources_dir = os.path.join(os.path.dirname(__file__), '../resources')
#         config = StackConfig(os.path.join(test_resources_dir, "myapp.yml"))
#         stack_handler = StackActionHandler(config)
#         stack_handler.create_or_update_stacks()
#
#
# if __name__ == "__main__":
#     test = CreateStacksTest()
#     test.test_sync_creates_stacks()