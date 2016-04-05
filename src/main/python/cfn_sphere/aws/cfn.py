import logging
import time
from datetime import timedelta
from boto import cloudformation
from boto.exception import BotoServerError
from cfn_sphere.util import get_logger, get_cfn_api_server_time, get_pretty_parameters_string, with_boto_retry
from cfn_sphere.exceptions import CfnStackActionFailedException, CfnSphereBotoError

logging.getLogger('boto').setLevel(logging.FATAL)


class CloudFormationStack(object):
    def __init__(self, template, parameters, name, region, timeout=600, tags=None):
        self.template = template
        self.parameters = parameters
        self.tags = {} if tags is None else tags
        self.name = name
        self.region = region
        self.timeout = timeout

    def get_parameters_list(self):
        return [(key, value) for key, value in self.parameters.items()]


class CloudFormation(object):
    def __init__(self, region="eu-west-1"):
        self.logger = get_logger()

        self.conn = cloudformation.connect_to_region(region)
        if not self.conn:
            self.logger.error("Could not connect to cloudformation API in {0}. Invalid region?".format(region))
            raise Exception("Got None connection object")

        self.logger.debug("Connected to cloudformation API at {0} with access key id: {1}".format(
            region, self.conn.aws_access_key_id))

    def stack_exists(self, stack_name):
        if stack_name in self.get_stack_names():
            return True
        else:
            return False

    @with_boto_retry()
    def get_stacks(self):
        try:
            result = []
            response = self.conn.describe_stacks()
            result.extend(response)
            while response.next_token:
                response = self.conn.describe_stacks(next_token=response.next_token)
                result.extend(response)
            return result
        except BotoServerError as e:
            raise CfnSphereBotoError(e)

    def get_stack_names(self):
        return [stack.stack_name for stack in self.get_stacks()]

    def get_stacks_dict(self):
        stacks_dict = {}
        for stack in self.get_stacks():
            stacks_dict[stack.stack_name] = {"parameters": stack.parameters, "outputs": stack.outputs}
        return stacks_dict

    @with_boto_retry()
    def get_stack(self, stack_name):
        try:
            return self.conn.describe_stacks(stack_name)[0]
        except BotoServerError as e:
            raise CfnSphereBotoError(e)

    def validate_stack_is_ready_for_action(self, stack):
        try:
            cfn_stack = self.get_stack(stack.name)
        except BotoServerError as e:
            raise CfnSphereBotoError(e)

        valid_states = ["CREATE_COMPLETE", "UPDATE_COMPLETE", "ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"]

        if cfn_stack.stack_status not in valid_states:
            raise CfnStackActionFailedException(
                "Stack {0} is in '{1}' state.".format(cfn_stack.stack_name, cfn_stack.stack_status))

    @with_boto_retry()
    def get_stack_state(self, stack_name):
        try:
            stack = self.conn.describe_stacks(stack_name)
            return stack.status
        except BotoServerError as e:
            raise CfnSphereBotoError(e)

    def get_stack_parameters_dict(self, stack_name):
        parameters = {}
        stack = self.get_stack(stack_name)

        for parameter in stack.parameters:
            parameters[parameter.key] = parameter.value

        return parameters

    @staticmethod
    def is_boto_no_update_required_exception(exception):
        if isinstance(exception, BotoServerError) and exception.message == "No updates are to be performed.":
            return True
        else:
            return False

    @with_boto_retry()
    def get_stack_events(self, stack_name):
        return self.conn.describe_stack_events(stack_name)

    @with_boto_retry()
    def _create_stack(self, stack):
        self.conn.create_stack(stack.name,
                               template_body=stack.template.get_template_json(),
                               parameters=stack.get_parameters_list(),
                               tags=stack.tags,
                               capabilities=['CAPABILITY_IAM'])

    @with_boto_retry()
    def _update_stack(self, stack):
        self.conn.update_stack(stack.name,
                               template_body=stack.template.get_template_json(),
                               parameters=stack.get_parameters_list(),
                               tags=stack.tags,
                               capabilities=['CAPABILITY_IAM'])

    @with_boto_retry()
    def _delete_stack(self, stack):
        self.conn.delete_stack(stack.name)

    @with_boto_retry()
    def create_stack(self, stack):
        assert isinstance(stack, CloudFormationStack)
        try:
            self.logger.info(
                "Creating stack {0} from template {1} with parameters:\n{2}".format(stack.name, stack.template.name,
                                                                                    get_pretty_parameters_string(
                                                                                        stack)))
            self._create_stack(stack)

            self.wait_for_stack_action_to_complete(stack.name, "create", stack.timeout)
            self.logger.info("Create completed for {0}".format(stack.name))
        except BotoServerError as e:
            raise CfnStackActionFailedException("Could not create {0}: {1}".format(stack.name, e.message), e)

    def update_stack(self, stack):
        try:

            try:
                self._update_stack(stack)
            except BotoServerError as e:

                if self.is_boto_no_update_required_exception(e):
                    self.logger.info("Stack {0} does not need an update".format(stack.name))
                    return
                else:
                    self.logger.info(
                        "Updating stack {0} ({1}) with parameters:\n{2}".format(stack.name,
                                                                                stack.template.name,
                                                                                get_pretty_parameters_string(
                                                                                    stack)))
                    raise

            self.logger.info(
                "Updating stack {0} ({1}) with parameters:\n{2}".format(stack.name,
                                                                        stack.template.name,
                                                                        get_pretty_parameters_string(stack)))

            self.wait_for_stack_action_to_complete(stack.name, "update", stack.timeout)
            self.logger.info("Update completed for {0}".format(stack.name))

        except BotoServerError as e:
            raise CfnStackActionFailedException("Could not update {0}: {1}".format(stack.name, e.message), e)

    def delete_stack(self, stack):
        try:
            self.logger.info("Deleting stack {0}".format(stack.name))
            self._delete_stack(stack)

            try:
                self.wait_for_stack_action_to_complete(stack.name, "delete", 600)
            except BotoServerError as e:
                if e.error_code == "ValidationError" and e.message.endswith("does not exist"):
                    pass
                else:
                    raise

            self.logger.info("Deletion completed for {0}".format(stack.name))
        except BotoServerError as e:
            raise CfnStackActionFailedException("Could not delete {0}: {1}".format(stack.name, e.message))

    def wait_for_stack_events(self, stack_name, expected_event, valid_from_timestamp, timeout):
        self.logger.debug("Waiting for {0} events, newer than {1}".format(expected_event, valid_from_timestamp))

        seen_event_ids = []
        start = time.time()
        while time.time() < (start + timeout):

            events = self.get_stack_events(stack_name)
            events.reverse()

            for event in events:
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
                            if event.resource_status.endswith("ROLLBACK_IN_PROGRESS"):
                                self.logger.error(
                                    "Failed to create stack (Reason: {0})".format(event.resource_status_reason))
                            if event.resource_status.endswith("ROLLBACK_COMPLETE"):
                                raise CfnStackActionFailedException("Rollback occured")
                        else:
                            if event.resource_status.endswith("_FAILED"):
                                self.logger.error("Failed to create {0} (Reason: {1})".format(
                                    event.logical_resource_id, event.resource_status_reason))
                            else:
                                self.logger.info(event)

            time.sleep(10)
        raise CfnStackActionFailedException(
            "Timeout occurred waiting for '{0}' on stack {1}".format(expected_event, stack_name))

    def wait_for_stack_action_to_complete(self, stack_name, action, timeout):
        allowed_actions = ["create", "update", "delete"]
        assert action.lower() in allowed_actions, "action argument must be one of {0}".format(allowed_actions)

        time_jitter_window = timedelta(seconds=10)
        minimum_event_timestamp = get_cfn_api_server_time() - time_jitter_window
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

    def validate_template(self, template):
        """

        :param template_body: CloudFormationTemplate
        :return: boolean (true if valid)
        """
        try:
            self.conn.validate_template(template_body=template.get_template_json())
            return True
        except BotoServerError as e:
            raise CfnSphereBotoError(e)


if __name__ == "__main__":
    cfn = CloudFormation()
    try:
        cfn.get_stack_events("foo")
    except Exception:
        pass
