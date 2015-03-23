__author__ = 'mhoyer'

import logging

from cfn_sphere.stack_config import StackConfig
from cfn_sphere.resolver.artifact_resolver import ArtifactResolver
from cfn_sphere.resolver.dependency_resolver import DependencyResolver
from cfn_sphere.connector.cloudformation import CloudFormation, CloudFormationTemplate


class StackHandler(object):
    def __init__(self, stack_config_file, config_dir):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        stack_config = StackConfig(stack_config_file)
        self.desired_stacks = stack_config.get()
        self.config_dir = config_dir

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

                if DependencyResolver.is_parameter_reference(value):
                    stripped_value = DependencyResolver.get_parameter_key_from_ref_value(value)
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

    def sync(self):
        order = self.get_stack_order(self.desired_stacks)
        self.logger.info("Stack processing order: {0}".format(", ".join(order)))

        for stack_name in order:
            data = self.desired_stacks[stack_name]

            cfn = CloudFormation(region=data["region"])
            artifacts_resolver = ArtifactResolver(region=data["region"])

            existing_stacks = cfn.get_stacks_dict()

            if stack_name not in existing_stacks:
                self.logger.info("Stack {0} doesn't exist, will create it".format(stack_name))

                # TODO: injecting a suspect config_dir into a CloudFormationTemplate feels bad, should get refactored
                template = CloudFormationTemplate(data["template"], config_dir=self.config_dir)
                parameters = self.resolve_parameters(artifacts_resolver, data.get("parameters", {}))

                # TODO: make this a synchronous call
                cfn.create_stack(stack_name, template, parameters)
            else:
                if not cfn.stack_is_good(stack_name):
                    self.logger.error("Stack {0} is in bad state".format(stack_name))

                self.logger.info("Stack {0} exists and probably needs an update".format(stack_name))
                # TODO: check if stack needs update
                # could be changes in:
                # - template itself
                # - parameters


if __name__ == "__main__":
    # template = CloudFormationTemplate("resources/vpc.json")
    # print template

    stack_handler = StackHandler("resources/vpc.json")
    #print stack_handler.get_stack_order(stack_handler.desired_stacks)
    #stack_handler.create_action_plan(stack_handler.desired_stacks)
    #stack_handler.sync()