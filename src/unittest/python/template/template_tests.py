import datetime

from six import string_types

from cfn_sphere.template import CloudFormationTemplate

try:
    from unittest2 import TestCase
    from mock import Mock
except ImportError:
    from unittest import TestCase
    from mock import Mock


class CloudFormationTemplateTests(TestCase):
    def test_get_template_body_dict_returns_template_format_value_as_string_if_date_given(self):
        template_dict = {
            'AWSTemplateFormatVersion': datetime.date(2010, 9, 9)
        }

        result = CloudFormationTemplate(template_dict, "Something").get_template_body_dict()
        template_version = result["AWSTemplateFormatVersion"]
        self.assertIsInstance(template_version, string_types)
        self.assertEqual(result["AWSTemplateFormatVersion"], "2010-09-09")

    def test_get_template_body_dict_returns_default_version_if_none_given(self):
        template_dict = {}

        result = CloudFormationTemplate(template_dict, "Something").get_template_body_dict()
        template_version = result["AWSTemplateFormatVersion"]
        self.assertIsInstance(template_version, string_types)
        self.assertEqual(result["AWSTemplateFormatVersion"], "2010-09-09")

    def test_get_no_echo_parameter_keys(self):
        template_dict = {
            'Parameters': {
                "a": {"Description": "param a", "Type": "String", "NoEcho": True},
                "b": {"Description": "param a", "Type": "String"},
                "c": {"Description": "param a", "Type": "String"},
                "d": {"Description": "param a", "Type": "String", "NoEcho": "true"},
                "e": {"Description": "param a", "Type": "String", "NoEcho": "True"},
                "f": {"Description": "param a", "Type": "String", "NoEcho": None},
                "g": {"Description": "param a", "Type": "String", "noecho": True},
            }
        }

        result = CloudFormationTemplate(template_dict, "Something").get_no_echo_parameter_keys()
        self.assertEqual(sorted(result), ['a', 'd', 'e'])

    def test_get_no_echo_parameter_keys_for_empty_parameters(self):
        template_dict = {}

        result = CloudFormationTemplate(template_dict, "Something").get_no_echo_parameter_keys()
        self.assertEqual(result, [])
