import unittest2
from mock import patch, Mock
import yaml
from textwrap import dedent
from cfn_sphere.custom_resources import CustomResourceHandler
from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.cloudformation.stack import CloudFormationStack
from cfn_sphere.cloudformation.template import CloudFormationTemplate


class CustomResourceHandlerTests(unittest2.TestCase):
    @patch('cfn_sphere.custom_resources.CustomResourceHandler.handle_sns_subscription')
    def test_process_post_resources(self, handle_sns_subscriptions_mock):
        custom_resource_yaml = dedent("""
        PostCustomResources:
            exposeTopicSubscription:
                Type: "Custom::SNS::Subscription"
                Properties:
                    TopicArn:
                      Ref: exposeTopicArn
                    QueueResourceName: exposeQueue
        """)

        custom_resource_dict = yaml.load(custom_resource_yaml)
        template = CloudFormationTemplate(custom_resource_dict, 'foo')
        stack = CloudFormationStack(template, {}, 'foo', 'foo-region')

        CustomResourceHandler.process_post_resources(stack)
        handle_sns_subscriptions_mock.assert_called_once_with({'Type': 'Custom::SNS::Subscription',
                                                               'Properties': {'TopicArn': {'Ref': 'exposeTopicArn'},
                                                                              'QueueResourceName': 'exposeQueue'}},
                                                              stack)

    def test_extract_topic_arn_by_parameter_value(self):
        resource_description = {'Type': 'Custom::SNS::Subscription',
                                'Properties': {'TopicArn': 'my-super-duper-arn',
                                               'QueueArn': {'Ref': 'exposeQueue'}}}

        result = CustomResourceHandler.extract_topic_arn(resource_description, {})
        self.assertEqual('my-super-duper-arn', result)

    def test_extract_topic_arn_by_parameter_reference(self):
        parameters = [('exposeTopicArn', 'my-super-duper-arn')]
        resource_description = {'Type': 'Custom::SNS::Subscription',
                                'Properties': {'TopicArn': {'Ref': 'exposeTopicArn'},
                                               'QueueArn': {'Ref': 'exposeQueue'}}}

        result = CustomResourceHandler.extract_topic_arn(resource_description, parameters)
        self.assertEqual('my-super-duper-arn', result)

    def test_extract_topic_arn_by_parameter_reference_raises_exception_on_invalid_reference(self):
        parameters = [('exposeTopicArn', 'my-super-duper-arn')]
        resource_description = {'Type': 'Custom::SNS::Subscription',
                                'Properties': {'TopicArn': {'Ref': 'exposeTopicArnWithTypo'},
                                               'QueueArn': {'Ref': 'exposeQueue'}}}

        with self.assertRaises(CfnSphereException):
            CustomResourceHandler.extract_topic_arn(resource_description, parameters)
