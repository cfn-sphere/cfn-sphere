from cfn_sphere.util import get_logger
from cfn_sphere.aws.cloudformation.api import CloudFormation
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
            assert artifact, "No value found"
            return artifact
        except Exception:
            raise ParameterResolverException("Could not get a valid value for {0}".format(key))

    @staticmethod
    def is_keep_value(value):
        return value.lower() == '@keep@'

    def resolve_parameter_values(self, parameters_dict, stack_name):
        parameters = {}
        for key, value in parameters_dict.items():

            if isinstance(value, list):

                self.logger.debug("List parameter found for {0}".format(key))
                value_string = self.convert_list_to_string(value)
                parameters[key] = value_string

            elif isinstance(value, str):

                self.logger.debug("String parameter found for {0}".format(key))

                if DependencyResolver.is_parameter_reference(value):
                    stripped_key = DependencyResolver.get_parameter_key_from_ref_value(value)
                    self.logger.debug(
                        "Resolved artifact value: ".format(self.get_output_value(stripped_key)))
                    parameters[key] = self.get_output_value(stripped_key)

                elif self.is_keep_value(value):
                    try:
                        actual_stack_parameters = self.cfn.get_stack_parameters_dict(stack_name)
                        actual_value = actual_stack_parameters.get(key, None)
                        if actual_value:
                            self.logger.info("Will keep '{0}' as actual value for {1}".format(actual_value, key))
                            parameters[key] = actual_value
                    except BotoServerError as e:
                        self.logger.info(
                            "Stack {0} seems to be non-existing. Could not find an actual value for {0}".format(
                                stack_name, key))

                else:
                    parameters[key] = value
            elif isinstance(value, bool):

                self.logger.debug("Boolean parameter found for {0}".format(key))
                parameters[key] = str(value).lower()
            elif isinstance(value, int):
                parameters[key] = str(value)
            elif isinstance(value, float):
                parameters[key] = str(value)
            else:
                raise NotImplementedError("Cannot handle {0} value for key: {1}".format(type(value), key))

        return parameters


if __name__ == "__main__":
    cfn = ParameterResolver()

    print(cfn.get_stack_outputs())
    print(cfn.get_output_value("simple-cloud-rest-api.WebsiteURL"))
    # print(cfn.get_artifact_value("blalbufg"))
