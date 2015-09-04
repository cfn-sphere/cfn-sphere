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
        self.assertEqual(('Fn::Join', ['-', ['a', 'b']]), result)

    def test_transform_join_key_accepts_empty_join_string(self):
        result = CloudFormationTemplateTransformer.transform_join_key('|join|', ['a', 'b'])
        self.assertEqual(('Fn::Join', ['', ['a', 'b']]), result)

    def test_transform_join_key_creates_valid_cfn_join_with_multiple_strings(self):
        result = CloudFormationTemplateTransformer.transform_join_key('|join|-', ['a', 'b', 'c', 'd', 'e'])
        self.assertEqual(('Fn::Join', ['-', ['a', 'b', 'c', 'd', 'e']]), result)

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
        self.assertDictEqual(expected, value)

    def test_transform_taupage_user_data_accepts_int_key_value(self):
        input = {'ports': {8080: 9000}}

        key, value = CloudFormationTemplateTransformer.transform_taupage_user_data_key('@taupageUserData@', input)
        expected = {
            "Fn::Base64": {
                "Fn::Join":
                    [
                        "\n",
                        [
                            "#taupage-ami-config",
                            "ports:",
                            {"Fn::Join": [": ", ["  8080", 9000]]}
                        ]
                    ]
            }
        }

        self.assertDictEqual(expected, value)

    def test_transform_taupage_user_data_accepts_joins(self):
        input = {
            "source": {"Fn::Join": [":", ["my-registry/my-app", {"Ref": "appVersion"}]]}
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
                                    "source",
                                    {
                                        "Fn::Join": [
                                            ":",
                                            [
                                                "my-registry/my-app",
                                                {
                                                    "Ref": "appVersion"
                                                }
                                            ]
                                        ]
                                    }
                                ]
                            ]
                        }
                    ]
                ]
            }
        }

        key, value = CloudFormationTemplateTransformer.transform_taupage_user_data_key('@taupageUserData@', input)
        import json
        print json.dumps(value, indent=4, sort_keys=True)
        self.assertDictEqual(expected, value)

    def test_transform_kv_to_cfn_join_accepts_int_key_value(self):
        result = CloudFormationTemplateTransformer.transform_kv_to_cfn_join(8080, 9000)
        expected = {'Fn::Join': [': ', [8080, 9000]]}

        self.assertEqual(expected, result)

    def test_transform_template_properly_renders_dict(self):
        template_dict = {
            'key1': '|ref|value',
            'key2': '|getatt|resource|attribute',
            '@TaupageUserData@':
                {
                    'key1': 'value',
                    'key2': {'ref': 'value'},
                    'key3': {'|join|.': ['a', 'b', 'c']}
                }
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {
            "key1": {
                "Ref": "value"
            },
            "key2": {
                "Fn::GetAtt": [
                    "resource",
                    "attribute"
                ]
            },
            "UserData": {
                "Fn::Base64": {
                    "Fn::Join": [
                        "\n",
                        [
                            "#taupage-ami-config",
                            {
                                "Fn::Join": [
                                    ": ",
                                    [
                                        "key1",
                                        "value"
                                    ]
                                ]
                            },
                            {
                                "Fn::Join": [
                                    ": ",
                                    [
                                        "key2",
                                        {
                                            "ref": "value"
                                        }
                                    ]
                                ]
                            },
                            {
                                "Fn::Join": [
                                    ": ",
                                    [
                                        "key3",
                                        {
                                            "Fn::Join": [
                                                ".",
                                                [
                                                    "a",
                                                    "b",
                                                    "c"
                                                ]
                                            ]
                                        }
                                    ]
                                ]
                            }
                        ]
                    ]
                }
            }
        }

        self.assertEqual(expected, result.body_dict)

    def test_transform_template_transforms_list_values(self):
        template_dict = {
            'key1': ["|ref|foo", "a", "b"]
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key1': [{'Ref': 'foo'}, 'a', 'b']}

        self.assertEqual(expected, result.body_dict)

    def test_transform_template_transforms_dict_list_items(self):
        template_dict = {
            'key1': {'key2': [{'key3': 'value3', 'foo': {'|Join|': ['a', 'b']}}]}
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key1': {'key2': [{'foo': {'Fn::Join': ['', ['a', 'b']]}, 'key3': 'value3'}]}}

        self.assertEqual(expected, result.body_dict)

    def test_transform_template_transforms_join_with_embedded_ref(self):
        template_dict = {
            'key1': {"|join|.": ["|ref|foo", "b"]}
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key1': {'Fn::Join': ['.', [{'Ref': 'foo'}, 'b']]}}

        self.assertEqual(expected, result.body_dict)
