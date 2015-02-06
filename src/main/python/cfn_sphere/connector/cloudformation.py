__author__ = 'mhoyer'

from urlparse import urlparse
from boto import cloudformation
from boto.resultset import ResultSet
from boto.exception import AWSConnectionError
import json
import logging


class CloudFormationTemplate(object):

    def __init__(self, template_url, template_body=None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        if not template_body:
            self.template_body = self._load_template(template_url)
        else:
            self.template_body = template_body

    def get_template_body(self):
        return self.template_body

    def _load_template(self, url):
        handler = self._get_template_handler(url)
        return handler(url)

    def _get_template_handler(self, url):
        protocol = urlparse(url).scheme
        print "PROTO: " + protocol
        if protocol.lower() == "http" or protocol.lower() == "https":
            self.logger.info("http template source detected")
            return self._http_get_template
        elif protocol.lower() == "s3":
            self.logger.info("S3 template source detected")
            return self._s3_get_template
        elif not protocol:
            self.logger.info("Filesystem template source detected")
            return self._fs_get_template
        else:
            self.logger.error("Unknown template source detected")
            raise NotImplementedError

    def _s3_get_template(self, url):
        pass

    def _http_get_template(self, url):
        pass

    def _fs_get_template(self, url):
        with open(url, 'r') as file:
            return json.loads(file.read())


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