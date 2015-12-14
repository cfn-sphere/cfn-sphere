import os
import time
import logging

import unittest2
from boto import cloudformation

from cfn_sphere.main import StackActionHandler
from cfn_sphere.stack_config.config import Config

LOGGER = logging.getLogger(__name__)


def get_resources_dir():
    return os.path.join(os.path.dirname(__file__), '../resources')


def cleanup_stacks():
    cfn = cloudformation.connect_to_region("eu-west-1")

    cfn.delete_stack("cfn-sphere-test-instances")
    wait_for_stack_to_disappear("cfn-sphere-test-instances")
    cfn.delete_stack("cfn-sphere-test-vpc")
    wait_for_stack_to_disappear("cfn-sphere-test-vpc")


def wait_for_stack_to_disappear(stack_name):
    LOGGER.info("Waiting for stack {0} to disappear".format(stack_name))
    cfn = cloudformation.connect_to_region("eu-west-1")

    for i in range(1, 30):
        stacks = [stack.stack_name for stack in cfn.list_stacks() if stack.stack_status != "DELETE_COMPLETE"]
        if stack_name not in stacks:
            return
        time.sleep(10)
        i += 1

    raise Exception("Timeout occured waiting for stack {0} to disappear".format(stack_name))


class CreateStacksTest(unittest2.TestCase):
    def test_sync_stacks(self):
        LOGGER.info("Cleaning up old stacks")
        cleanup_stacks()

        test_resources_dir = get_resources_dir()
        config = Config(config_file=os.path.join(test_resources_dir, "stacks.yml"))
        stack_handler = StackActionHandler(config)

        LOGGER.info("Syncing stacks")
        stack_handler.create_or_update_stacks()

        LOGGER.info("Cleaning up")
        cleanup_stacks()


if __name__ == "__main__":
    unittest2.main()
