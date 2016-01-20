from boto.exception import BotoServerError
import unittest2
from mock import patch
from cfn_sphere.exceptions import CfnSphereException, CfnSphereBotoError
from cfn_sphere.stack_configuration.parameter_resolver import ParameterResolver


class ParameterResolverTests(unittest2.TestCase):

    def test_convert_list_to_string_returns_valid_string(self):
        list = ['a', 'b', 'c']
        self.assertEqual("a,b,c", ParameterResolver.convert_list_to_string(list))

    def test_convert_list_to_string_returns_valid_string_if_list_contains_int(self):
        list = ['a', 6, 'c']
        self.assertEqual("a,6,c", ParameterResolver.convert_list_to_string(list))

    def test_convert_list_to_string_returns_empty_list_on_empty_list(self):
        self.assertEqual("", ParameterResolver.convert_list_to_string([]))

    @patch('cfn_sphere.stack_configuration.parameter_resolver.ParameterResolver.convert_list_to_string')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_calls_convert_list_to_string_on_list_value(self, kms, ec2_api, cfn, convert_list_to_string_mock):
        ParameterResolver().resolve_parameter_values({'foo': ['a', 'b']}, 'foo')
        convert_list_to_string_mock.assert_called_once_with(['a', 'b'])

    @patch('cfn_sphere.stack_configuration.parameter_resolver.ParameterResolver.get_output_value')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_returns_ref_value(self, kms, ec2_api, cfn, get_output_value_mock):
        get_output_value_mock.return_value = 'bar'
        result = ParameterResolver().resolve_parameter_values({'foo': '|Ref|stack.output'}, 'foo')
        get_output_value_mock.assert_called_once_with('stack.output')
        self.assertEqual({'foo': 'bar'}, result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.ParameterResolver.get_output_value')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_returns_ref_list_value(self, kms, ec2_api, cfn, get_output_value_mock):
        get_output_value_mock.return_value = 'bar'
        result = ParameterResolver().resolve_parameter_values({'foo': ['|Ref|stack.output', '|Ref|stack.output']}, 'foo')
        get_output_value_mock.assert_called_with('stack.output')
        self.assertEqual({'foo': 'bar,bar'}, result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_raises_exception_on_none_value(self, kms, ec2_api, cfn):
        with self.assertRaises(NotImplementedError):
            ParameterResolver().resolve_parameter_values({'foo': None}, 'foo')

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_returns_list_with_string_value(self, kms, ec2_api, cfn):
        result = ParameterResolver().resolve_parameter_values({'foo': "baa"}, 'foo')
        self.assertEqual({'foo': 'baa'}, result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_returns_str_representation_of_false(self, kms, ec2_api, cfn):
        result = ParameterResolver().resolve_parameter_values({'foo': False}, 'foo')
        self.assertEqual({'foo': 'false'}, result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_returns_str_representation_of_int(self, kms, ec2_api, cfn):
        result = ParameterResolver().resolve_parameter_values({'foo': 5}, 'foo')
        self.assertEqual({'foo': '5'}, result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_returns_str_representation_of_float(self, kms, ec2_api, cfn):
        result = ParameterResolver().resolve_parameter_values({'foo': 5.555}, 'foo')
        self.assertEqual({'foo': '5.555'}, result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_get_latest_value_returns_stacks_actual_value(self, kms,  ec2_api, cfn_mock):
        cfn_mock.return_value.get_stack_parameters_dict.return_value = {'my-key': 'my-actual-value'}

        pr = ParameterResolver()
        result = pr.get_latest_value('my-key', '|keepOrUse|default-value', 'my-stack')

        cfn_mock.return_value.get_stack_parameters_dict.assert_called_once_with('my-stack')
        self.assertEqual('my-actual-value', result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_get_latest_value_returns_default_value(self, kms, ec2_api, cfn_mock):
        cfn_mock.return_value.get_stack_parameters_dict.return_value = {'not-my-key': 'my-actual-value'}

        pr = ParameterResolver()
        result = pr.get_latest_value('my-key', '|keepOrUse|default-value', 'my-stack')

        cfn_mock.return_value.get_stack_parameters_dict.assert_called_once_with('my-stack')
        self.assertEqual('default-value', result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_get_latest_value_returns_default_value(self, kms, ec2_api, cfn_mock):
        cfn_mock.return_value.get_stack_parameters_dict.side_effect = CfnSphereBotoError(BotoServerError("500", "foo"))

        resolver = ParameterResolver()
        with self.assertRaises(CfnSphereException):
            resolver.get_latest_value('my-key', '|keepOrUse|default-value', 'my-stack')

    def test_is_keep_value_returns_true_for_keep_keyword(self):
        result = ParameterResolver.is_keep_value('|keeporuse|')
        self.assertTrue(result)

    def test_is_keep_value_returns_true_for_uppercase_keep_keyword(self):
        result = ParameterResolver.is_keep_value('|KEEPORUSE|')
        self.assertTrue(result)

    def test_is_keep_value_returns_true_for_mixed_case_keep_keyword(self):
        result = ParameterResolver.is_keep_value('|keepOrUse|')
        self.assertTrue(result)

    def test_is_keep_value_returns_false_for_empty_value(self):
        result = ParameterResolver.is_keep_value('')
        self.assertFalse(result)

    def test_get_default_from_keep_value_returns_proper_string(self):
        result = ParameterResolver.get_default_from_keep_value('|keepOrUse|foo')
        self.assertEqual('foo', result)

    def test_get_default_from_keep_value_returns_proper_string_if_it_contains_separator(self):
        result = ParameterResolver.get_default_from_keep_value('|keepOrUse|foo|foo.de')
        self.assertEqual('foo|foo.de', result)

    def test_get_default_from_keep_value_returns_empty_string(self):
        result = ParameterResolver.get_default_from_keep_value('|keepOrUse|')
        self.assertEqual('', result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
    def test_resolve_parameter_values_returns_decrypted_value(self, kms_mock, ec2_api, cfn):
        kms_mock.return_value.decrypt.return_value = "decryptedValue"

        result = ParameterResolver().resolve_parameter_values({'foo': "|kms|encryptedValue"}, 'foo')
        self.assertEqual({'foo': 'decryptedValue'}, result)

