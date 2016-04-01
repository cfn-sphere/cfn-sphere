import logging
import time
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from datetime import timedelta
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
        return [{"ParameterKey": key, "ParameterValue": value} for key, value in self.parameters.items()]

    def get_tags_list(self):
        return [{"Key": key, "Value": value} for key, value in self.tags.items()]


class CloudFormation(object):
    def __init__(self, region="eu-west-1"):
        self.logger = get_logger()
        self.client = boto3.client('cloudformation', region_name=region)
        self.resource = boto3.resource('cloudformation', region_name=region)

    def get_stack(self, stack_name):
        """
        Get stack resource representation for a given stack_name
        :param stack_name: str:
        :return: boto3.resources.factory.cloudformation.Stack
        :raise CfnSphereBotoError:
        """
        try:
            return self.resource.Stack(stack_name)
        except (BotoCoreError, ClientError) as e:
            raise CfnSphereBotoError(e)

    def get_stacks(self):
        """
        Get all stacks

        :return: List(boto3.resources.factory.cloudformation.Stack)
        :raise CfnSphereBotoError:
        """
        try:
            return list(self.resource.stacks.all())
        except (BotoCoreError, ClientError) as e:
            raise CfnSphereBotoError(e)

    def stack_exists(self, stack_name):
        """
        Check if a stack exists for given stack_name

        :param stack_name: str
        :return: bool
        """
        if stack_name in self.get_stack_names():
            return True
        else:
            return False

    def get_stack_names(self):
        """
        Get a list of stack names
        :return: list(str)
        """
        return [stack.stack_name for stack in self.get_stacks()]

    def get_stacks_dict(self):
        """
        Get a dict containing all stacks with their name as key and {parameters, outputs} as value
        :return: dict
        """
        stacks_dict = {}
        for stack in self.get_stacks():
            stacks_dict[stack.stack_name] = {"parameters": stack.parameters, "outputs": stack.outputs}
        return stacks_dict

    def validate_stack_is_ready_for_action(self, stack):
        """
        Check if a stack is in a state capable for modification actions

        :param stack: cfn_sphere.aws.cfn.CloudFormationStack
        :raise CfnStackActionFailedException: if the stack is in an invalid state
        """
        cfn_stack = self.get_stack(stack.name)

        valid_states = ["CREATE_COMPLETE", "UPDATE_COMPLETE", "ROLLBACK_COMPLETE", "UPDATE_ROLLBACK_COMPLETE"]

        if cfn_stack.stack_status not in valid_states:
            raise CfnStackActionFailedException(
                "Stack {0} is in '{1}' state.".format(cfn_stack.stack_name, cfn_stack.stack_status))

    def get_stack_state(self, stack_name):
        """
        Get stack status
        :param stack_name: str
        :return: str: stack status
        :raise CfnSphereBotoError:
        """
        return self.get_stack(stack_name).stack_status

    def get_stack_parameters_dict(self, stack_name):
        """
        Get a stacks parameters
        :param stack_name: str
        :return: dict
        """
        parameters = {}
        stack = self.get_stack(stack_name)

        for parameter in stack.parameters:
            parameters[parameter["ParameterKey"]] = parameter["ParameterValue"]

        return parameters

    @staticmethod
    def is_boto_no_update_required_exception(exception):
        """
        Return true if the given exception means that a stack doesn't require an update
        :param exception: Exception
        :return: bool
        """
        if isinstance(exception, ClientError):
            if exception.response["Error"]["Message"] == "No updates are to be performed.":
                return True
            else:
                return False
        else:
            return False

    def get_stack_events(self, stack_name):
        """
        Get recent stack events for a given stack_name
        :param stack_name: str
        :return: list(dict)
        """
        paginator = self.client.get_paginator('describe_stack_events')
        return tuple(paginator.paginate(StackName=stack_name))[0]["StackEvents"]

    def _create_stack(self, stack):
        """
        Create cloudformation stack
        :param stack: cfn_sphere.aws.cfn.CloudFormationStack
        """
        self.client.create_stack(
            StackName=stack.name,
            TemplateBody=stack.template.get_template_json(),
            Parameters=stack.get_parameters_list(),
            TimeoutInMinutes=123,
            Capabilities=[
                'CAPABILITY_IAM'
            ],
            OnFailure='DELETE',
            Tags=stack.get_tags_list()
        )

    def _update_stack(self, stack):
        """
        Update cloudformation stack
        :param stack: cfn_sphere.aws.cfn.CloudFormationStack
        """
        self.client.update_stack(
            StackName=stack.name,
            TemplateBody=stack.template.get_template_json(),
            Parameters=stack.get_parameters_list(),
            Capabilities=[
                'CAPABILITY_IAM'
            ],
            Tags=stack.get_tags_list()
        )

    def _delete_stack(self, stack):
        """
        Delete cloudformation stack
        :param stack: cfn_sphere.aws.cfn.CloudFormationStack
        """
        self.client.delete_stack(StackName=stack.name)

    def create_stack(self, stack):
        assert isinstance(stack, CloudFormationStack)
        try:
            self.logger.info(
                "Creating stack {0} from template {1} with parameters:\n{2}".format(stack.name,
                                                                                    stack.template.name,
                                                                                    get_pretty_parameters_string(
                                                                                        stack)))
            self._create_stack(stack)

            self.wait_for_stack_action_to_complete(stack.name, "create", stack.timeout)
            self.logger.info("Create completed for {0}".format(stack.name))
        except (BotoCoreError, ClientError) as e:
            raise CfnStackActionFailedException("Could not create {0}: {1}".format(stack.name, e))

    def update_stack(self, stack):
        try:

            try:
                self._update_stack(stack)
            except ClientError as e:

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
        except (BotoCoreError, ClientError) as e:
            raise CfnStackActionFailedException("Could not update {0}: {1}".format(stack.name, e))

    def delete_stack(self, stack):
        try:
            self.logger.info("Deleting stack {0}".format(stack.name))
            self._delete_stack(stack)

            try:
                self.wait_for_stack_action_to_complete(stack.name, "delete", 600)
            except (BotoCoreError, ClientError) as e:
                if e.error_code == "ValidationError" and str(e).endswith("does not exist"):
                    pass
                else:
                    raise

            self.logger.info("Deletion completed for {0}".format(stack.name))
        except (BotoCoreError, ClientError) as e:
            raise CfnStackActionFailedException("Could not delete {0}: {1}".format(stack.name, e))

    def wait_for_stack_events(self, stack_name, expected_stack_event_status, valid_from_timestamp, timeout):
        self.logger.debug("Waiting for {0} events, newer than {1}".format(expected_stack_event_status,
                                                                          valid_from_timestamp))

        seen_event_ids = []
        start = time.time()
        while time.time() < (start + timeout):

            events = self.get_stack_events(stack_name)
            events.reverse()

            for event in events:
                if event["EventId"] not in seen_event_ids:
                    seen_event_ids.append(event["EventId"])
                    event = self.wait_for_stack_event(event, valid_from_timestamp, expected_stack_event_status)

                    if event:
                        return event

            time.sleep(10)
        raise CfnStackActionFailedException(
            "Timeout occurred waiting for '{0}' on stack {1}".format(expected_stack_event_status, stack_name))

    def wait_for_stack_event(self, event, valid_from_timestamp, expected_stack_event_status):
        if event["Timestamp"] > valid_from_timestamp:

            if event["ResourceType"] == "AWS::CloudFormation::Stack":
                self.logger.debug("Raw event: {0}".format(event))

                if event["ResourceStatus"] == expected_stack_event_status:
                    return event

                if event["ResourceStatus"].endswith("_FAILED"):
                    raise CfnStackActionFailedException("Stack is in {0} state".format(event["ResourceStatus"]))

                if event["ResourceStatus"].endswith("ROLLBACK_IN_PROGRESS"):
                    self.logger.error("Failed to create stack (Reason: {0})".format(event["ResourceStatusReason"]))
                    return None

                if event["ResourceStatus"].endswith("ROLLBACK_COMPLETE"):
                    raise CfnStackActionFailedException("Rollback occured")
            else:
                if event["ResourceStatus"].endswith("_FAILED"):
                    self.logger.error("Failed to create {0} (Reason: {1})".format(event["LogicalResourceId"],
                                                                                  event["ResourceStatusReason"]))
                    return None
                else:
                    status_reason = event.get("ResourceStatusReason", None)
                    status_reason_string = " ({0})".format(status_reason) if status_reason else ""
                    event_string = "{0}: {1}{2}".format(event["LogicalResourceId"],
                                                        event["ResourceStatus"],
                                                        status_reason_string)

                    self.logger.info(event_string)
                    return None

    def wait_for_stack_action_to_complete(self, stack_name, action, timeout):
        allowed_actions = ["create", "update", "delete"]
        assert action.lower() in allowed_actions, "action argument must be one of {0}".format(allowed_actions)

        time_jitter_window = timedelta(seconds=10)
        minimum_event_timestamp = get_cfn_api_server_time() - time_jitter_window
        expected_start_event_state = action.upper() + "_IN_PROGRESS"

        start_event = self.wait_for_stack_events(stack_name,
                                                 expected_start_event_state,
                                                 minimum_event_timestamp,
                                                 timeout=120)

        self.logger.info("Stack {0} started".format(action))

        minimum_event_timestamp = start_event["Timestamp"]
        expected_complete_event_state = action.upper() + "_COMPLETE"

        end_event = self.wait_for_stack_events(stack_name,
                                               expected_complete_event_state,
                                               minimum_event_timestamp,
                                               timeout)

        elapsed = end_event["Timestamp"] - start_event["Timestamp"]
        self.logger.info("Stack {0} completed after {1}s".format(action, elapsed.seconds))

    def validate_template(self, template):
        """
        Validate template
        :param template: CloudFormationTemplate
        :return: boolean (true if valid)
        """
        try:
            self.client.validate_template(template_body=template.get_template_json())
            return True
        except (BotoCoreError, ClientError) as e:
            raise CfnSphereBotoError(e)


if __name__ == "__main__":
    cfn = CloudFormation()
    print(cfn.get_stack_events("grafana"))
