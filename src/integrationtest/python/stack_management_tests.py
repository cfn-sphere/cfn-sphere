import os
import logging

from boto import cloudformation
from boto.ec2 import autoscale
from boto.exception import BotoServerError

from cfn_sphere import StackActionHandler
from cfn_sphere.stack_configuration import Config

logging.getLogger('cfn_sphere').setLevel(logging.DEBUG)


class CfnSphereIntegrationTest(object):
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.test_resources_dir = self._get_resources_dir()
        self.cfn_conn = cloudformation.connect_to_region("eu-west-1")
        self.config = Config(config_file=os.path.join(self.test_resources_dir, "stacks.yml"))

    @staticmethod
    def _get_resources_dir():
        return os.path.join(os.path.dirname(__file__), '../resources')

    @staticmethod
    def get_output_dict_from_stack(stack):
        result = {}
        for output in stack.outputs:
            result[output.key] = output.value
        return result

    @staticmethod
    def get_parameter_dict_from_stack(stack):
        result = {}
        for parameter in stack.parameters:
            result[parameter.key] = parameter.value
        return result

    def verify_stacks_are_gone(self):
        for stack_name in self.config.stacks.keys():
            try:
                stack = self.cfn_conn.describe_stacks(stack_name)[0]
                if stack.stack_status != "DELETE_COMPLETE":
                    raise Exception("Stack {0} seems to exist but should not".format(stack_name))
            except BotoServerError:
                pass

    def sync_stacks(self):
        stack_handler = StackActionHandler(self.config)
        self.logger.info("Syncing stacks")
        stack_handler.create_or_update_stacks()

    def delete_stacks(self):
        StackActionHandler(self.config).delete_stacks()
        self.verify_stacks_are_gone()

    def test_stacks_are_in_create_complete_state(self):
        self.logger.info("Verifying stacks are in CREATE_COMPLETE state")

        for stack_name in self.config.stacks.keys():
            stack = self.cfn_conn.describe_stacks(stack_name)[0]
            self.assert_equal("CREATE_COMPLETE", stack.stack_status)

    def test_stacks_are_in_update_complete_state(self):
        self.logger.info("Verifying stacks are in CREATE_COMPLETE state")

        for stack_name in self.config.stacks.keys():
            stack = self.cfn_conn.describe_stacks(stack_name)[0]
            self.assert_equal("UPDATE_COMPLETE", stack.stack_status)

    @staticmethod
    def assert_equal(a, b):
        if not a == b:
            raise Exception("'{0}' is not '{1}'".format(a, b))

    @staticmethod
    def assert_true(a):
        if not isinstance(a, bool) and not a:
            raise Exception("{0} is not true".format(a))


class StackCreationTests(CfnSphereIntegrationTest):
    def test_instance_stack_uses_vpc_outputs(self):
        self.logger.info("Verifying cfn-sphere-test-instances uses referenced values from cfn-sphere-test-vpc stack")

        vpc_stack = self.cfn_conn.describe_stacks("cfn-sphere-test-vpc")[0]
        instance_stack = self.cfn_conn.describe_stacks("cfn-sphere-test-instances")[0]

        vpc_stack_outputs = self.get_output_dict_from_stack(vpc_stack)
        instance_stack_parameters = self.get_parameter_dict_from_stack(instance_stack)
        vpc_stack_parameters = self.get_parameter_dict_from_stack(vpc_stack)

        self.assert_equal(vpc_stack_outputs["id"], instance_stack_parameters["vpcID"])
        self.assert_equal(vpc_stack_outputs["subnetA"], instance_stack_parameters["subnetID"])
        self.assert_equal(vpc_stack_parameters["testtag"], "unchanged")

    def test_userdata(self):
        self.logger.info("Verifying user-data from instance in cfn-sphere-test-instances")

        autoscale_conn = autoscale.connect_to_region("eu-west-1")
        instance_stack_resources = self.cfn_conn.describe_stack_resource("cfn-sphere-test-instances", "lc")
        lc_name = \
            instance_stack_resources["DescribeStackResourceResponse"]["DescribeStackResourceResult"][
                "StackResourceDetail"][
                "PhysicalResourceId"]
        lc = autoscale_conn.get_all_launch_configurations(names=[lc_name])[0]

        user_data_lines = lc.user_data.split('\n')

        self.assert_equal("#taupage-ami-config", user_data_lines[0])

        self.assert_true("application_version: 1" in user_data_lines)
        self.assert_true("  stack: cfn-sphere-test-instances" in user_data_lines)

        dockercfg_root_index = user_data_lines.index("dockercfg:")
        self.assert_equal("  https://my-private-registry:", user_data_lines[dockercfg_root_index + 1])
        self.assert_equal("    email: test@example.com", user_data_lines[dockercfg_root_index + 2])
        self.assert_equal("    auth: my-secret-string", user_data_lines[dockercfg_root_index + 3])

        environment_root_index = user_data_lines.index("environment:")
        self.assert_equal("  DYNAMO_DB_PREFIX: cfn-sphere-test-instances", user_data_lines[environment_root_index + 1])

        notify_cfn_root_index = user_data_lines.index("notify_cfn:")
        self.assert_equal("  resource: asg", user_data_lines[notify_cfn_root_index + 1])
        self.assert_equal("  stack: cfn-sphere-test-instances", user_data_lines[notify_cfn_root_index + 2])

        ports_root_index = user_data_lines.index("ports:")
        self.assert_equal("  8080: 9000", user_data_lines[ports_root_index + 1])

    def run(self, setup=True, cleanup=True):
        if setup:
            self.logger.info("### Preparing tests ###")
            self.delete_stacks()
            self.verify_stacks_are_gone()
            self.sync_stacks()

        self.logger.info("### Executing tests ###")
        self.test_stacks_are_in_create_complete_state()
        self.test_userdata()
        self.test_instance_stack_uses_vpc_outputs()

        if cleanup:
            self.logger.info("### Cleaning up environment ###")
            self.delete_stacks()
            self.verify_stacks_are_gone()


if __name__ == "__main__":
    StackCreationTests().run()
