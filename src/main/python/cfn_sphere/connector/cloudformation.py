__author__ = 'mhoyer'

from boto import cloudformation
from boto.resultset import ResultSet
from boto.exception import AWSConnectionError
import logging


class CloudFormation(object):

    def __init__(self, region="eu-west-1", stacks= None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.conn = cloudformation.connect_to_region(region)
        if not self.conn:
            self.logger.error("Could not connect to cloudformation API in {0}. Invalid region?".format(region))
            raise AWSConnectionError("Got None connection object")

        self.logger.info("Connected to cloudformation API at {0} with access key id: {1}".format(
            region, self.conn.aws_access_key_id))

        self.stacks = stacks
        if not self.stacks:
            self._load_stacks()

        assert isinstance(self.stacks, ResultSet)

    def _load_stacks(self):
        self.stacks = self.conn.describe_stacks()
        assert isinstance(self.stacks, ResultSet)

    def get_stacks(self):
        return self.stacks

    def get_stacks_dict(self):
        stacks_dict = {}
        for stack in self.stacks:
            stacks_dict[stack.stack_name] = {"parameters": stack.parameters, "outputs": stack.outputs}
        return stacks_dict

    def create_stack(self, template):
        self.conn.create_stack("bla", template_body={}, parameters=[])


if __name__ == "__main__":
    cfn = CloudFormation()