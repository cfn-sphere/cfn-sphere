import unittest2
from cfn_sphere.aws.cloudformation.template import CloudFormationTemplate
from cfn_sphere.exceptions import TemplateErrorException
from mock import Mock


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
        self.assertEqual([{'Fn::Join': [': ', ['my-key', {'Ref': 'my-value'}]]}], result)

    def test_transform_userdata_dict_ignores_values_without_keyword(self):
        result = CloudFormationTemplate.transform_userdata_dict({'my-key': 'my-value'})
        self.assertEqual([{'Fn::Join': [': ', ['my-key', 'my-value']]}], result)

    def test_transform_userdata_dict_indents_sub_dicts(self):
        result = CloudFormationTemplate.transform_userdata_dict({'my-key': {'my-sub-key': 'value'}})
        self.assertEqual(['my-key:', {'Fn::Join': [': ', ['  my-sub-key', 'value']]}], result)

    def test_transform_userdata_dict_accepts_integer_values(self):
        result = CloudFormationTemplate.transform_userdata_dict({'my-key': 3})
        self.assertEqual([{'Fn::Join': [': ', ['my-key', 3]]}], result)

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
                            "Fn::Join": [
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
                            "Fn::Join": [
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
                            "Fn::Join": [
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
                            "Fn::Join": [
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
