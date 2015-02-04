__author__ = 'mhoyer'

from cfn_sphere.stack_config import StackConfig
from cfn_sphere.artifact_resolver import ArtifactResolver
import logging


class StackHandler(object):

    def __init__(self, region="eu-west-1", stacks= None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.stacks = StackConfig("resources/stacks.yml").get()
        self.artifacts = ArtifactResolver()

    def sync(self):
        for name, data in self.stacks.iteritems():
            self.logger.info("### Working on stack {0} ###".format(name))
            parameters = data.get("parameters", {})
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
                        self.logger.info("Resolved artifact value: ".format(self.artifacts.get_artifact_value(value)))

                    #print "Parameter: " + key + ": " + str(value)
                else:
                    raise NotImplementedError("Cannot handle {0} value for key: {1}".format(type(value), key))



if __name__ == "__main__":
    stack_handler = StackHandler()
    stack_handler.sync()