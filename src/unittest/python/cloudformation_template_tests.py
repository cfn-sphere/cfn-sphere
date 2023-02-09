try:
    from unittest import TestCase
except ImportError:
    from unittest import TestCase

import six

from cfn_sphere.template import CloudFormationTemplate


class TestCloudFormationTemplateTests(TestCase):
    def test_get_template_body_dict(self):
        template_body = {
            'Description': 'some description',
            'Metadata': {
                'meta': 'value'
            },
            'Parameters': {
                'parameter': 'value'
            },
            'Mappings': {
                'mapping': 'value'
            },
            'Conditions': {
                'condition': 'value'
            },
            'Resources': {
                'resource': 'value'
            },
            'Outputs': {
                'output': 'value'
            }
        }
        template = CloudFormationTemplate(template_body, 'some name')

        self.assertEqual(template.template_format_version, '2010-09-09')
        self.assertEqual(template.description, 'some description')
        self.assertEqual(template.metadata, {'meta': 'value'})
        self.assertEqual(template.parameters, {'parameter': 'value'})
        self.assertEqual(template.mappings, {'mapping': 'value'})
        self.assertEqual(template.conditions, {'condition': 'value'})
        self.assertEqual(template.resources, {'resource': 'value'})
        self.assertEqual(template.outputs, {'output': 'value'})

    def test_get_no_echo_parameter_keys_returns_parameter_keys_with_no_echo_set(self):
        template_body = {
            'Parameters': {
                'myParameter1': {
                    'Type': 'String',
                    'NoEcho': True
                },
                'myParameter2': {
                    'Type': 'String'
                },
                'myParameter3': {
                    'Type': 'Number',
                    'NoEcho': 'true'
                },
                'myParameter4': {
                    'Type': 'Number',
                    'NoEcho': 'false'
                },
                'myParameter5': {
                    'Type': 'Number',
                    'NoEcho': False
                }
            }
        }
        template = CloudFormationTemplate(template_body, 'some name')
        six.assertCountEqual(self, ['myParameter1', 'myParameter3'], template.get_no_echo_parameter_keys())

    def test_get_no_echo_parameter_keys_returns_empty_list_without_parameters(self):
        template_body = {
            'Parameters': {}
        }
        template = CloudFormationTemplate(template_body, 'some name')
        six.assertCountEqual(self, [], template.get_no_echo_parameter_keys())

    def test_get_no_echo_parameter_keys_returns_empty_list_with_none_parameters(self):
        template_body = {
            'Parameters': None
        }
        template = CloudFormationTemplate(template_body, 'some name')
        six.assertCountEqual(self, [], template.get_no_echo_parameter_keys())
