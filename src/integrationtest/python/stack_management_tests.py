import os
import logging

import unittest2
from boto import cloudformation
from boto.ec2 import autoscale
from boto.exception import BotoServerError

from cfn_sphere import StackActionHandler
from cfn_sphere.stack_configuration import Config

LOGGER = logging.getLogger(__name__)
LOGGER.setLevel(logging.INFO)
logging.getLogger('cfn_sphere').setLevel(logging.DEBUG)


def get_resources_dir():
    return os.path.join(os.path.dirname(__file__), '../resources')


def verify_stacks_are_gone(cfn_conn, config):
    for stack_name in config.stacks.keys():
        try:
            stack = cfn_conn.describe_stacks(stack_name)[0]
            if stack.stack_status != "DELETE_COMPLETE":
                raise Exception("Stack {0} seems to exist but should not".format(stack_name))
        except BotoServerError:
            pass


def get_output_dict_from_stack(stack):
    result = {}
    for output in stack.outputs:
        result[output.key] = output.value
    return result


def get_parameter_dict_from_stack(stack):
    result = {}
    for parameter in stack.parameters:
        result[parameter.key] = parameter.value
    return result


class CreateStacksTest(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        test_resources_dir = get_resources_dir()
        cls.cfn_conn = cloudformation.connect_to_region("eu-west-1")
        cls.config = Config(config_file=os.path.join(test_resources_dir, "stacks.yml"))
        cls.stack_handler = StackActionHandler(cls.config)

        LOGGER.info("Syncing stacks")
        cls.stack_handler.create_or_update_stacks()

    @classmethod
    def tearDownClass(cls):
        LOGGER.info("Cleaning up")
        cls.stack_handler.delete_stacks()
        verify_stacks_are_gone(cls.cfn_conn, cls.config)

    def test_stacks_are_in_update_complete_state(self):
        LOGGER.info("Verifying stacks are in CREATE_COMPLETE state")

        for stack_name in self.config.stacks.keys():
            stack = self.cfn_conn.describe_stacks(stack_name)[0]
            self.assertEqual("CREATE_COMPLETE", stack.stack_status)

    def test_instance_stack_uses_vpc_outputs(self):
        vpc_stack = self.cfn_conn.describe_stacks("cfn-sphere-test-vpc")[0]
        instance_stack = self.cfn_conn.describe_stacks("cfn-sphere-test-instances")[0]

        vpc_stack_outputs = get_output_dict_from_stack(vpc_stack)
        instance_stack_parameters = get_parameter_dict_from_stack(instance_stack)
        vpc_stack_parameters = get_parameter_dict_from_stack(vpc_stack)

        self.assertEqual(vpc_stack_outputs["id"], instance_stack_parameters["vpcID"])
        self.assertEqual(vpc_stack_outputs["subnet"], instance_stack_parameters["subnetID"])
        self.assertEqual(vpc_stack_parameters["testtag"], "unchanged")

    def test_userdata(self):
        autoscale_conn = autoscale.connect_to_region("eu-west-1")
        instance_stack_resources = self.cfn_conn.describe_stack_resource("cfn-sphere-test-instances", "lc")
        lc_name = \
            instance_stack_resources["DescribeStackResourceResponse"]["DescribeStackResourceResult"][
                "StackResourceDetail"][
                "PhysicalResourceId"]
        lc = autoscale_conn.get_all_launch_configurations(names=[lc_name])[0]

        user_data_lines = lc.user_data.split('\n')

        self.assertEqual("#taupage-ami-config", user_data_lines[0])

        self.assertTrue("application_version: 1" in user_data_lines)
        self.assertTrue("  stack: cfn-sphere-test-instances" in user_data_lines)

        dockercfg_root_index = user_data_lines.index("dockercfg:")
        self.assertEqual("  https://my-private-registry:", user_data_lines[dockercfg_root_index + 1])
        self.assertEqual("    email: test@example.com", user_data_lines[dockercfg_root_index + 2])
        self.assertEqual("    auth: my-secret-string", user_data_lines[dockercfg_root_index + 3])

        environment_root_index = user_data_lines.index("environment:")
        self.assertEqual("  DYNAMO_DB_PREFIX: cfn-sphere-test-instances", user_data_lines[environment_root_index + 1])

        notify_cfn_root_index = user_data_lines.index("notify_cfn:")
        self.assertEqual("  resource: asg", user_data_lines[notify_cfn_root_index + 1])
        self.assertEqual("  stack: cfn-sphere-test-instances", user_data_lines[notify_cfn_root_index + 2])

        ports_root_index = user_data_lines.index("ports:")
        self.assertEqual("  8080: 9000", user_data_lines[ports_root_index + 1])



class UpdateStacksWithCliParamsTest(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        test_resources_dir = get_resources_dir()
        cls.cfn_conn = cloudformation.connect_to_region("eu-west-1")
        cls.config = Config(config_file=os.path.join(test_resources_dir, "stacks.yml"))
        cls.stack_handler = StackActionHandler(cls.config)
        LOGGER.info("Creating stacks")
        cls.stack_handler.create_or_update_stacks()

        cls.config = Config(config_file=os.path.join(test_resources_dir, "stacks.yml"),
                            cli_params='cfn-sphere-test-instances:appVersion=42,cfn-sphere-test-vpc:testtag=changed')
        cls.stack_handler = StackActionHandler(cls.config)
        LOGGER.info("Updating stack with cli params")
        cls.stack_handler.create_or_update_stacks()

    @classmethod
    def tearDownClass(cls):
        LOGGER.info("Cleaning up")
        cls.stack_handler.delete_stacks()
        verify_stacks_are_gone(cls.cfn_conn, cls.config)

    def test_stacks_are_in_update_complete_state(self):
        LOGGER.info("Verifying stacks are in UPDATE_COMPLETE state")

        for stack_name in self.config.stacks.keys():
            stack = self.cfn_conn.describe_stacks(stack_name)[0]
            self.assertEqual("UPDATE_COMPLETE", stack.stack_status)

    def test_instance_stack_uses_vpc_outputs(self):
        vpc_stack = self.cfn_conn.describe_stacks("cfn-sphere-test-vpc")[0]
        instance_stack = self.cfn_conn.describe_stacks("cfn-sphere-test-instances")[0]

        vpc_stack_outputs = get_output_dict_from_stack(vpc_stack)
        instance_stack_parameters = get_parameter_dict_from_stack(instance_stack)
        vpc_stack_parameters = get_parameter_dict_from_stack(vpc_stack)

        self.assertEqual(vpc_stack_outputs["id"], instance_stack_parameters["vpcID"])
        self.assertEqual(vpc_stack_outputs["subnet"], instance_stack_parameters["subnetID"])
        self.assertEqual(vpc_stack_parameters["testtag"], "changed")

    def test_userdata(self):
        autoscale_conn = autoscale.connect_to_region("eu-west-1")
        instance_stack_resources = self.cfn_conn.describe_stack_resource("cfn-sphere-test-instances", "lc")
        lc_name = \
            instance_stack_resources["DescribeStackResourceResponse"]["DescribeStackResourceResult"][
                "StackResourceDetail"][
                "PhysicalResourceId"]
        lc = autoscale_conn.get_all_launch_configurations(names=[lc_name])[0]

        user_data_lines = lc.user_data.split('\n')

        self.assertEqual("#taupage-ami-config", user_data_lines[0])

        self.assertTrue("application_version: 42" in user_data_lines)
        self.assertTrue("  stack: cfn-sphere-test-instances" in user_data_lines)

        dockercfg_root_index = user_data_lines.index("dockercfg:")
        self.assertEqual("  https://my-private-registry:", user_data_lines[dockercfg_root_index + 1])
        self.assertEqual("    email: test@example.com", user_data_lines[dockercfg_root_index + 2])
        self.assertEqual("    auth: my-secret-string", user_data_lines[dockercfg_root_index + 3])

        environment_root_index = user_data_lines.index("environment:")
        self.assertEqual("  DYNAMO_DB_PREFIX: cfn-sphere-test-instances", user_data_lines[environment_root_index + 1])

        notify_cfn_root_index = user_data_lines.index("notify_cfn:")
        self.assertEqual("  resource: asg", user_data_lines[notify_cfn_root_index + 1])
        self.assertEqual("  stack: cfn-sphere-test-instances", user_data_lines[notify_cfn_root_index + 2])

        ports_root_index = user_data_lines.index("ports:")
        self.assertEqual("  8080: 9000", user_data_lines[ports_root_index + 1])


if __name__ == "__main__":
    unittest2.main()
