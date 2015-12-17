import os
import logging

import unittest2
from boto import cloudformation

from cfn_sphere import StackActionHandler
from cfn_sphere.stack_configuration import Config

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
logging.getLogger('cfn_sphere').setLevel(logging.DEBUG)


def get_resources_dir():
    return os.path.join(os.path.dirname(__file__), '../resources')


class CreateStacksTest(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        test_resources_dir = get_resources_dir()
        cls.config = Config(config_file=os.path.join(test_resources_dir, "stacks.yml"))
        cls.stack_handler = StackActionHandler(cls.config)

        LOGGER.info("Syncing stacks")
        cls.stack_handler.create_or_update_stacks()

    @classmethod
    def tearDownClass(cls):
        LOGGER.info("Cleaning up")
        cls.stack_handler.delete_stacks()

    def test_stacks_are_in_create_complete_state(self):
        LOGGER.info("Verifying stacks are in CREATE_COMPLETE state")
        cfn = cloudformation.connect_to_region("eu-west-1")

        for stack_name in self.config.stacks.keys():
            stack = cfn.describe_stacks(stack_name)[0]
            self.assertEqual("CREATE_COMPLETE", stack.stack_status)


if __name__ == "__main__":
    unittest2.main()
