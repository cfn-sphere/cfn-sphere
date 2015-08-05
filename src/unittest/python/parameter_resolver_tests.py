import unittest2, mock
from mock import patch, Mock

from cfn_sphere.cloudformation.api import CloudFormation
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