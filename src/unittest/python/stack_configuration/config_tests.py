try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase

from cfn_sphere.stack_configuration import Config, StackConfig, NoConfigException
from cfn_sphere.exceptions import CfnSphereException


class ConfigTests(TestCase):
    def test_properties_parsing(self):
        config = Config(
            config_dict={
                'region': 'eu-west-1',
                'tags': {
                    'global-tag': 'global-tag-value'
                },
                'stacks': {
                    'any-stack': {
                        'timeout': 99,
                        'template-url': 'foo.json',
                        'tags': {
                            'any-tag': 'any-tag-value'
                        },
                        'parameters': {
                            'any-parameter': 'any-value'
                        }
                    }
                }
            }
        )
        self.assertEqual('eu-west-1', config.region)
        self.assertEqual(1, len(config.stacks.keys()))
        self.assertTrue(isinstance(config.stacks['any-stack'], StackConfig))
        self.assertEqual('foo.json', config.stacks['any-stack'].template_url)
        self.assertDictContainsSubset({'any-tag': 'any-tag-value', 'global-tag': 'global-tag-value'},
                                      config.stacks['any-stack'].tags)
        self.assertDictContainsSubset({'global-tag': 'global-tag-value'}, config.tags)
        self.assertDictContainsSubset({'any-parameter': 'any-value'}, config.stacks['any-stack'].parameters)
        self.assertEqual(99, config.stacks['any-stack'].timeout)

    def test_raises_exception_if_no_region_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'foo': '', 'stacks': {'any-stack': {'template': 'foo.json'}}})

    def test_raises_exception_if_no_stacks_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'region': 'eu-west-1'})

    def test_properties_parsing_cli_params(self):
        config = Config(cli_params=("stack1.p1=v1", "stack1.p2=v2"),
                        config_dict={'region': 'eu-west-1', 'stacks': {'foo': {'template-url': 'foo.json'}}})
        self.assertTrue('p1' in config.cli_params['stack1'])
        self.assertTrue('p2' in config.cli_params['stack1'])
        self.assertTrue('v1' in config.cli_params['stack1'].values())
        self.assertTrue('v2' in config.cli_params['stack1'].values())

    def test_config_raises_exception_if_only_cli_params_given(self):
        with self.assertRaises(NoConfigException):
            Config(cli_params="foo")

    def test_parse_cli_parameters_throws_exception_on_invalid_syntax(self):
        with self.assertRaises(CfnSphereException):
            Config._parse_cli_parameters(("foo",))

    def test_parse_cli_parameters_parses_multiple_parameters(self):
        self.assertDictEqual({'stack1': {'p1': 'v1', 'p2': 'v2'}, 'stack2': {'p1': 'v1'}},
                             Config._parse_cli_parameters(("stack1.p1=v1", "stack1.p2=v2", "stack2.p1=v1")))

    def test_parse_cli_parameters_accepts_spaces(self):
        self.assertDictEqual({'stack1': {'p1': 'v1', 'p2': 'v2'}, 'stack2': {'p1': 'v1'}},
                             Config._parse_cli_parameters(("stack1.p1 = v1 ", "stack1.p2=v2", "stack2.p1=v1 ")))

    def test_parse_cli_parameters_parses_single_string_parameter(self):
        self.assertDictEqual({'stack1': {'p1': 'v1'}}, Config._parse_cli_parameters(("stack1.p1=v1",)))

    def test_parse_cli_parameters_parses_single_int_parameter(self):
        self.assertDictEqual({'stack1': {'p1': '2'}}, Config._parse_cli_parameters(("stack1.p1=2",)))

    def test_parse_cli_parameters_accepts_list_of_strings(self):
        self.assertDictEqual({'stack1': {'p1': 'v1,v2,v3'}},
                             Config._parse_cli_parameters(("stack1.p1=v1,v2,v3",)))

    def test_parse_cli_parameters_accepts_list_of_int(self):
        self.assertDictEqual({'stack1': {'p1': '1,2,3'}},
                             Config._parse_cli_parameters(("stack1.p1=1,2,3",)))
