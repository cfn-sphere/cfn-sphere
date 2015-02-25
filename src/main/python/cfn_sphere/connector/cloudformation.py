__author__ = 'mhoyer'

from boto import cloudformation
from boto.resultset import ResultSet
from boto.exception import AWSConnectionError, BotoServerError
import json
import logging
import time
import os


class CloudFormationTemplate(object):
    def __init__(self, template_url, template_body=None, config_dir=None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.config_dir = config_dir
        self.url = template_url
        self.body = template_body

        if not self.body:
            self.body = self._load_template(self.url)

    def get_template_body(self):
        return self.body

    def _load_template(self, url):
        self.logger.debug("Working in {0}".format(os.getcwd()))
        if url.lower().startswith("s3://"):
            return self._s3_get_template(url)
        else:
            return self._fs_get_template(url)

    def _fs_get_template(self, url):
        if not os.path.isabs(url) and self.config_dir:
            url = os.path.join(self.config_dir, url)

        try:
            with open(url, 'r') as template_file:
                return json.loads(template_file.read())
        except ValueError as e:
            self.logger.error("Could not load template from {0}: {1}".format(url, e.strerror))
            # TODO: handle error condition
            raise
        except IOError as e:
            self.logger.error("Could not load template from {0}: {1}".format(url, e.strerror))
            raise

    def _s3_get_template(self, url):
        raise NotImplementedError


class CloudFormation(object):
    def __init__(self, region="eu-west-1", stacks=None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.conn = cloudformation.connect_to_region(region)
        if not self.conn:
            self.logger.error("Could not connect to cloudformation API in {0}. Invalid region?".format(region))
            raise AWSConnectionError("Got None connection object")

        self.logger.debug("Connected to cloudformation API at {0} with access key id: {1}".format(
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

    def create_stack(self, stack_name, template, parameters):
        assert isinstance(template, CloudFormationTemplate)
        try:
            self.logger.info(
                "Creating stack {0} from template {1} with parameters: {2}".format(stack_name, template.url,
                                                                                   parameters))
            self.conn.create_stack(stack_name,
                                   template_body=json.dumps(template.get_template_body()),
                                   parameters=parameters)
            self.wait_for_update_complete(stack_name)
        except BotoServerError as e:
            self.logger.error(
                "Could not create stack {0}. Cloudformation API response: {1}".format(stack_name, e.message))

    def wait_for_update_complete(self, stack_name, timeout=600):
        start = time.time()
        while time.time() < (start + timeout):
            for event in self.get_stack_events(stack_name):
                print event
                if event.resource_status.endswith("_COMPLETE"):
                    return True
            time.sleep(5)
        return False


    def get_stack_events(self, stack_name):
        return self.conn.describe_stack_events(stack_name)


if __name__ == "__main__":
    cfn = CloudFormation()