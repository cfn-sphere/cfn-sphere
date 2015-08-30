import json
import datetime
import unittest2
from datetime import timedelta
from boto.cloudformation.stack import StackEvent
from cfn_sphere.aws.cloudformation.cfn_api import CloudFormation
from cfn_sphere.aws.cloudformation.template import CloudFormationTemplate, CloudFormationTemplateLoader
from cfn_sphere.exceptions import TemplateErrorException
from mock import patch, Mock


class CloudFormationTemplateTests(unittest2.TestCase):

    def test_transform_dict_executes_value_handler_and_passes_correct_value(self):
        function_mock = Mock()
        function_mock.return_value = 'foo_new', 'bla_new'

        mapping = {'@foo@': function_mock}
        dict = {'a': {'b': {'@foo@': 'bla'}}}

        CloudFormationTemplate.transform_dict(dict, mapping)

        function_mock.assert_called_once_with('bla')
        self.assertEqual({'a': {'b': {'foo_new': 'bla_new'}}}, dict)

    def test_transform_dict_raises_exception_on_unknown_handler(self):
        mapping = {'@foo': Mock()}
        dict = {'a': {'b': {'@not-registered-handler': 'bla'}}}

        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplate.transform_dict(dict, mapping)

    def test_transform_userdata_dict_creates_cfn_reference(self):
        result = CloudFormationTemplate.transform_userdata_dict({'my-key': '|ref|my-value'})
        self.assertEqual([{'Fn::Join:': [': ', ['my-key', {'Ref': 'my-value'}]]}], result)

    def test_transform_userdata_dict_ignores_values_without_keyword(self):
        result = CloudFormationTemplate.transform_userdata_dict({'my-key': 'my-value'})
        self.assertEqual([{'Fn::Join:': [': ', ['my-key', 'my-value']]}], result)

    def test_transform_userdata_dict_indents_sub_dicts(self):
        result = CloudFormationTemplate.transform_userdata_dict({'my-key': {'my-sub-key': 'value'}})
        self.assertEqual(['my-key:', {'Fn::Join:': [': ', ['  my-sub-key', 'value']]}], result)

    def test_transform_userdata_dict_accepts_integer_values(self):
        result = CloudFormationTemplate.transform_userdata_dict({'my-key': 3})
        self.assertEqual([{'Fn::Join:': [': ', ['my-key', 3]]}], result)

    def test_transform_reference_string_creates_valid_cfn_reference(self):
        result = CloudFormationTemplate.transform_reference_string('|ref|my-value')
        self.assertEqual({'Ref': 'my-value'}, result)

    def test_transform_getattr_string_creates_valid_cfn_getattr(self):
        result = CloudFormationTemplate.transform_getattr_string('|getatt|resource|attribute')
        self.assertEqual({'Fn::GetAtt': ['resource','attribute' ]}, result)

    def test_render_taupage_user_data(self):
        input = {
            "application_id": "|Ref|AWS::StackName",
            "application_version": "|Ref|dockerImageVersion",
            "environment": {
                "SSO_KEY": "|Ref|mySsoKey",
                "QUEUE_URL": "|Ref|myQueueUrl"
            }
        }
        expected = {
            "Fn::Base64": {
                "Fn::Join": [
                    "\n",
                    [
                        "#taupage-ami-config",
                        {
                            "Fn::Join:": [
                                ": ",
                                [
                                    "application_id",
                                    {
                                        "Ref": "AWS::StackName"
                                    }
                                ]
                            ]
                        },
                        {
                            "Fn::Join:": [
                                ": ",
                                [
                                    "application_version",
                                    {
                                        "Ref": "dockerImageVersion"
                                    }
                                ]
                            ]
                        },
                        "environment:",
                        {
                            "Fn::Join:": [
                                ": ",
                                [
                                    "  QUEUE_URL",
                                    {
                                        "Ref": "myQueueUrl"
                                    }
                                ]
                            ]
                        },
                        {
                            "Fn::Join:": [
                                ": ",
                                [
                                    "  SSO_KEY",
                                    {
                                        "Ref": "mySsoKey"
                                    }
                                ]
                            ]
                        }
                    ]
                ]
            }
        }

        key, value = CloudFormationTemplate.render_taupage_user_data(input)
        self.assertDictEqual(expected, value)


class CloudFormationTemplateLoaderTests(unittest2.TestCase):
    @patch("cfn_sphere.aws.cloudformation.template.CloudFormationTemplateLoader._fs_get_template")
    def test_load_template_calls_fs_get_template_for_fs_url(self, mock):
        url = "/tmp/template.json"

        loader = CloudFormationTemplateLoader
        loader.get_template_dict_from_url(url)

        mock.assert_called_with(url)

    @patch("cfn_sphere.aws.cloudformation.template.CloudFormationTemplateLoader._s3_get_template")
    def test_load_template_calls_s3_get_template_for_s3_url(self, mock):
        url = "s3://my-bucket.amazon.com/foo.json"

        loader = CloudFormationTemplateLoader
        loader.get_template_dict_from_url(url)

        mock.assert_called_with(url)

    def test_load_template_raises_exception_on_unknown_protocol(self):
        url = "xxx://foo.json"

        loader = CloudFormationTemplateLoader

        with self.assertRaises(TemplateErrorException):
            loader.get_template_dict_from_url(url)


class CloudFormationApiTests(unittest2.TestCase):

    @patch('cfn_sphere.aws.cloudformation.cfn_api.cloudformation')
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

    @patch('cfn_sphere.aws.cloudformation.cfn_api.cloudformation')
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

    @patch('cfn_sphere.aws.cloudformation.cfn_api.cloudformation')
    def test_wait_for_stack_event_raises_exception_on_rollback(self, cloudformation_mock):
        timestamp = datetime.datetime.utcnow()

        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body_dict.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "ROLLBACK_IN_PROGRESS"
        event.event_id = "123"
        event.timestamp = timestamp

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        with self.assertRaises(Exception):
            cfn.wait_for_stack_events("foo", ["UPDATE_COMPLETE"], timestamp - timedelta(seconds=10),
                                      timeout=10)

    @patch('cfn_sphere.aws.cloudformation.cfn_api.cloudformation')
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
