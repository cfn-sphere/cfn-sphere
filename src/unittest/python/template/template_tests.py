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
