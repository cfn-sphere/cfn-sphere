__author__ = 'mhoyer'

from cfn_sphere.connector.cloudformation import CloudFormation
import logging


class ArtifactResolverException(Exception):
    pass


class ArtifactResolver(object):
    """
    Resolves a given artifact identifier to the value of a stacks output.
    """

    def __init__(self, region="eu-west-1"):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.cfn = CloudFormation(region)

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
            raise ArtifactResolverException("Could not get a valid value for {0}".format(key))


if __name__ == "__main__":
    cfn = ArtifactResolver()

    print(cfn.get_available_artifacts())
    print(cfn.get_artifact_value("simple-cloud-rest-api.WebsiteURL"))
    #print(cfn.get_artifact_value("blalbufg"))