__author__ = 'mhoyer'

from cfn_sphere.connector.cloudformation import CloudFormation
import logging


class ArtifactResolver(object):

    def __init__(self, region="eu-west-1", stacks= None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.cfn = CloudFormation(region)

    def get_available_artifacts(self):
        artifacts = {}
        stacks = self.cfn.get_stacks()
        for stack in stacks:
            for output in stack.outputs:
                key = stack.stack_name + '.' + output.key
                value = output.value

                artifacts[key] = value
        return artifacts

    def get_artifact_value(self, key):
        artifacts = self.get_available_artifacts()
        try:
            return artifacts[key]
        except KeyError:
            return None

if __name__ == "__main__":
    cfn = ArtifactResolver()

    print cfn.get_available_artifacts()
    print cfn.get_artifact_value("betasearch-test.S3LogBucket")
    print cfn.get_artifact_value("betasearch-live.S3LogBucket")
    print cfn.get_artifact_value("blalbufg")