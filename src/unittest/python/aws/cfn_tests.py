import datetime
from datetime import timedelta
from dateutil.tz import tzutc

import unittest2
from mock import Mock, patch
from boto.cloudformation.stack import StackEvent, Stack
from boto.exception import BotoServerError

from cfn_sphere.template import CloudFormationTemplate
from cfn_sphere.aws.cfn import CloudFormationStack
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.exceptions import CfnStackActionFailedException, CfnSphereBotoError


class CloudFormationApiTests(unittest2.TestCase):
    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_get_stacks_correctly_handles_pagination(self, boto_mock):
        stacks_1 = [Mock(spec=Stack), Mock(spec=Stack)]
        stacks_2 = [Mock(spec=Stack), Mock(spec=Stack)]
        boto_mock.return_value.get_paginator.return_value.paginate.return_value = [{'Stacks': stacks_1},
                                                                                   {'Stacks': stacks_2}]

        cfn = CloudFormation()
        print(cfn.get_stacks())
        self.assertListEqual(stacks_1 + stacks_2, cfn.get_stacks())

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_events_returns_on_start_event_with_valid_timestamp(self, cloudformation_mock):
        timestamp = datetime.datetime.utcnow()

        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body_dict.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "UPDATE_IN_PROGRESS"
        event.event_id = "123"
        event.timestamp = timestamp

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        event = cfn.wait_for_stack_events("foo", "UPDATE_IN_PROGRESS",
                                          timestamp - timedelta(seconds=10),
                                          timeout=10)

        self.assertEqual(timestamp, event.timestamp)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_events_returns_on_update_complete(self, cloudformation_mock):
        timestamp = datetime.datetime.utcnow()

        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body_dict.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "UPDATE_COMPLETE"
        event.event_id = "123"
        event.timestamp = timestamp

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        cfn.wait_for_stack_events("foo", "UPDATE_COMPLETE", timestamp - timedelta(seconds=10),
                                  timeout=10)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_events_raises_exception_on_rollback(self, cloudformation_mock):
        timestamp = datetime.datetime.utcnow()

        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body_dict.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "ROLLBACK_COMPLETE"
        event.event_id = "123"
        event.timestamp = timestamp

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        with self.assertRaises(Exception):
            cfn.wait_for_stack_events("foo", ["UPDATE_COMPLETE"], timestamp - timedelta(seconds=10),
                                      timeout=10)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_events_raises_exception_on_update_failure(self, cloudformation_mock):
        timestamp = datetime.datetime.utcnow()

        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body_dict.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "UPDATE_FAILED"
        event.event_id = "123"
        event.timestamp = timestamp

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        with self.assertRaises(Exception):
            cfn.wait_for_stack_events("foo", ["UPDATE_COMPLETE"], timestamp - timedelta(seconds=10),
                                      timeout=10)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_event_returns_expected_event(self, _):
        event = {
            'PhysicalResourceId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'StackName': 'my-stack',
            'LogicalResourceId': 'cfn-sphere-test-vpc',
            'StackId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'ResourceType': 'AWS::CloudFormation::Stack',
            'Timestamp': datetime.datetime(2016, 4, 1, 8, 3, 27, 548000, tzinfo=tzutc()),
            'EventId': 'my-event-id',
            'ResourceStatus': 'CREATE_COMPLETE'
        }
        valid_from_timestamp = datetime.datetime(2016, 4, 1, 8, 3, 25, 548000, tzinfo=tzutc())
        cfn = CloudFormation()

        result = cfn.wait_for_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertDictEqual(event, result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_event_returns_none_if_event_appears_to_early(self, _):
        event = {
            'PhysicalResourceId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'StackName': 'my-stack',
            'LogicalResourceId': 'cfn-sphere-test-vpc',
            'StackId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'ResourceType': 'AWS::CloudFormation::Stack',
            'Timestamp': datetime.datetime(2016, 4, 1, 8, 3, 27, 548000, tzinfo=tzutc()),
            'EventId': 'my-event-id',
            'ResourceStatus': 'CREATE_COMPLETE'
        }
        valid_from_timestamp = datetime.datetime(2016, 4, 1, 8, 3, 30, 548000, tzinfo=tzutc())
        cfn = CloudFormation()

        result = cfn.wait_for_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_event_returns_none_if_event_has_not_expected_state(self, _):
        event = {
            'PhysicalResourceId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'StackName': 'my-stack',
            'LogicalResourceId': 'cfn-sphere-test-vpc',
            'StackId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'ResourceType': 'AWS::CloudFormation::Stack',
            'Timestamp': datetime.datetime(2016, 4, 1, 8, 3, 27, 548000, tzinfo=tzutc()),
            'EventId': 'my-event-id',
            'ResourceStatus': 'CREATE_IN_PROGRESS'
        }
        valid_from_timestamp = datetime.datetime(2016, 4, 1, 8, 3, 25, 548000, tzinfo=tzutc())
        cfn = CloudFormation()

        result = cfn.wait_for_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_event_returns_none_if_event_is_no_stack_event(self, _):
        event = {
            'PhysicalResourceId': 'arn:aws:sns:eu-west-1:1234567890:my-topic',
            'StackName': 'my-stack',
            'LogicalResourceId': 'VPC',
            'StackId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'ResourceType': 'AWS::SNS::Topic',
            'Timestamp': datetime.datetime(2016, 4, 1, 8, 3, 27, 548000, tzinfo=tzutc()),
            'EventId': 'my-event-id',
            'ResourceStatus': 'CREATE_COMPLETE'
        }
        valid_from_timestamp = datetime.datetime(2016, 4, 1, 8, 3, 25, 548000, tzinfo=tzutc())
        cfn = CloudFormation()

        result = cfn.wait_for_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_event_raises_exception_on_error_event(self, _):
        event = {
            'PhysicalResourceId': 'arn:aws:sns:eu-west-1:1234567890:my-topic',
            'StackName': 'my-stack',
            'LogicalResourceId': 'VPC',
            'StackId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'ResourceType': 'AWS::CloudFormation::Stack',
            'Timestamp': datetime.datetime(2016, 4, 1, 8, 3, 27, 548000, tzinfo=tzutc()),
            'EventId': 'my-event-id',
            'ResourceStatus': 'UPDATE_FAILED'
        }
        valid_from_timestamp = datetime.datetime(2016, 4, 1, 8, 3, 25, 548000, tzinfo=tzutc())
        cfn = CloudFormation()

        with self.assertRaises(CfnStackActionFailedException):
            cfn.wait_for_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_event_returns_none_on_rollback_in_progress_state(self, _):
        event = {
            'PhysicalResourceId': 'arn:aws:sns:eu-west-1:1234567890:my-topic',
            'StackName': 'my-stack',
            'LogicalResourceId': 'VPC',
            'StackId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'ResourceType': 'AWS::CloudFormation::Stack',
            'Timestamp': datetime.datetime(2016, 4, 1, 8, 3, 27, 548000, tzinfo=tzutc()),
            'EventId': 'my-event-id',
            'ResourceStatus': 'ROLLBACK_IN_PROGRESS',
            'ResourceStatusReason': 'Foo'
        }
        valid_from_timestamp = datetime.datetime(2016, 4, 1, 8, 3, 25, 548000, tzinfo=tzutc())
        cfn = CloudFormation()

        result = cfn.wait_for_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_wait_for_stack_event_raises_exception_on_rollback_complete(self, _):
        event = {
            'PhysicalResourceId': 'arn:aws:sns:eu-west-1:1234567890:my-topic',
            'StackName': 'my-stack',
            'LogicalResourceId': 'VPC',
            'StackId': 'arn:aws:cloudformation:eu-west-1:1234567890:stack/my-stack/my-stack-id',
            'ResourceType': 'AWS::CloudFormation::Stack',
            'Timestamp': datetime.datetime(2016, 4, 1, 8, 3, 27, 548000, tzinfo=tzutc()),
            'EventId': 'my-event-id',
            'ResourceStatus': 'ROLLBACK_COMPLETE'
        }
        valid_from_timestamp = datetime.datetime(2016, 4, 1, 8, 3, 25, 548000, tzinfo=tzutc())
        cfn = CloudFormation()

        with self.assertRaises(CfnStackActionFailedException):
            cfn.wait_for_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")

    @patch('cfn_sphere.aws.cfn.boto3.client')
    @patch('cfn_sphere.aws.cfn.CloudFormation.wait_for_stack_action_to_complete')
    def test_create_stack_calls_cloudformation_api_properly(self, _, cloudformation_mock):
        stack = Mock(spec=CloudFormationStack)
        stack.name = "stack-name"
        stack.get_parameters_list.return_value = [('a', 'b')]
        stack.tags = [('any-tag', 'any-tag-value')]
        stack.parameters = {}
        stack.template = Mock(spec=CloudFormationTemplate)
        stack.template.name = "template-name"
        stack.template.get_template_json.return_value = {'key': 'value'}
        stack.timeout = 42

        cfn = CloudFormation()
        cfn.create_stack(stack)

        cloudformation_mock.return_value.create_stack.assert_called_once_with('stack-name',
                                                                              capabilities=['CAPABILITY_IAM'],
                                                                              parameters=[('a', 'b')],
                                                                              tags=[('any-tag', 'any-tag-value')],
                                                                              template_body={'key': 'value'})

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_update_stack_calls_cloudformation_api_properly(self, _, cloudformation_mock):
        stack = Mock(spec=CloudFormationStack)
        stack.name = "stack-name"
        stack.get_parameters_list.return_value = [('a', 'b')]
        stack.tags = [('any-tag', 'any-tag-value')]
        stack.parameters = {}
        stack.template = Mock(spec=CloudFormationTemplate)
        stack.template.name = "template-name"
        stack.template.get_template_json.return_value = {'key': 'value'}
        stack.timeout = 42

        cfn = CloudFormation()
        cfn.update_stack(stack)

        cloudformation_mock.return_value.update_stack.assert_called_once_with('stack-name',
                                                                              capabilities=['CAPABILITY_IAM'],
                                                                              parameters=[('a', 'b')],
                                                                              tags=[('any-tag', 'any-tag-value')],
                                                                              template_body={'key': 'value'})

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_validate_stack_is_ready_for_action_raises_exception_on_unknown_stack_state(self, cloudformation_mock):
        describe_stack_mock = Mock()
        describe_stack_mock.stack_status = "FOO"
        describe_stack_mock.stack_name = "my-stack"

        cloudformation_mock.return_value.describe_stacks.return_value = [describe_stack_mock]

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnStackActionFailedException):
            cfn.validate_stack_is_ready_for_action(stack)

        cloudformation_mock.return_value.describe_stacks.assert_called_once_with('my-stack')

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_validate_stack_is_ready_for_action_raises_exception_on_bad_stack_state(self, cloudformation_mock):
        describe_stack_mock = Mock()
        describe_stack_mock.stack_status = "UPDATE_IN_PROGRESS"
        describe_stack_mock.stack_name = "my-stack"

        cloudformation_mock.return_value.describe_stacks.return_value = [describe_stack_mock]

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnStackActionFailedException):
            cfn.validate_stack_is_ready_for_action(stack)

        cloudformation_mock.return_value.describe_stacks.assert_called_once_with('my-stack')

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_validate_stack_is_ready_for_action_raises_proper_exception_on_boto_error(self, cloudformation_mock):
        cloudformation_mock.return_value.describe_stacks.side_effect = BotoServerError('400', 'Bad Request')

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnSphereBotoError):
            cfn.validate_stack_is_ready_for_action(stack)

        cloudformation_mock.return_value.describe_stacks.assert_called_once_with('my-stack')

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_validate_stack_is_ready_for_action_passes_if_stack_is_in_good_state(self, cloudformation_mock):
        describe_stack_mock = Mock()
        describe_stack_mock.stack_status = "UPDATE_COMPLETE"
        describe_stack_mock.stack_name = "my-stack"

        cloudformation_mock.return_value.describe_stacks.return_value = [describe_stack_mock]

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        cfn.validate_stack_is_ready_for_action(stack)

        cloudformation_mock.return_value.describe_stacks.assert_called_once_with('my-stack')

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_get_stack_parameters_dict_returns_proper_dict(self, _, get_stack_mock):
        cfn = CloudFormation()

        parameter_1 = Mock()
        parameter_1.key = "myKey1"
        parameter_1.value = "myValue1"
        parameter_2 = Mock()
        parameter_2.key = "myKey2"
        parameter_2.value = "myValue2"

        stack_mock = Mock()
        stack_mock.parameters = [parameter_1, parameter_2]
        get_stack_mock.return_value = stack_mock

        result = cfn.get_stack_parameters_dict('foo')

        self.assertDictEqual({'myKey1': 'myValue1', 'myKey2': 'myValue2'}, result)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_get_stack_parameters_dict_returns_empty_dict_for_empty_parameters(self, _, get_stack_mock):
        cfn = CloudFormation()

        stack_mock = Mock()
        stack_mock.parameters = []
        get_stack_mock.return_value = stack_mock

        result = cfn.get_stack_parameters_dict('foo')

        self.assertDictEqual({}, result)

    def test_is_boto_no_update_required_exception_returns_false_with_other_exception(self):
        exception = Mock(spec=Exception)
        exception.message = "No updates are to be performed."
        self.assertFalse(CloudFormation.is_boto_no_update_required_exception(exception))

    def test_is_boto_no_update_required_exception_returns_false_without_message(self):
        exception = Mock(spec=BotoServerError)
        exception.message = "Something went wrong."
        self.assertFalse(CloudFormation.is_boto_no_update_required_exception(exception))

    def test_is_boto_no_update_required_exception_returns_true_for_message(self):
        exception = Mock(spec=BotoServerError)
        exception.message = "No updates are to be performed."
        self.assertTrue(CloudFormation.is_boto_no_update_required_exception(exception))
