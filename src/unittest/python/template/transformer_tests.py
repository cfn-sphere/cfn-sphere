try:
    from unittest2 import TestCase
    from mock import Mock, mock
except ImportError:
    from unittest import TestCase
    from unittest import mock
    from unittest.mock import Mock

from cfn_sphere.template import CloudFormationTemplate
import six

from cfn_sphere.template.transformer import CloudFormationTemplateTransformer
from cfn_sphere.exceptions import TemplateErrorException


class CloudFormationTemplateTransformerTests(TestCase):
    def test_scan_dict_keys_executes_key_handler_for_all_matching_keys(self):
        dictionary = {'key': 'value'}
        handler = Mock()
        handler.return_value = 'new-key', 'new-value'

        result = CloudFormationTemplateTransformer.scan_dict_keys(dictionary, handler)
        expected_calls = [mock.call('key', 'value')]

        six.assertCountEqual(self, expected_calls, handler.mock_calls)
        self.assertDictEqual(result, {'new-key': 'new-value'})

    def test_scan_dict_values_executes_value_handler_for_all_matching_prefixes(self):
        dictionary = {'a': 'foo123', 'b': {'c': 'foo234'}}
        handler = Mock()
        handler.return_value = "foo"

        result = CloudFormationTemplateTransformer.scan_dict_values(dictionary, handler)
        expected_calls = [mock.call('foo123'), mock.call('foo234')]
        six.assertCountEqual(self, expected_calls, handler.mock_calls)
        six.assertCountEqual(self, result, {'a': 'foo', 'b': {'c': 'foo'}})

    def test_transform_dict_to_yaml_lines_list(self):
        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list({'my-key': 'my-value'})
        self.assertEqual([{'Fn::Join': [': ', ['my-key', 'my-value']]}], result)

    def test_transform_dict_to_yaml_lines_list_indents_sub_dicts(self):
        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(
            {'my-key': {'my-sub-key': 'value'}})
        self.assertEqual(['my-key:', {'Fn::Join': [': ', ['  my-sub-key', 'value']]}], result)

    def test_transform_dict_to_yaml_lines_list_accepts_integer_values(self):
        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list({'my-key': 3})
        self.assertEqual([{'Fn::Join': [': ', ['my-key', 3]]}], result)

    def test_transform_dict_to_yaml_lines_list_accepts_list_values(self):
        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list({'my-key': ['a', 'b']})
        self.assertEqual(['my-key:', '- a', '- b'], result)

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

    def test_transform_taupage_user_data_key(self):
        input = {
            "application_id": "stackName",
            "application_version": "imageVersion",
            "environment": {
                "SSO_KEY": "mySsoKey",
                "QUEUE_URL": {"ref": "myQueueUrl"}
            }
        }
        expected = {'Fn::Base64':
            {
                'Fn::Join':
                    ['\n', ['#taupage-ami-config',
                            {'Fn::Join': [': ', ['application_id', 'stackName']]},
                            {'Fn::Join': [': ', ['application_version', 'imageVersion']]},
                            'environment:',
                            {'Fn::Join': [': ', ['  QUEUE_URL', {'ref': 'myQueueUrl'}]]},
                            {'Fn::Join': [': ', ['  SSO_KEY', 'mySsoKey']]}]
                     ]
            }
        }

        key, value = CloudFormationTemplateTransformer.transform_taupage_user_data_key('@taupageUserData@', input)
        self.assertEqual("UserData", key)
        self.assertEqual(expected, value)

    def test_transform_yaml_user_data_key(self):
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
                                    "  SSO_KEY",
                                    "mySsoKey"
                                ]
                            ]
                        },
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
                        }
                    ]
                ]
            }
        }

        key, value = CloudFormationTemplateTransformer.transform_yaml_user_data_key('@YamlUserData@', input)
        self.assertEqual("UserData", key)
        six.assertCountEqual(self, expected, value)

    def test_transform_dict_to_yaml_lines_list_accepts_multiple_sub_dicts(self):
        input = {
            "foo": {
                'baa': {'key': 'value'}
            }
        }
        expected = [
            'foo:',
            '  baa:',
            {'Fn::Join': [': ', ['    key', 'value']]}

        ]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        six.assertCountEqual(self, expected, result)

    def test_transform_dict_to_yaml_lines_list_accepts_int_key_value(self):
        input = {'ports': {8080: 9000}}

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        expected = [
            "ports:",
            {"Fn::Join": [": ", ["  8080", 9000]]}
        ]

        six.assertCountEqual(self, expected, result)

    def test_transform_dict_to_yaml_lines_list_accepts_joins(self):
        input = {
            "source": {"Fn::Join": [":", ["my-registry/my-app", {"Ref": "appVersion"}]]}
        }

        expected = [
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

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        six.assertCountEqual(self, expected, result)

    def test_transform_dict_to_yaml_lines_list_returns_stable_order(self):
        input = {'d': 'd', 'a': 'a', 'e': 'e', 'b': {'f': 'f', 'c': 'c', 'a': 'a'}, "#": "3"}

        expected = [{'Fn::Join': [': ', ['#', '3']]},
                    {'Fn::Join': [': ', ['a', 'a']]},
                    'b:',
                    {'Fn::Join': [': ', ['  a', 'a']]},
                    {'Fn::Join': [': ', ['  c', 'c']]},
                    {'Fn::Join': [': ', ['  f', 'f']]},
                    {'Fn::Join': [': ', ['d', 'd']]},
                    {'Fn::Join': [': ', ['e', 'e']]}]

        result = CloudFormationTemplateTransformer.transform_dict_to_yaml_lines_list(input)
        self.assertEqual(expected, result)

    def test_transform_kv_to_cfn_join_accepts_int_key_value(self):
        result = CloudFormationTemplateTransformer.transform_kv_to_cfn_join(8080, 9000)
        expected = {'Fn::Join': [': ', [8080, 9000]]}

        self.assertEqual(expected, result)

    def test_transform_kv_to_cfn_join_quotes_strings_with_colons(self):
        result = CloudFormationTemplateTransformer.transform_kv_to_cfn_join('f:b', 'foo:baa')
        expected = {'Fn::Join': [': ', ["'f:b'", "'foo:baa'"]]}

        self.assertEqual(expected, result)

    def test_transform_template_properly_renders_dict(self):
        template_dict = {
            'Resources': {
                'key1': '|ref|value',
                'key2': '|getatt|resource|attribute',
                '@TaupageUserData@':
                    {
                        'key1': 'value',
                        'key2': {'ref': 'value'},
                        'key3': {'|join|.': ['a', 'b', 'c']}
                    }
            }}

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
        six.assertCountEqual(self, expected, result.resources)

    def test_transform_template_transforms_references_in_conditions_section(self):
        template_dict = {
            'Conditions': {'key1': ["|ref|foo", "a", "b"], "key2": "|Ref|baa"}
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key1': [{'Ref': 'foo'}, 'a', 'b'], 'key2': {'Ref': 'baa'}}

        self.assertEqual(expected, result.conditions)

    def test_transform_template_transforms_list_values(self):
        template_dict = {
            'Resources': {'key1': ["|ref|foo", "a", "b"]}
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key1': [{'Ref': 'foo'}, 'a', 'b']}

        self.assertEqual(expected, result.resources)

    def test_transform_template_transforms_dict_list_items(self):
        template_dict = {
            'Resources': {'key1': {'key2': [{'key3': 'value3', 'foo': {'|Join|': ['a', 'b']}}]}}
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key1': {'key2': [{'foo': {'Fn::Join': ['', ['a', 'b']]}, 'key3': 'value3'}]}}

        six.assertCountEqual(self, expected, result.resources)

    def test_transform_template_transforms_join_with_embedded_ref(self):
        template_dict = {
            'Resources': {'key1': {"|join|.": ["|ref|foo", "b"]}}
        }

        result = CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))
        expected = {'key1': {'Fn::Join': ['.', [{'Ref': 'foo'}, 'b']]}}

        self.assertEqual(expected, result.resources)

    def test_transform_template_raises_exception_on_unknown_reference_value(self):
        template_dict = {
            'Resources': {'key1': "|foo|foo"}
        }

        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))

    def test_transform_template_raises_exception_on_unknown_reference_key(self):
        template_dict = {
            'Resources': {'|key|': "foo"}
        }

        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))

    def test_transform_template_raises_exception_on_unknown_at_reference_key(self):
        template_dict = {
            'Resources': {'@foo@': "foo"}
        }

        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))

    def test_transform_template_raises_exception_on_embedded_reference(self):
        template_dict = {
            'Resources': {'key1': {"foo": ["|foo|foo", "b"]}}
        }

        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_template(CloudFormationTemplate(template_dict, 'foo'))

    def test_check_for_leftover_reference_values_raises_exception_on_existing_reference(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.check_for_leftover_reference_values('|Ref|foo')

    def test_check_for_leftover_reference_values_raises_exception_on_references_in_list_values(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.check_for_leftover_reference_values(['a', '|Ref|foo', 'b'])

    def test_check_for_leftover_reference_values_properly_returns_values_without_reference(self):
        self.assertEqual('foo', CloudFormationTemplateTransformer.check_for_leftover_reference_values('foo'))

    def test_check_for_leftover_reference_values_properly_returns_empty_values(self):
        self.assertEqual('', CloudFormationTemplateTransformer.check_for_leftover_reference_values(''))

    def test_check_for_leftover_reference_keys_raises_exception_on_existing_at_reference(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.check_for_leftover_reference_keys('@Foo@', 'foo')

    def test_check_for_leftover_reference_keys_raises_exception_on_existing_pipe_reference(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.check_for_leftover_reference_keys('|foo|', 'foo')

    def test_check_for_leftover_reference_keys_properly_returns_values_without_reference(self):
        self.assertEqual(('key', 'value'),
                         CloudFormationTemplateTransformer.check_for_leftover_reference_keys('key', 'value'))

    def test_check_for_leftover_reference_keys_properly_returns_empty_values(self):
        self.assertEqual(('', ''), CloudFormationTemplateTransformer.check_for_leftover_reference_keys('', ''))
