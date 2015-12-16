import os
import logging

import unittest2
from boto import cloudformation

from cfn_sphere import StackActionHandler
from cfn_sphere.stack_configuration import Config

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.DEBUG)
logging.getLogger('cfn_sphere').setLevel(logging.DEBUG)


def get_resources_dir():
    return os.path.join(os.path.dirname(__file__), '../resources')


def verify_stack_status(config):
    cfn = cloudformation.connect_to_region("eu-west-1")

    for stack_name in config.stacks.keys():
        stack = cfn.describe_stacks(stack_name)[0]
        if stack.stack_status != "CREATE_COMPLETE":
            raise Exception(
                "Stack {0} is in {1} state, expected 'CREATE_COMPLETE'".format(stack_name, stack.stack_status))


class CreateStacksTest(unittest2.TestCase):
    def test_sync_stacks(self):
        test_resources_dir = get_resources_dir()
        config = Config(config_file=os.path.join(test_resources_dir, "stacks.yml"))

        stack_handler = StackActionHandler(config)

        LOGGER.info("Syncing stacks")
        stack_handler.create_or_update_stacks()

        LOGGER.info("Verifying stack state")
        verify_stack_status(config)

        LOGGER.info("Cleaning up")
        stack_handler.delete_stacks()


if __name__ == "__main__":
    unittest2.main()
