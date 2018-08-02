import base64
import json
import logging
import os

import boto3
import yaml
from botocore.exceptions import ClientError
from yaml.scanner import ScannerError

from cfn_sphere import StackActionHandler
from cfn_sphere.stack_configuration import Config

logging.getLogger('cfn_sphere').setLevel(logging.DEBUG)

SSM_INTEGRATION_PLAIN_PATH = '/test-cfn-sphere/plain_parameter'
SSM_INTEGRATION_PLAIN_VALUE = 'testplainparameterssm'
SSM_INTEGRATION_ENCRYPTED_PATH = '/test-cfn-sphere/encrypted_parameter'
SSM_INTEGRATION_ENCRYPTED_VALUE = 'testencryptedparameterssm'


class CfnSphereIntegrationTest(object):
    def __init__(self, stack_name_suffix=None, cli_params=None):
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)
        self.test_resources_dir = self._get_resources_dir()
        self.cfn_conn = boto3.client('cloudformation', region_name='eu-west-1')
        self.kms_conn = boto3.client('kms', region_name='eu-west-1')
        self.ssm_conn = boto3.client('ssm', region_name='eu-west-1')
        self.config = Config(config_file=os.path.join(self.test_resources_dir, "stacks.yml"),
                             cli_params=cli_params,
                             stack_name_suffix=stack_name_suffix)

    @staticmethod
    def _get_resources_dir():
        return os.path.join(os.path.dirname(__file__), '../resources')

    @staticmethod
    def get_output_dict_from_stack(stack):
        result = {}
        for output in stack["Outputs"]:
            result[output["OutputKey"]] = output["OutputValue"]

        return result

    @staticmethod
    def get_parameter_dict_from_stack(stack):
        result = {}
        for parameter in stack["Parameters"]:
            result[parameter["ParameterKey"]] = parameter["ParameterValue"]

        return result

    def get_stack_description(self, stack_name):
        return self.cfn_conn.describe_stacks(StackName=stack_name)["Stacks"][0]

    def get_stack_policy(self, stack_name):
        return json.loads(self.cfn_conn.get_stack_policy(StackName=stack_name)["StackPolicyBody"])

    def verify_stacks_are_gone(self):
        for stack_name in self.config.stacks.keys():
            try:
                stack = self.get_stack_description(stack_name)
                if stack["StackStatus"] != "DELETE_COMPLETE":
                    raise Exception("Stack {0} seems to exist but should not".format(stack_name))
            except ClientError as e:
                if e.response["Error"]["Code"] == "ValidationError" and e.response["Error"]["Message"].endswith(
                        "does not exist"):
                    pass

    def sync_stacks(self):
        stack_handler = StackActionHandler(self.config)
        self.logger.info("Syncing stacks")
        stack_handler.create_or_update_stacks()

    def sync_stacks_with_parameters_overwrite(self, cli_params):
        config = Config(config_file=os.path.join(self.test_resources_dir, "stacks.yml"), cli_params=cli_params)
        stack_handler = StackActionHandler(config)
        self.logger.info("Syncing stacks")
        stack_handler.create_or_update_stacks()

    def delete_stacks(self):
        StackActionHandler(self.config).delete_stacks()
        self.verify_stacks_are_gone()

    def test_stacks_are_in_create_complete_state(self):
        self.logger.info("Verifying stacks are in CREATE_COMPLETE state")

        for stack_name in self.config.stacks.keys():
            stack = self.get_stack_description(stack_name)
            self.assert_equal("CREATE_COMPLETE", stack["StackStatus"])

    def test_stacks_are_in_update_complete_state(self):
        self.logger.info("Verifying stacks are in CREATE_COMPLETE state")

        for stack_name in self.config.stacks.keys():
            stack = self.get_stack_description(stack_name)
            self.assert_equal("UPDATE_COMPLETE", stack["StackStatus"])

    @staticmethod
    def assert_equal(a, b):
        if not a == b:
            raise Exception("'{0}' is not '{1}'".format(a, b))

    @staticmethod
    def assert_true(a):
        if not isinstance(a, bool) and not a:
            raise Exception("{0} is not true".format(a))


class StackManagementTests(CfnSphereIntegrationTest):
    def test_stacks_use_updated_parameters(self):
        self.logger.info("Verifying stacks use parameters given by cli")

        vpc_stack = self.get_stack_description("cfn-sphere-test-vpc")
        instance_stack = self.get_stack_description("cfn-sphere-test-instances")

        instance_stack_parameters = self.get_parameter_dict_from_stack(instance_stack)
        vpc_stack_parameters = self.get_parameter_dict_from_stack(vpc_stack)

        self.assert_equal("2", instance_stack_parameters["appVersion"])
        self.assert_equal("changed", vpc_stack_parameters["testtag"])

    def test_instance_stack_uses_vpc_outputs(self):
        self.logger.info("Verifying cfn-sphere-test-instances uses referenced values from cfn-sphere-test-vpc stack")

        vpc_stack = self.get_stack_description("cfn-sphere-test-vpc")
        instance_stack = self.get_stack_description("cfn-sphere-test-instances")

        vpc_stack_outputs = self.get_output_dict_from_stack(vpc_stack)
        instance_stack_parameters = self.get_parameter_dict_from_stack(instance_stack)
        vpc_stack_parameters = self.get_parameter_dict_from_stack(vpc_stack)

        self.assert_equal(vpc_stack_outputs["id"], instance_stack_parameters["vpcID"])
        self.assert_equal(vpc_stack_outputs["subnetA"], instance_stack_parameters["subnetID"])
        self.assert_equal(vpc_stack_parameters["testtag"], "unchanged")

    def test_instance_stack_userdata(self):
        self.logger.info("Verifying user-data of instance in cfn-sphere-test-instances")

        autoscale_conn = boto3.client('autoscaling', region_name='eu-west-1')
        instance_stack_resources = self.cfn_conn.describe_stack_resource(StackName="cfn-sphere-test-instances",
                                                                         LogicalResourceId="lc")
        lc_name = \
            instance_stack_resources["StackResourceDetail"]["PhysicalResourceId"]
        lc = autoscale_conn.describe_launch_configurations(LaunchConfigurationNames=[lc_name])["LaunchConfigurations"][
            0]
        try:
            user_data = yaml.load(base64.b64decode(lc["UserData"]))
        except ScannerError as e:
            raise Exception(
                "Could not parse yaml UserData from:\n{0}\nERROR:\n{1}".format(base64.b64decode(lc["UserData"]), e))

        self.assert_equal("cfn-sphere-test-instances", user_data["application_id"])
        self.assert_equal(1, user_data["application_version"])
        self.assert_equal("my-private-registry/foo1", user_data["source"])

        cloudwatch_logs_config = user_data["cloudwatch_logs"]
        self.assert_equal("my-syslog-group", cloudwatch_logs_config["/var/log/syslog"])
        self.assert_equal("my-application-log-group", cloudwatch_logs_config["/var/log/application.log"])

        healthcheck_config = user_data["healthcheck"]
        self.assert_equal("elb", healthcheck_config["type"])
        self.assert_equal("my-elb", healthcheck_config["loadbalancer_name"])

        notify_cfn_config = user_data["notify_cfn"]
        self.assert_equal("asg", notify_cfn_config["resource"])
        self.assert_equal("cfn-sphere-test-instances", notify_cfn_config["stack"])

        ports_config = user_data["ports"]
        self.assert_equal(9000, ports_config[8080])

        docker_config = user_data["dockercfg"]
        registry_config = docker_config["https://my-private-registry"]
        self.assert_equal("my-secret-string", registry_config["auth"])
        self.assert_equal("test@example.com", registry_config["email"])

        environment_config = user_data["environment"]
        self.assert_equal("cfn-sphere-test-instances", environment_config["DYNAMO_DB_PREFIX"])
        self.assert_equal("value-5-foo", environment_config["SOME_COMBINED_VALUE"])

        list_values = user_data["list-values"]
        print(list_values)
        self.assert_equal(len(list_values), 6)
        self.assert_equal("a", list_values[0])
        self.assert_equal("b", list_values[1])
        self.assert_equal(1, list_values[2])
        self.assert_equal(1, list_values[3])
        self.assert_equal(2, list_values[4])
        self.assert_true(isinstance(list_values[5], list))

        sublist_values = list_values[5]
        print(sublist_values)
        self.assert_equal("a", sublist_values[0])
        self.assert_equal("b", sublist_values[1])
        self.assert_equal(10, sublist_values[2])
        self.assert_equal(1, sublist_values[3])

        # uncomment this to test kms decryption
        # self.assert_equal("myCleartextString", user_data["kms_encrypted_value"])

        # test ssm configuration
        self.assert_equal(SSM_INTEGRATION_PLAIN_VALUE, user_data["ssm_plain_value"])
        self.assert_equal(SSM_INTEGRATION_ENCRYPTED_VALUE, user_data["ssm_encrypted_value"])

    def test_instance_stack_uses_file_parameter(self):
        instance_stack = self.get_stack_description("cfn-sphere-test-instances")
        instance_stack_parameters = self.get_parameter_dict_from_stack(instance_stack)
        self.assert_equal("my-text-file-parameter", instance_stack_parameters["textFileParameter"])

    def test_instance_stack_doesnt_update_without_changes(self):
        self.logger.info("Verify stack doesn't update without changes ###")
        old_stack_last_update = self.get_stack_description("cfn-sphere-test-instances")["LastUpdatedTime"]
        self.sync_stacks()
        new_stack_last_update = self.get_stack_description("cfn-sphere-test-instances")["LastUpdatedTime"]
        self.assert_equal(old_stack_last_update, new_stack_last_update)

    def test_instances_stack_has_specific_stack_policy_configured(self):
        self.logger.info("Verify vpc stack has global-stack-policy configured ###")
        stack_policy = self.get_stack_policy("cfn-sphere-test-instances")
        self.assert_true(len(stack_policy["Statement"]) == 1)

    def test_vpc_stack_has_global_stack_policy_configured(self):
        self.logger.info("Verify vpc stack has global-stack-policy configured ###")
        stack_policy = self.get_stack_policy("cfn-sphere-test-vpc")
        self.assert_true(len(stack_policy["Statement"]) == 2)

    def run(self, setup=True, cleanup=True):
        try:
            if setup:
                self.logger.info("### Preparing tests ###")
                self.ssm_conn.put_parameter(Name=SSM_INTEGRATION_PLAIN_PATH, Type='String',
                                            Value=SSM_INTEGRATION_PLAIN_VALUE)
                self.ssm_conn.put_parameter(Name=SSM_INTEGRATION_ENCRYPTED_PATH, Type='SecureString',
                                            Value=SSM_INTEGRATION_ENCRYPTED_VALUE)
                self.delete_stacks()
                self.verify_stacks_are_gone()
                self.sync_stacks()

            self.logger.info("### Executing vpc stack tests ###")
            self.test_vpc_stack_has_global_stack_policy_configured()

            self.logger.info("### Executing instances stack tests ###")
            self.test_stacks_are_in_create_complete_state()
            self.test_instance_stack_userdata()
            self.test_instance_stack_uses_vpc_outputs()
            self.test_instance_stack_uses_file_parameter()
            self.test_instances_stack_has_specific_stack_policy_configured()

            self.logger.info("### Executing cli parameter update tests ###")
            self.sync_stacks_with_parameters_overwrite(
                ("cfn-sphere-test-vpc.testtag=changed", "cfn-sphere-test-instances.appVersion=2"))
            self.test_stacks_are_in_update_complete_state()
            self.test_stacks_use_updated_parameters()

            self.test_instance_stack_doesnt_update_without_changes()

        finally:
            if cleanup:
                self.logger.info("### Cleaning up environment ###")
                self.delete_stacks()
                self.verify_stacks_are_gone()
                self.ssm_conn.delete_parameter(Name=SSM_INTEGRATION_PLAIN_PATH)
                self.ssm_conn.delete_parameter(Name=SSM_INTEGRATION_ENCRYPTED_PATH)


class StackSuffixingTests(CfnSphereIntegrationTest):
    def __init__(self):
        suffix = "-suffix"
        cli_params = ["cfn-sphere-test-vpc.testtag=value_supplied_by_cli_param"]

        super(StackSuffixingTests, self).__init__(stack_name_suffix=suffix, cli_params=cli_params)

    def test_instance_stack_uses_vpc_outputs(self):
        self.logger.info(
            "Verifying cfn-sphere-test-instances-suffix uses referenced values from cfn-sphere-test-vpc-suffix stack")

        vpc_stack = self.get_stack_description("cfn-sphere-test-vpc-suffix")
        instance_stack = self.get_stack_description("cfn-sphere-test-instances-suffix")

        vpc_stack_outputs = self.get_output_dict_from_stack(vpc_stack)
        instance_stack_parameters = self.get_parameter_dict_from_stack(instance_stack)
        vpc_stack_parameters = self.get_parameter_dict_from_stack(vpc_stack)

        self.assert_equal(vpc_stack_outputs["id"], instance_stack_parameters["vpcID"])
        self.assert_equal(vpc_stack_outputs["subnetA"], instance_stack_parameters["subnetID"])
        self.assert_equal(vpc_stack_parameters["testtag"], "value_supplied_by_cli_param")

    def run(self, setup=True, cleanup=True):
        try:
            if setup:
                self.logger.info("### Preparing tests ###")
                self.ssm_conn.put_parameter(Name=SSM_INTEGRATION_PLAIN_PATH, Type='String',
                                            Value=SSM_INTEGRATION_PLAIN_VALUE)
                self.ssm_conn.put_parameter(Name=SSM_INTEGRATION_ENCRYPTED_PATH, Type='SecureString',
                                            Value=SSM_INTEGRATION_ENCRYPTED_VALUE)

                self.delete_stacks()
                self.verify_stacks_are_gone()
                self.sync_stacks()

            self.logger.info("### Executing tests ###")
            self.test_instance_stack_uses_vpc_outputs()

        finally:
            if cleanup:
                self.logger.info("### Cleaning up environment ###")
                self.delete_stacks()
                self.verify_stacks_are_gone()
                self.ssm_conn.delete_parameter(Name=SSM_INTEGRATION_PLAIN_PATH)
                self.ssm_conn.delete_parameter(Name=SSM_INTEGRATION_ENCRYPTED_PATH)


if __name__ == "__main__":
    StackManagementTests().run()
    StackSuffixingTests().run()
