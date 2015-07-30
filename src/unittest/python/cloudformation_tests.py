__author__ = 'mhoyer'

import datetime
import unittest2
from datetime import timedelta
from boto.cloudformation.stack import StackEvent
from cfn_sphere.connector.cloudformation import CloudFormation, CloudFormationTemplate, NoTemplateFoundException
from mock import patch, Mock


class CloudFormationTemplateTests(unittest2.TestCase):
    def setUp(self):
        self.cfn_template = CloudFormationTemplate("", template_body={"bla": "foo"})

    @patch("cfn_sphere.connector.cloudformation.CloudFormationTemplate._fs_get_template")
    def test_load_template_calls_fs_get_template_for_fs_url(self, mock):
        URL = "/tmp/template.json"

        self.cfn_template._load_template(URL)
        mock.assert_called_with(URL)

    @patch("cfn_sphere.connector.cloudformation.CloudFormationTemplate._s3_get_template")
    def test_load_template_calls_s3_get_template_for_s3_url(self, mock):
        URL = "s3://my-bucket.amazon.com/foo.json"

        self.cfn_template._load_template(URL)
        mock.assert_called_with(URL)

    def test_load_template_raises_exception_on_unknown_protocol(self):
        URL = "xxx://foo.json"
        with self.assertRaises(NoTemplateFoundException):
            self.cfn_template._load_template(URL)

class CloudFormationTests(unittest2.TestCase):

    @patch('cfn_sphere.connector.cloudformation.cloudformation')
    def test_wait_for_stack_event_returns_on_start_event_with_valid_timestamp(self, cloudformation_mock):
        timestamp = datetime.datetime.utcnow()

        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "UPDATE_IN_PROGRESS"
        event.event_id = "123"
        event.timestamp = timestamp

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        event = cfn.wait_for_stack_events("foo", ["UPDATE_IN_PROGRESS"],
                                          datetime.datetime.utcnow() - timedelta(seconds=10),
                                          timeout=10)

        self.assertEqual(timestamp, event.timestamp)

    @patch('cfn_sphere.connector.cloudformation.cloudformation')
    def test_wait_for_stack_event_returns_on_update_complete(self, cloudformation_mock):
        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "UPDATE_COMPLETE"
        event.event_id = "123"
        event.timestamp = datetime.datetime.utcnow()

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        cfn.wait_for_stack_events("foo", ["UPDATE_COMPLETE"], datetime.datetime.utcnow() - timedelta(seconds=10),
                                  timeout=10)

    @patch('cfn_sphere.connector.cloudformation.cloudformation')
    def test_wait_for_stack_event_raises_exception_on_rollback(self, cloudformation_mock):
        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "ROLLBACK_IN_PROGRESS"
        event.event_id = "123"
        event.timestamp = datetime.datetime.utcnow()

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        with self.assertRaises(Exception):
            cfn.wait_for_stack_events("foo", ["UPDATE_COMPLETE"], datetime.datetime.utcnow() - timedelta(seconds=10),
                                      timeout=10)

    @patch('cfn_sphere.connector.cloudformation.cloudformation')
    def test_wait_for_stack_event_raises_exception_on_update_failure(self, cloudformation_mock):
        template_mock = Mock(spec=CloudFormationTemplate)
        template_mock.url = "foo.yml"
        template_mock.get_template_body.return_value = {}

        event = StackEvent()
        event.resource_type = "AWS::CloudFormation::Stack"
        event.resource_status = "UPDATE_FAILED"
        event.event_id = "123"
        event.timestamp = datetime.datetime.utcnow()

        stack_events_mock = Mock()
        stack_events_mock.describe_stack_events.return_value = [event]

        cloudformation_mock.connect_to_region.return_value = stack_events_mock

        cfn = CloudFormation()
        with self.assertRaises(Exception):
            cfn.wait_for_stack_events("foo", ["UPDATE_COMPLETE"], datetime.datetime.utcnow() - timedelta(seconds=10),
                                      timeout=10)