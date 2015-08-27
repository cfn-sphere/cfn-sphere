import json
import logging
import time
import datetime
from datetime import timedelta
from boto import cloudformation
from boto.exception import BotoServerError
from cfn_sphere.util import get_logger
from cfn_sphere.aws.cloudformation.template import CloudFormationTemplate
from cfn_sphere.exceptions import CfnStackActionFailedException


class CloudFormation(object):
    def __init__(self, region="eu-west-1"):
        logging.getLogger('boto').setLevel(logging.FATAL)
        self.logger = get_logger()

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
            response = self.conn.describe_stacks(next_token=response.next_token)
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

    def validate_stack_is_ready_for_updates(self, stack_name):
        stack = self.get_stack(stack_name)
        valid_states = ["CREATE_COMPLETE", "UPDATE_COMPLETE", "ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"]

        if stack.stack_status not in valid_states:
            raise CfnStackActionFailedException(
                "Stack {0} is in '{1}' state.".format(stack.stack_name, stack.stack_status))

    def get_stack_state(self, stack_name):
        stack = self.conn.describe_stacks(stack_name)
        return stack.status

    def create_stack(self, stack_name, template, parameters):
        assert isinstance(template, CloudFormationTemplate)
        try:
            self.logger.info(
                "Creating stack {0} from template {1} with parameters: {2}".format(stack_name, template.name,
                                                                                   parameters))
            self.conn.create_stack(stack_name,
                                   template_body=template.get_template_json(),
                                   parameters=parameters,
                                   capabilities=['CAPABILITY_IAM'])
            self.wait_for_stack_action_to_complete(stack_name, "create")
            self.logger.info("Create completed for {}".format(stack_name))
        except BotoServerError as e:
            raise CfnStackActionFailedException(
                "Could not create stack {0}. Cloudformation API response: {1}".format(stack_name, e.message))

    def update_stack(self, stack_name, template, parameters):
        assert isinstance(template, CloudFormationTemplate)
        try:
            self.logger.info(
                "Updating stack {0} from template {1} with parameters: {2}".format(stack_name, template.name,
                                                                                   parameters))

            self.conn.update_stack(stack_name,
                                   template_body=template.get_template_json(),
                                   parameters=parameters,
                                   capabilities=['CAPABILITY_IAM'])

            self.wait_for_stack_action_to_complete(stack_name, "update")
            self.logger.info("Update completed for {0}".format(stack_name))
        except BotoServerError as e:
            error = json.loads(e.body).get("Error", "{}")
            error_message = error.get("Message")
            if error_message == "No updates are to be performed.":
                self.logger.info("Nothing to do: {0}.".format(error_message))
            else:
                error_code = error.get("Code")
                raise CfnStackActionFailedException("{0}: {1}.".format(error_code, error_message))

    def wait_for_stack_events(self, stack_name, expected_event, valid_from_timestamp, timeout):

        logging.debug("Waiting for {0} events, newer than {1}".format(expected_event, valid_from_timestamp))

        seen_event_ids = []
        start = time.time()
        while time.time() < (start + timeout):

            for event in self.conn.describe_stack_events(stack_name):
                if event.event_id not in seen_event_ids:
                    seen_event_ids.append(event.event_id)
                    if event.timestamp > valid_from_timestamp:

                        if event.resource_type == "AWS::CloudFormation::Stack":
                            self.logger.debug(event)

                            if event.resource_status == expected_event:
                                return event
                            if event.resource_status.endswith("_FAILED"):
                                raise CfnStackActionFailedException(
                                    "Stack is in {0} state".format(event.resource_status))
                            if event.resource_status.startswith("ROLLBACK_"):
                                raise CfnStackActionFailedException("Rollback occured")
                        else:
                            self.logger.info(event)

            time.sleep(10)
        raise CfnStackActionFailedException(
            "Timeout occurred waiting for events: '{0}' on stack {1}".format(expected_event, stack_name))

    def wait_for_stack_action_to_complete(self, stack_name, action, timeout=600):

        allowed_actions = ["create", "update", "delete"]
        assert action.lower() in allowed_actions, "action argument must be one of {0}".format(allowed_actions)

        time_jitter_window = timedelta(seconds=10)
        minimum_event_timestamp = datetime.datetime.utcnow() - time_jitter_window
        expected_start_event = action.upper() + "_IN_PROGRESS"

        start_event = self.wait_for_stack_events(stack_name,
                                                 expected_start_event,
                                                 minimum_event_timestamp,
                                                 timeout=120)

        self.logger.info("Stack {0} started".format(action))

        minimum_event_timestamp = start_event.timestamp
        expected_complete_event = action.upper() + "_COMPLETE"

        end_event = self.wait_for_stack_events(stack_name,
                                               expected_complete_event,
                                               minimum_event_timestamp,
                                               timeout)

        elapsed = end_event.timestamp - start_event.timestamp
        self.logger.info("Stack {0} completed after {1}s".format(action, elapsed.seconds))


if __name__ == "__main__":
    cfn = CloudFormation()
    print(cfn.get_stacks_dict())
