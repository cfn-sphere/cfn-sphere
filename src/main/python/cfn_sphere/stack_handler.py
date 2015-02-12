__author__ = 'mhoyer'

from cfn_sphere.stack_config import StackConfig
from cfn_sphere.artifact_resolver import ArtifactResolver
from cfn_sphere.connector.cloudformation import CloudFormation, CloudFormationTemplate
from boto.cloudformation.stack import Stack
import logging


class StackHandler(object):
    def __init__(self):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.desired_stacks = StackConfig("resources/stacks.yml").get()

    def sync(self):
        for name, data in self.desired_stacks.iteritems():
            self.logger.info("### Working on stack {0} ###".format(name))
            cfn = CloudFormation(region=data["region"])
            artifacts_resolver = ArtifactResolver(region=data["region"])

            existing_stacks = cfn.get_stacks_dict()

            if name not in existing_stacks:
                self.logger.info("Stack <{0}> doesn't exist, will create it".format(name))

                template = CloudFormationTemplate(data["template"])
                parameters = self.resolve_parameters(artifacts_resolver, data.get("parameters", {}))

                #TODO: make this a synchronous call
                cfn.create_stack(name, template, parameters)
            else:
                self.logger.info("Stack <{0}> exists and probably needs an update".format(name))
                # TODO: check if stack needs update

    @staticmethod
    def get_parameter_key_from_ref_value(value):
        if not value:
            return ""

        stripped_value = value.partition('::')[2]
        return stripped_value

    @staticmethod
    def is_parameter_reference(value):
        if value.lower().startswith("ref::"):
            return True
        else:
            return False

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

    def resolve_parameters(self, artifacts_resolver, parameters):
        param_list = []
        for key, value in parameters.iteritems():

            if isinstance(value, list):

                self.logger.debug("List parameter found for {0}".format(key))
                value_string = self.convert_list_to_string(value)
                param_list.append((key, value_string))

            elif isinstance(value, basestring):

                self.logger.debug("String parameter found for {0}".format(key))

                if self.is_parameter_reference(value):
                    stripped_value = self.get_parameter_key_from_ref_value(value)
                    self.logger.debug(
                        "Resolved artifact value: ".format(artifacts_resolver.get_artifact_value(stripped_value)))
                    param_list.append((key, artifacts_resolver.get_artifact_value(stripped_value)))
                else:
                    param_list.append((key, str(value)))
            elif isinstance(value, bool):

                self.logger.debug("Boolean parameter found for {0}".format(key))
                param_list.append((key, str(value).lower()))
            else:
                raise NotImplementedError("Cannot handle {0} value for key: {1}".format(type(value), key))

        return param_list


if __name__ == "__main__":
    # template = CloudFormationTemplate("resources/vpc.json")
    # print template

    stack_handler = StackHandler()
    stack_handler.sync()