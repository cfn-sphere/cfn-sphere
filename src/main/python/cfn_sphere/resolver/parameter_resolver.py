from cfn_sphere.util import get_logger
from cfn_sphere.aws.cloudformation.cfn_api import CloudFormation
from cfn_sphere.aws.ec2 import Ec2Api
from cfn_sphere.resolver.dependency_resolver import DependencyResolver
from boto.exception import BotoServerError


class ParameterResolverException(Exception):
    pass


class ParameterResolver(object):
    """
    Resolves a given artifact identifier to the value of a stacks output.
    """

    def __init__(self, region="eu-west-1"):
        self.logger = get_logger()
        self.cfn = CloudFormation(region)
        self.ec2 = Ec2Api(region)

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
        self.logger.debug("Found artifacts: {0}".format(artifacts))
        try:
            artifact = artifacts[key]
            return artifact
        except KeyError:
            raise ParameterResolverException("Could not get a valid value for {0}.".format(key))

    @staticmethod
    def is_keep_value(value):
        return value.lower().startswith('|keeporuse|')

    @staticmethod
    def is_taupage_ami_reference(value):
        return value.lower() == '|latesttaupageami|'

    @staticmethod
    def get_default_from_keep_value(value):
        return value.split('|', 2)[2]

    def get_actual_value(self, key, value, stack_name):
        try:
            actual_stack_parameters = self.cfn.get_stack_parameters_dict(stack_name)
            actual_value = actual_stack_parameters.get(key, None)
            if actual_value:
                self.logger.info("Will keep '{0}' as actual value for {1}".format(actual_value, key))
                return actual_value
            else:
                return self.get_default_from_keep_value(value)
        except BotoServerError:
            self.logger.info("Will use default value for {0}".format(key))
            return self.get_default_from_keep_value(value)

    def resolve_parameter_values(self, parameters_dict, stack_name):
        parameters = {}
        for key, value in parameters_dict.items():

            if isinstance(value, list):

                self.logger.debug("List parameter found for {0}".format(key))
                value_string = self.convert_list_to_string(value)
                parameters[key] = value_string

            elif isinstance(value, str):

                if DependencyResolver.is_parameter_reference(value):
                    referenced_stack, output_name = DependencyResolver.parse_stack_reference_value(value)
                    parameters[key] = str(self.get_output_value(referenced_stack + '.' + output_name))

                elif self.is_keep_value(value):
                    parameters[key] = str(self.get_actual_value(key, value, stack_name))

                elif self.is_taupage_ami_reference(value):
                    parameters[key] = str(self.ec2.get_latest_taupage_image_id())

                else:
                    parameters[key] = value

            elif isinstance(value, bool):
                parameters[key] = str(value).lower()
            elif isinstance(value, int):
                parameters[key] = str(value)
            elif isinstance(value, float):
                parameters[key] = str(value)
            else:
                raise NotImplementedError("Cannot handle {0} value for key: {1}".format(type(value), key))

        return parameters
