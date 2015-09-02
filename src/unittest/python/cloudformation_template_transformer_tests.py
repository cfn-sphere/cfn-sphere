import unittest2
from cfn_sphere.aws.cloudformation.template_transformer import CloudFormationTemplateTransformer
from cfn_sphere.aws.cloudformation.template import CloudFormationTemplate
from cfn_sphere.exceptions import TemplateErrorException
from mock import Mock, mock


class CloudFormationTemplateTransformerTests(unittest2.TestCase):
    def test_transform_dict_values_executes_value_handler_for_all_matching_prefixes(self):
        dictionary = {'a': 'foo123', 'b': {'c': 'foo234'}}
        handler = Mock()
        handler.return_value = "foo"

        result = CloudFormationTemplateTransformer.transform_dict_values(dictionary, handler)
        expected_calls = [mock.call('foo123'), mock.call('foo234')]

        self.assertListEqual(expected_calls, handler.mock_calls)
        self.assertEqual(result, {'a': 'foo', 'b': {'c': 'foo'}})

    def test_transform_userdata_dict_to_lines_list(self):
        result = CloudFormationTemplateTransformer.transform_userdata_dict_to_lines_list({'my-key': 'my-value'})
        self.assertEqual([{'Fn::Join': [': ', ['my-key', 'my-value']]}], result)

    def test_transform_userdata_dict_to_lines_list_indents_sub_dicts(self):
        result = CloudFormationTemplateTransformer.transform_userdata_dict_to_lines_list(
            {'my-key': {'my-sub-key': 'value'}})
        self.assertEqual(['my-key:', {'Fn::Join': [': ', ['  my-sub-key', 'value']]}], result)

    def test_transform_userdata_dict_to_lines_list_accepts_integer_values(self):
        result = CloudFormationTemplateTransformer.transform_userdata_dict_to_lines_list({'my-key': 3})
        self.assertEqual([{'Fn::Join': [': ', ['my-key', 3]]}], result)

    def test_transform_join_key_creates_valid_cfn_join(self):
        result = CloudFormationTemplateTransformer.transform_join_key('|join|-', ['a', 'b'])
        self.assertEqual({'Fn::Join': ['-', ['a', 'b']]}, result)

    def test_transform_join_key_accepts_empty_join_string(self):
        result = CloudFormationTemplateTransformer.transform_join_key('|join|', ['a', 'b'])
        self.assertEqual({'Fn::Join': ['', ['a', 'b']]}, result)

    def test_transform_join_key_creates_valid_cfn_join_with_multiple_strings(self):
        result = CloudFormationTemplateTransformer.transform_join_key('|join|-', ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual({'Fn::Join': ['-', ['a', 'b', 'c', 'd', 'e']]}, result)

    def test_transform_reference_string_creates_valid_cfn_reference(self):
        result = CloudFormationTemplateTransformer.transform_reference_string('|ref|my-value')
        self.assertEqual({'Ref': 'my-value'}, result)

    def test_transform_reference_string_ignores_value_without_reference(self):
        result = CloudFormationTemplateTransformer.transform_reference_string('my-value')
        self.assertEqual('my-value', result)

    def test_transform_reference_string_raises_exception_on_empty_reference(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_reference_string('|ref|')

    def test_transform_reference_string_ignores_none_values(self):
        result = CloudFormationTemplateTransformer.transform_reference_string(None)
        self.assertEqual(None, result)

    def test_transform_reference_string_ignores_empty_strings(self):
        result = CloudFormationTemplateTransformer.transform_reference_string('')
        self.assertEqual('', result)

    def test_transform_getattr_string_creates_valid_cfn_getattr(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string('|getatt|resource|attribute')
        self.assertEqual({'Fn::GetAtt': ['resource', 'attribute']}, result)

    def test_transform_getattr_string_raises_exception_on_missing_resource(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_getattr_string('|getatt|attribute')

    def test_transform_getattr_string_ignores_none_values(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string(None)
        self.assertEqual(None, result)

    def test_transform_getattr_string_ignores_empty_strings(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string('')
        self.assertEqual('', result)

    def test_transform_template_returns_properly_rendered_dict(self):
        template_dict = {'key1': '|ref|value', 'key2': '|getatt|resource|attribute',
                         '@TaupageUserData@': {'key': 'value'}}

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key2': {'Fn::GetAtt': ['resource', 'attribute']}, 'key1': {'Ref': 'value'}, 'UserData': {
            'Fn::Base64': {'Fn::Join': ['\n', ['#taupage-ami-config', {'Fn::Join': [': ', ['key', 'value']]}]]}}}

        self.assertEqual(expected, result.body_dict)

    def test_render_taupage_user_data(self):
        input = {
            "application_id": "stackName",
            "application_version": "imageVersion",
            "environment": {
                "SSO_KEY": "mySsoKey",
                "QUEUE_URL": {"ref": "myQueueUrl"}
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
                                    "stackName"
                                ]
                            ]
                        },
                        {
                            "Fn::Join": [
                                ": ",
                                [
                                    "application_version",
                                    "imageVersion"
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
                                        "ref": "myQueueUrl"
                                    }
                                ]
                            ]
                        },
                        {
                            "Fn::Join": [
                                ": ",
                                [
                                    "  SSO_KEY",
                                    "mySsoKey"
                                ]
                            ]
                        }
                    ]
                ]
            }
        }

        key, value = CloudFormationTemplateTransformer.transform_taupage_user_data_key('@taupageUserData@', input)
        import json

        print json.dumps(value)
        self.assertDictEqual(expected, value)

        # def test_transform_template_transforms_combined_functions(self):
        #     template = CloudFormationTemplate({'my-key': '|join|.|(|ref|my-value)|domain.de'}, 'foo')
        #     result = CloudFormationTemplateTransformer.transform_template(template)
        #     print result.body_dict
        #
        #     expected = [{'Fn::Join': [': ', ['my-key', {'Fn::Join': ['.', [{'Ref': 'my-value'}, 'domain.de']]}]]}]
        #
        #     self.assertEqual(expected, result)
