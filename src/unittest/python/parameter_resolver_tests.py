import unittest2
from mock import patch

from cfn_sphere.resolver.parameter_resolver import ParameterResolver


class ParameterResolverTests(unittest2.TestCase):

    def test_convert_list_to_string_returns_valid_string(self):
        list = ['a', 'b', 'c']
        self.assertEqual("a,b,c", ParameterResolver.convert_list_to_string(list))

    def test_convert_list_to_string_returns_valid_string_if_list_contains_int(self):
        list = ['a', 6, 'c']
        self.assertEqual("a,6,c", ParameterResolver.convert_list_to_string(list))

    def test_convert_list_to_string_returns_empty_list_on_empty_list(self):
        self.assertEqual("", ParameterResolver.convert_list_to_string([]))

    @patch('cfn_sphere.resolver.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.resolver.parameter_resolver.ParameterResolver.convert_list_to_string')
    def test_resolve_parameter_values_calls_convert_list_to_string_on_list_value(self, convert_list_to_string_mock, _):
        ParameterResolver().resolve_parameter_values({'foo': ['a', 'b']}, 'foo')
        convert_list_to_string_mock.assert_called_once_with(['a', 'b'])

    @patch('cfn_sphere.resolver.parameter_resolver.CloudFormation')
    def test_resolve_parameter_values_raises_exception_on_none_value(self, _):
        with self.assertRaises(NotImplementedError):
            ParameterResolver().resolve_parameter_values({'foo': None}, 'foo')

    @patch('cfn_sphere.resolver.parameter_resolver.CloudFormation')
    def test_resolve_parameter_values_returns_list_with_string_value(self, _):
        result = ParameterResolver().resolve_parameter_values({'foo': "baa"}, 'foo')
        self.assertEqual({'foo': 'baa'}, result)

    @patch('cfn_sphere.resolver.parameter_resolver.CloudFormation')
    def test_resolve_parameter_values_returns_str_representation_of_false(self, _):
        result = ParameterResolver().resolve_parameter_values({'foo': False}, 'foo')
        self.assertEqual({'foo': 'false'}, result)

    @patch('cfn_sphere.resolver.parameter_resolver.CloudFormation')
    def test_resolve_parameter_values_returns_str_representation_of_int(self, _):
        result = ParameterResolver().resolve_parameter_values({'foo': 5}, 'foo')
        self.assertEqual({'foo': '5'}, result)

    @patch('cfn_sphere.resolver.parameter_resolver.CloudFormation')
    def test_resolve_parameter_values_returns_str_representation_of_float(self, _):
        result = ParameterResolver().resolve_parameter_values({'foo': 5.555}, 'foo')
        self.assertEqual({'foo': '5.555'}, result)

    def test_is_keep_value_returns_true_for_keep_keyword(self):
        result = ParameterResolver.is_keep_value('@keep@')
        self.assertTrue(result)

    def test_is_keep_value_returns_true_for_uppercase_keep_keyword(self):
        result = ParameterResolver.is_keep_value('@KEEP@')
        self.assertTrue(result)

    def test_is_keep_value_returns_true_for_mixed_case_keep_keyword(self):
        result = ParameterResolver.is_keep_value('@Keep@')
        self.assertTrue(result)

    def test_is_keep_value_returns_false_for_empty_value(self):
        result = ParameterResolver.is_keep_value('')
        self.assertFalse(result)
