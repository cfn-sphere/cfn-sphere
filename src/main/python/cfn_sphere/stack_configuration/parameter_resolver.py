from cfn_sphere.exceptions import CfnSphereException, CfnSphereBotoErrorException
from cfn_sphere.util import get_logger
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.aws.ec2 import Ec2Api
from cfn_sphere.aws.kms import KMS
from cfn_sphere.stack_configuration.dependency_resolver import DependencyResolver

import pprint

class ParameterResolver(object):
    """
    Resolves a given artifact identifier to the value of a stacks output.
    """

    def __init__(self, region="eu-west-1"):
        self.logger = get_logger()
        self.cfn = CloudFormation(region)
        self.ec2 = Ec2Api(region)
        self.kms = KMS(region)

    @staticmethod
    def convert_list_to_string(value):
        if not value:
            return ""

        value_string = ""
        for item in value:
            if value_string:
                value_string += ','
            value_string += str(item)
        return value_string

    def get_stack_outputs(self):
        """
        Get a list of all available stack outputs in format <stack-name>.<output>.
        :return: dict
        """
        artifacts = {}
        stacks = self.cfn.get_stacks()
        for stack in stacks:
            for output in stack.outputs:
                key = stack.stack_name + '.' + output.key
                artifacts[key] = output.value
        return artifacts

    def get_output_value(self, key):
        """
        Get value for a specific output key in format <stack-name>.<output>.
        :param key: str <stack-name>.<output>
        :return: str
        """
        artifacts = self.get_stack_outputs()
        self.logger.debug("Looking up key: {0}".format(key))
        self.logger.debug("Found artifacts:\n{0}".format(pprint.pformat(artifacts)))
        try:
            artifact = artifacts[key]
            return artifact
        except KeyError:
            raise CfnSphereException("Could not get a valid value for {0}.".format(key))

    @staticmethod
    def is_keep_value(value):
        return value.lower().startswith('|keeporuse|')

    @staticmethod
    def is_taupage_ami_reference(value):
        return value.lower() == '|latesttaupageami|'

    @staticmethod
    def is_kms(value):
        return value.lower().startswith('|kms|')

    @staticmethod
    def get_default_from_keep_value(value):
        return value.split('|', 2)[2]

    def get_latest_value(self, key, value, stack_name):
        try:
            if self.cfn.stack_exists(stack_name):
                latest_stack_parameters = self.cfn.get_stack_parameters_dict(stack_name)
                latest_value = latest_stack_parameters.get(key, None)
                if latest_value:
                    self.logger.info("Will keep '{0}' as latest value for {1}".format(latest_value, key))
                    return latest_value
                else:
                    return self.get_default_from_keep_value(value)
            else:
                return self.get_default_from_keep_value(value)
        except CfnSphereBotoErrorException as e:
            raise CfnSphereException("Could not get latest value for {0}: {1}".format(key, e))

    def resolve_parameter_values(self, parameters_dict, stack_name):
        parameters = {}

        for key, value in parameters_dict.items():

            if isinstance(value, list):

                self.logger.debug("List parameter found for {0}".format(key))
                for i, item in enumerate(value):
                    if DependencyResolver.is_parameter_reference(item):
                        referenced_stack, output_name = DependencyResolver.parse_stack_reference_value(item)
                        value[i] = str(self.get_output_value(referenced_stack + '.' + output_name))

                value_string = self.convert_list_to_string(value)
                parameters[key] = value_string

            elif isinstance(value, str):

                if DependencyResolver.is_parameter_reference(value):
                    referenced_stack, output_name = DependencyResolver.parse_stack_reference_value(value)
                    parameters[key] = str(self.get_output_value(referenced_stack + '.' + output_name))

                elif self.is_keep_value(value):
                    parameters[key] = str(self.get_latest_value(key, value, stack_name))

                elif self.is_taupage_ami_reference(value):
                    parameters[key] = str(self.ec2.get_latest_taupage_image_id())

                elif self.is_kms(value):
                    parameters[key] = str(self.kms.decrypt(value.split('|', 2)[2]))

                else:
                    parameters[key] = value

            elif isinstance(value, bool):
                parameters[key] = str(value).lower()
            elif isinstance(value, (int, float)):
                parameters[key] = str(value)
            else:
                raise NotImplementedError("Cannot handle {0} type for key: {1}".format(type(value), key))

        return parameters

    @staticmethod
    def update_parameters_with_cli_parameters(parameters, cli_parameters, stack_name):
        """
        Overwrite parameters from stack_config with those provided by user by cli
        :param parameters: dict
        :param cli_parameters: dict
        :param stack_name: string
        :return: dict

        """
        if stack_name in cli_parameters.keys():
            for new_key, new_value in cli_parameters[stack_name].items():
                parameters[new_key] = new_value

        return parameters
