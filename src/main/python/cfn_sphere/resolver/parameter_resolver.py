from cfn_sphere.util import get_logger
from cfn_sphere.cloudformation.api import CloudFormation
from cfn_sphere.resolver.dependency_resolver import DependencyResolver


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

    def get_available_artifacts(self):
        """
        Get a list of all available artifacts
        :return: dict
        """
        artifacts = {}
        stacks = self.cfn.get_stacks()
        for stack in stacks:
            for output in stack.outputs:
                key = stack.stack_name + '.' + output.key
                value = output.value

                artifacts[key] = value
        return artifacts

    def get_artifact_value(self, key):
        """
        Get value for a specific artifact key in format <stack-name>.<output>.
        :param key: str <stack-name>.<output>
        :return: str
        """
        artifacts = self.get_available_artifacts()
        self.logger.debug("Looking up key: {0}".format(key))
        self.logger.debug("Found artifacts: {0}".format(artifacts))
        try:
            artifact = artifacts[key]
            assert artifact, "No value found"
            return artifact
        except Exception:
            raise ParameterResolverException("Could not get a valid value for {0}".format(key))

    def resolve_parameters(self, parameters):
        param_list = []
        for key, value in parameters.items():

            if isinstance(value, list):

                self.logger.debug("List parameter found for {0}".format(key))
                value_string = self.convert_list_to_string(value)
                param_list.append((key, value_string))

            elif isinstance(value, str):

                self.logger.debug("String parameter found for {0}".format(key))

                if DependencyResolver.is_parameter_reference(value):
                    stripped_value = DependencyResolver.get_parameter_key_from_ref_value(value)
                    self.logger.debug(
                        "Resolved artifact value: ".format(self.get_artifact_value(stripped_value)))
                    param_list.append((key, self.get_artifact_value(stripped_value)))
                else:
                    param_list.append((key, str(value)))
            elif isinstance(value, bool):

                self.logger.debug("Boolean parameter found for {0}".format(key))
                param_list.append((key, str(value).lower()))
            else:
                raise NotImplementedError("Cannot handle {0} value for key: {1}".format(type(value), key))

        return param_list


if __name__ == "__main__":
    cfn = ParameterResolver()

    print(cfn.get_available_artifacts())
    print(cfn.get_artifact_value("simple-cloud-rest-api.WebsiteURL"))
    # print(cfn.get_artifact_value("blalbufg"))