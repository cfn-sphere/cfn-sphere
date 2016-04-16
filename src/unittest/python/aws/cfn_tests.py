try:
    from unittest2 import TestCase
    from mock import Mock, patch
except ImportError:
    from unittest import TestCase
    from unittest.mock import Mock, patch

import datetime

from botocore.exceptions import ClientError, BotoCoreError
from dateutil.tz import tzutc

from cfn_sphere.template import CloudFormationTemplate
from cfn_sphere.aws.cfn import CloudFormationStack
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.exceptions import CfnStackActionFailedException, CfnSphereBotoError


class CloudFormationApiTests(TestCase):
    @patch('cfn_sphere.aws.cfn.boto3.resource')
    def test_get_stack_properly_calls_boto(self, boto_mock):
        CloudFormation().get_stack("Foo")
        boto_mock.return_value.Stack.assert_called_once_with("Foo")

    @patch('cfn_sphere.aws.cfn.boto3.resource')
    def test_get_stack_raises_cfnsphere_boto_exception_on_client_error(self, boto_mock):
        boto_mock.return_value.Stack.side_effect = ClientError({"Error": {"Code": "Error", "Message": "AnyMessage"}},
                                                               "FooOperation")
        with self.assertRaises(CfnSphereBotoError):
            CloudFormation().get_stack("Foo")

    @patch('cfn_sphere.aws.cfn.boto3.resource')
    def test_get_stack_raises_cfnsphere_boto_exception_on_botocore_error(self, boto_mock):
        boto_mock.return_value.Stack.side_effect = BotoCoreError()
        with self.assertRaises(CfnSphereBotoError):
            CloudFormation().get_stack("Foo")

    @patch('cfn_sphere.aws.cfn.boto3.resource')
    def test_get_stack_raises_other_exceptions_as_is(self, boto_mock):
        boto_mock.return_value.Stack.side_effect = TimeoutError()
        with self.assertRaises(TimeoutError):
            CloudFormation().get_stack("Foo")

    @patch('cfn_sphere.aws.cfn.boto3.resource')
    def test_get_stacks_properly_calls_boto(self, boto_mock):
        CloudFormation().get_stacks()
        boto_mock.return_value.stacks.all.assert_called_once_with()

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_stack_exists_returns_true_for_existing_stack(self, get_stack_mock):
        get_stack_mock.return_value = Mock()
        self.assertTrue(CloudFormation().stack_exists("stack1"))

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_stack_exists_returns_false_for_non_existing_stack(self, get_stack_mock):
        get_stack_mock.side_effect = ClientError({"Error": {"Message": "Stack with id stack3 does not exist"}}, "Foo")
        self.assertFalse(CloudFormation().stack_exists("stack3"))

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack_descriptions')
    def test_get_stacks_dict_returns_empty_dict_with_no_stacks(self, get_stack_descriptions_mock):
        get_stack_descriptions_mock.return_value = {}
        self.assertEqual({}, CloudFormation().get_stacks_dict())

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack_descriptions')
    def test_get_stacks_dict_returns_stack_dict(self, get_stack_descriptions_mock):
        get_stack_descriptions_mock.return_value = [{"StackName": "Foo", "Parameters": [], "Outputs": []}]
        self.assertEqual({'Foo': {'outputs': [], 'parameters': []}}, CloudFormation().get_stacks_dict())

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack_descriptions')
    def test_get_stacks_dict_always_returns_empty_list_parameters_and_outputs(self, get_stack_descriptions_mock):
        get_stack_descriptions_mock.return_value = [{"StackName": "Foo"}]
        self.assertEqual({'Foo': {'outputs': [], 'parameters': []}}, CloudFormation().get_stacks_dict())

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_handle_stack_event_returns_expected_event(self, _):
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

        result = cfn.handle_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertDictEqual(event, result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_handle_stack_event_returns_none_if_event_appears_to_early(self, _):
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

        result = cfn.handle_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_handle_stack_event_returns_none_if_event_has_not_expected_state(self, _):
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

        result = cfn.handle_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_handle_stack_event_returns_none_if_event_is_no_stack_event(self, _):
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

        result = cfn.handle_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_handle_stack_event_raises_exception_on_error_event(self, _):
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
            cfn.handle_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_handle_stack_event_returns_none_on_rollback_in_progress_state(self, _):
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

        result = cfn.handle_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")
        self.assertIsNone(result)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_handle_stack_event_raises_exception_on_rollback_complete(self, _):
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
            cfn.handle_stack_event(event, valid_from_timestamp, "CREATE_COMPLETE")

    @patch('cfn_sphere.aws.cfn.boto3.client')
    @patch('cfn_sphere.aws.cfn.CloudFormation.wait_for_stack_action_to_complete')
    def test_create_stack_calls_cloudformation_api_properly(self, _, cloudformation_mock):
        stack = Mock(spec=CloudFormationStack)
        stack.name = "stack-name"
        stack.get_parameters_list.return_value = [('a', 'b')]
        stack.get_tags_list.return_value = [('any-tag', 'any-tag-value')]
        stack.parameters = {}
        stack.template = Mock(spec=CloudFormationTemplate)
        stack.template.name = "template-name"
        stack.template.get_template_json.return_value = {'key': 'value'}
        stack.timeout = 42

        cfn = CloudFormation()
        cfn.create_stack(stack)

        cloudformation_mock.return_value.create_stack.assert_called_once_with(
            Capabilities=['CAPABILITY_IAM'],
            OnFailure='DELETE',
            Parameters=[('a', 'b')],
            StackName='stack-name',
            Tags=[('any-tag', 'any-tag-value')],
            TemplateBody={'key': 'value'},
            TimeoutInMinutes=42)

    @patch('cfn_sphere.aws.cfn.boto3.client')
    @patch('cfn_sphere.aws.cfn.CloudFormation.wait_for_stack_action_to_complete')
    def test_update_stack_calls_cloudformation_api_properly(self, _, cloudformation_mock):
        stack = Mock(spec=CloudFormationStack)
        stack.name = "stack-name"
        stack.get_parameters_list.return_value = [('a', 'b')]
        stack.get_tags_list.return_value = [('any-tag', 'any-tag-value')]
        stack.parameters = {}
        stack.template = Mock(spec=CloudFormationTemplate)
        stack.template.name = "template-name"
        stack.template.get_template_json.return_value = {'key': 'value'}
        stack.timeout = 42

        cfn = CloudFormation()
        cfn.update_stack(stack)

        cloudformation_mock.return_value.update_stack.assert_called_once_with(
            Capabilities=['CAPABILITY_IAM'],
            Parameters=[('a', 'b')],
            StackName='stack-name',
            Tags=[('any-tag', 'any-tag-value')],
            TemplateBody={'key': 'value'})

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_raises_exception_on_unknown_stack_state(self, get_stack_mock):
        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "FOO"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnStackActionFailedException):
            cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_raises_exception_on_update_in_progress(self, get_stack_mock):
        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "UPDATE_IN_PROGRESS"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnStackActionFailedException):
            cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_raises_exception_on_delete_in_progress(self, get_stack_mock):
        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "DELETE_IN_PROGRESS"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnStackActionFailedException):
            cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_raises_exception_on_create_in_progress(self, get_stack_mock):
        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "CREATE_IN_PROGRESS"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnStackActionFailedException):
            cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_raises_proper_exception_on_boto_error(self, get_stack_mock):
        get_stack_mock.side_effect = CfnSphereBotoError(None)

        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "UPDATE_COMPLETE"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        with self.assertRaises(CfnSphereBotoError):
            cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_passes_if_stack_is_in_update_complete_state(self, get_stack_mock):
        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "UPDATE_COMPLETE"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_passes_if_stack_is_in_create_complete_state(self, get_stack_mock):
        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "CREATE_COMPLETE"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    def test_validate_stack_is_ready_for_action_passes_if_stack_is_in_rollback_complete_state(self, get_stack_mock):
        stack_mock = Mock()
        stack_mock.stack_name = "my-stack"
        stack_mock.stack_status = "ROLLBACK_COMPLETE"
        get_stack_mock.return_value = stack_mock

        stack = CloudFormationStack('', [], 'my-stack', 'my-region')

        cfn = CloudFormation()
        cfn.validate_stack_is_ready_for_action(stack)

    @patch('cfn_sphere.aws.cfn.CloudFormation.get_stack')
    @patch('cfn_sphere.aws.cfn.boto3.client')
    def test_get_stack_parameters_dict_returns_proper_dict(self, _, get_stack_mock):
        cfn = CloudFormation()

        stack_mock = Mock()
        stack_mock.parameters = [{"ParameterKey": "myKey1", "ParameterValue": "myValue1"},
                                 {"ParameterKey": "myKey2", "ParameterValue": "myValue2"}]
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
        exception = Mock(spec=ClientError)
        exception.response = {"Error": {"Message": "Something went wrong"}}
        self.assertFalse(CloudFormation.is_boto_no_update_required_exception(exception))

    def test_is_boto_no_update_required_exception_returns_true_for_message(self):
        exception = Mock(spec=ClientError)
        exception.response = {"Error": {"Message": "No updates are to be performed."}}
        self.assertTrue(CloudFormation.is_boto_no_update_required_exception(exception))
