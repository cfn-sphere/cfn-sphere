__author__ = 'mhoyer'

import json
import logging
import time
import datetime
import os

from datetime import timedelta

from boto import cloudformation
from boto.exception import BotoServerError
import yaml


class NoTemplateFoundException(Exception):
    pass


class CloudFormationTemplate(object):
    def __init__(self, template_url, template_body=None, working_dir=None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.DEBUG)
        self.logger = logging.getLogger(__name__)

        self.working_dir = working_dir
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
        """
        Load cfn template from filesyste

        :param url: str template path
        :return: dict repr of cfn template
        """

        if not os.path.isabs(url) and self.working_dir:
            url = os.path.join(self.working_dir, url)

        try:
            with open(url, 'r') as template_file:
                if url.lower().endswith(".json"):
                    return json.loads(template_file.read())
                if url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                    return yaml.load(template_file.read())
        except ValueError as e:
            raise NoTemplateFoundException("Could not load template from {0}: {1}".format(url, e.strerror))
        except IOError as e:
            raise NoTemplateFoundException("Could not load template from {0}: {1}".format(url, e.strerror))

    def _s3_get_template(self, url):
        raise NotImplementedError


class CloudFormation(object):
    def __init__(self, region="eu-west-1", stacks=None):
        logging.getLogger('boto').setLevel(logging.FATAL)

        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.conn = cloudformation.connect_to_region(region)
        if not self.conn:
            self.logger.error("Could not connect to cloudformation API in {0}. Invalid region?".format(region))
            raise Exception("Got None connection object")

        self.logger.debug("Connected to cloudformation API at {0} with access key id: {1}".format(
            region, self.conn.aws_access_key_id))

    def get_stacks(self):
        result = []
        response = self.conn.describe_stacks()
        result.extend(response)
        while response.next_token:
            response = self.cfconn.describe_stacks(next_token=response.next_token)
        result.extend(response)
        return result

    def get_stack_names(self):
        return [stack.stack_name for stack in self.get_stacks()]

    def get_stacks_dict(self):
        stacks_dict = {}
        for stack in self.get_stacks():
            stacks_dict[stack.stack_name] = {"parameters": stack.parameters, "outputs": stack.outputs}
        return stacks_dict

    def get_stack(self, stack_name):
        return self.conn.describe_stacks(stack_name)[0]

    def stack_is_in_good_state(self, stack_name):
        stack = self.get_stack(stack_name)
        if stack.stack_status in ["CREATE_COMPLETE", "UPDATE_COMPLETE", "ROLLBACK_COMPLETE",
                                  "UPDATE_ROLLBACK_COMPLETE"]:
            return True
        else:
            self.logger.error("Stack {0} is in {1} state, because of: {2}".format(stack.stack_name, stack.stack_status,
                                                                                  stack.stack_status_reason))
            return False

    def get_stack_state(self, stack_name):
        stack = self.conn.describe_stacks(stack_name)
        return stack.status

    def create_stack(self, stack_name, template, parameters):
        assert isinstance(template, CloudFormationTemplate)
        try:
            self.logger.info(
                "Creating stack {0} from template {1} with parameters: {2}".format(stack_name, template.url,
                                                                                   parameters))
            self.conn.create_stack(stack_name,
                                   template_body=json.dumps(template.get_template_body()),
                                   parameters=parameters)
            self.wait_for_stack_action_to_complete(stack_name)
            self.logger.info("Create completed for {}".format(stack_name))
        except BotoServerError as e:
            self.logger.error(
                "Could not create stack {0}. Cloudformation API response: {1}".format(stack_name, e.message))
            raise

    def update_stack(self, stack_name, template, parameters):
        assert isinstance(template, CloudFormationTemplate)
        try:
            self.logger.info(
                "Updating stack {0} from template {1} with parameters: {2}".format(stack_name, template.url,
                                                                                   parameters))

            self.conn.update_stack(stack_name,
                                   template_body=json.dumps(template.get_template_body()),
                                   parameters=parameters)

            self.wait_for_stack_action_to_complete(stack_name)
            self.logger.info("Update completed for {}".format(stack_name))
        except BotoServerError as e:
            error = json.loads(e.body).get("Error", "{}")
            error_message = error.get("Message")
            if error_message == "No updates are to be performed.":
                self.logger.info("Nothing to do: {0}.".format(error_message))
            else:
                error_code = error.get("Code")
                self.logger.error("Stack '{0}' does not exist.".format(self.stack_name))
                raise Exception("{0}: {1}.".format(error_code, error_message))

    def wait_for_stack_events(self, stack_name: str, expected_events: list, valid_from_timestamp: datetime,
                              timeout: int):

        logging.debug("Waiting for {} events, newer than {}".format(expected_events, valid_from_timestamp))

        seen_event_ids = []
        start = time.time()
        while time.time() < (start + timeout):

            for event in self.conn.describe_stack_events(stack_name):
                if event.event_id not in seen_event_ids:
                    seen_event_ids.append(event.event_id)
                    if event.timestamp > valid_from_timestamp:
                        self.logger.info(event)

                        if event.resource_type == "AWS::CloudFormation::Stack":

                            if event.resource_status in expected_events:
                                return event
                            if event.resource_status.endswith("_FAILED"):
                                raise Exception("Stack is in {} state".format(event.resource_status))
                            if event.resource_status.startswith("ROLLBACK_"):
                                raise Exception("Rollback occured")

            time.sleep(10)
        raise Exception("Timeout occurred waiting for events: '{}' on stack {}".format(expected_events, stack_name))

    def wait_for_stack_action_to_complete(self, stack_name):

        start_event = self.wait_for_stack_events(stack_name, ["UPDATE_IN_PROGRESS"],
                                                 datetime.datetime.utcnow() - timedelta(seconds=10), timeout=120)
        self.wait_for_stack_events(stack_name, ["CREATE_COMPLETE", "UPDATE_COMPLETE"], start_event.timestamp,
                                   timeout=600)


if __name__ == "__main__":
    cfn = CloudFormation()
    print(cfn.get_stacks_dict())
