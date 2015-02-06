__author__ = 'mhoyer'

from cfn_sphere.stack_config import StackConfig
from cfn_sphere.artifact_resolver import ArtifactResolver
from cfn_sphere.connector.cloudformation import CloudFormation
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
            existing_stacks = CloudFormation(region=data["region"]).get_stacks_dict()
            artifacts_resolver = ArtifactResolver(region=data["region"])

            if name not in existing_stacks:
                self.logger.info("Stack <{0}> doesn't exist, will create it".format(name))
            else:
                self.logger.info("Stack <{0}> exists and probably needs an update".format(name))
                #TODO: check if stack needs update

            self.get_new_stack_parameters(data.get("parameters", {}))

    def get_new_stack_parameters(self, parameters):
        for key, value in parameters.iteritems():
            if isinstance(value, list):
                self.logger.info("List parameter found for {0}".format(key))
                for item in value:
                    #TODO: handle value here
                    pass
            elif isinstance(value, basestring):
                self.logger.info("String parameter found for {0}".format(key))
                #TODO: handle value here
                if value.startswith("Ref::"):
                    self.logger.info("Resolved artifact value: ".format(self.artifacts_resolver.get_artifact_value(value)))

                    #print "Parameter: " + key + ": " + str(value)
            else:
                raise NotImplementedError("Cannot handle {0} value for key: {1}".format(type(value), key))


if __name__ == "__main__":
    stack_handler = StackHandler()
    stack_handler.sync()