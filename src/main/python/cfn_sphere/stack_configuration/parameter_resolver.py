import pprint

from cfn_sphere.file_loader import FileLoader
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.aws.ec2 import Ec2Api
from cfn_sphere.aws.kms import KMS
from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.stack_configuration.dependency_resolver import DependencyResolver
from cfn_sphere.util import get_logger


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

    def get_output_value(self, stack_outputs, stack, output_key):
        """
        Get value for a specific output key in format <stack-name>.<output>.
        :param output_key: str <stack-name>.<output>
        :return: str
        """
        self.logger.debug("Looking up output {0} from stack {1}".format(output_key, stack))

        try:
            artifact = stack_outputs[stack][output_key]
            return artifact
        except KeyError:
            raise CfnSphereException("Could not get a valid value for {0}.".format(output_key))

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

    @staticmethod
    def is_file(value):
        return value.lower().startswith('|file|')

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
        except Exception as e:
            raise CfnSphereException("Could not get latest value for {0}: {1}".format(key, e))

    def resolve_parameter_values(self, stack_name, stack_config):
        resolved_parameters = {}
        stack_outputs = self.cfn.get_stacks_outputs()

        for key, value in stack_config.parameters.items():

            if isinstance(value, list):
                self.logger.debug("List parameter found for {0}".format(key))
                for i, item in enumerate(value):
                    if DependencyResolver.is_parameter_reference(item):
                        referenced_stack, output_name = DependencyResolver.parse_stack_reference_value(item)
                        value[i] = str(self.get_output_value(stack_outputs, referenced_stack, output_name))

                value_string = self.convert_list_to_string(value)
                resolved_parameters[key] = value_string

            elif isinstance(value, str):

                if DependencyResolver.is_parameter_reference(value):
                    referenced_stack, output_name = DependencyResolver.parse_stack_reference_value(value)
                    resolved_parameters[key] = str(self.get_output_value(stack_outputs, referenced_stack, output_name))

                elif self.is_keep_value(value):
                    resolved_parameters[key] = str(self.get_latest_value(key, value, stack_name))

                elif self.is_taupage_ami_reference(value):
                    resolved_parameters[key] = str(self.ec2.get_latest_taupage_image_id())

                elif self.is_kms(value):
                    resolved_parameters[key] = str(self.kms.decrypt(value.split('|', 2)[2]))

                elif self.is_file(value):
                    url = value.split('|', 2)[2]
                    resolved_parameters[key] = FileLoader.get_file(url, stack_config.working_dir)

                else:
                    resolved_parameters[key] = value

            elif isinstance(value, bool):
                resolved_parameters[key] = str(value).lower()
            elif isinstance(value, (int, float)):
                resolved_parameters[key] = str(value)
            else:
                raise NotImplementedError("Cannot handle {0} type for key: {1}".format(type(value), key))

        return resolved_parameters

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
            parameters.update(cli_parameters[stack_name])
        if None in cli_parameters:
            parameters.update(cli_parameters[None])

        return parameters
