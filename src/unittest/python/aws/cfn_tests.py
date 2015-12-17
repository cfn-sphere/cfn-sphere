import datetime
from datetime import timedelta

import unittest2
from mock import Mock, patch
from boto.cloudformation.stack import StackEvent, Stack
from boto.exception import BotoServerError
from boto.resultset import ResultSet

from cfn_sphere.template import CloudFormationTemplate
from cfn_sphere.aws.cfn import CloudFormationStack
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.exceptions import CfnStackActionFailedException, CfnSphereBotoError


class CloudFormationApiTests(unittest2.TestCase):
    @patch('cfn_sphere.aws.cfn.cloudformation')
    def test_get_stacks_correctly_calls_aws_api(self, cloudformation_mock):
        stacks = [Mock(spec=Stack), Mock(spec=Stack)]

        result = ResultSet()
        result.extend(stacks)
        result.next_token = None
        cloudformation_mock.connect_to_region.return_value.describe_stacks.return_value = result

        cfn = CloudFormation()
        self.assertListEqual(stacks, cfn.get_stacks())

    @patch('cfn_sphere.aws.cfn.cloudformation')
    def test_get_stacks_correctly_aggregates_paged_results(self, cloudformation_mock):
        stacks_1 = [Mock(spec=Stack), Mock(spec=Stack)]
        stacks_2 = [Mock(spec=Stack), Mock(spec=Stack)]

        result_1 = ResultSet()
        result_1.extend(stacks_1)
        result_1.next_token = "my-next-token"

        result_2 = ResultSet()
        result_2.extend(stacks_2)
        result_2.next_token = None

        cloudformation_mock.connect_to_region.return_value.describe_stacks.side_effect = [result_1, result_2]

        cfn = CloudFormation()
        self.assertListEqual(stacks_1 + stacks_2, cfn.get_stacks())

    @patch('cfn_sphere.aws.cfn.cloudformation')
    def test_wait_for_stack_event_returns_on_start_event_with_valid_timestamp(self, cloudformation_mock):
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

    @patch('cfn_sphere.aws.cfn.cloudformation')
    def test_wait_for_stack_event_returns_on_update_complete(self, cloudformation_mock):
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

    @patch('cfn_sphere.aws.cfn.cloudformation')
    def test_wait_for_stack_event_raises_exception_on_rollback(self, cloudformation_mock):
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

    @patch('cfn_sphere.aws.cfn.cloudformation')
    def test_wait_for_stack_event_raises_exception_on_update_failure(self, cloudformation_mock):
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

    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
    @patch('cfn_sphere.aws.cfn.CloudFormation.wait_for_stack_action_to_complete')
    def test_create_stack_calls_cloudformation_api_properly(self, _, cloudformation_mock):
        stack = Mock(spec=CloudFormationStack)
        stack.name = "stack-name"
        stack.get_parameters_list.return_value = [('a', 'b')]
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
                                                                              template_body={'key': 'value'})

    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
    @patch('cfn_sphere.aws.cfn.CloudFormation.wait_for_stack_action_to_complete')
    def test_update_stack_calls_cloudformation_api_properly(self, _, cloudformation_mock):
        stack = Mock(spec=CloudFormationStack)
        stack.name = "stack-name"
        stack.get_parameters_list.return_value = [('a', 'b')]
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
                                                                              template_body={'key': 'value'})

    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
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

    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
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

    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
    def test_validate_stack_is_ready_for_action_raises_proper_exception_on_boto_error(self, cloudformation_mock):
        cloudformation_mock.return_value.describe_stacks.side_effect = BotoServerError('400', 'Bad Request')

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnSphereBotoError):
            cfn.validate_stack_is_ready_for_action(stack)

        cloudformation_mock.return_value.describe_stacks.assert_called_once_with('my-stack')

    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
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
    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
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
    @patch('cfn_sphere.aws.cfn.cloudformation.connect_to_region')
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
