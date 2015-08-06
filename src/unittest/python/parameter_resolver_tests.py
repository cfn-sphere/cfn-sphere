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

    @patch('cfn_sphere.resolver.parameter_resolver.ParameterResolver.convert_list_to_string')
    def test_resolve_parameter_values_calls_convert_list_to_string_on_list_value(self, convert_list_to_string_mock):
        ParameterResolver().resolve_parameter_values({'foo': ['a', 'b']})
        convert_list_to_string_mock.assert_called_once_with(['a', 'b'])

    def test_resolve_parameter_values_raises_exception_on_none_value(self):
        with self.assertRaises(NotImplementedError):
            ParameterResolver().resolve_parameter_values({'foo': None})

    def test_resolve_parameter_values_returns_list_with_string_value(self):
        result = ParameterResolver().resolve_parameter_values({'foo': "baa"})
        self.assertEqual([('foo', 'baa')], result)

    def test_resolve_parameter_values_returns_str_representation_of_false(self):
        result = ParameterResolver().resolve_parameter_values({'foo': False})
        self.assertEqual([('foo', 'false')], result)

    def test_resolve_parameter_values_returns_str_representation_of_int(self):
        result = ParameterResolver().resolve_parameter_values({'foo': 5})
        self.assertEqual([('foo', '5')], result)

    def test_resolve_parameter_values_returns_str_representation_of_float(self):
        result = ParameterResolver().resolve_parameter_values({'foo': 5.555})
        self.assertEqual([('foo', '5.555')], result)