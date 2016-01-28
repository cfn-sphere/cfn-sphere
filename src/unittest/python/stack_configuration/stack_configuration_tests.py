import unittest2

from cfn_sphere.stack_configuration import Config, StackConfig, NoConfigException
from cfn_sphere.exceptions import BadConfigException


class StackConfigurationTests(unittest2.TestCase):
    def test_properties_parsing(self):
        config = Config(
            config_dict={'region': 'eu-west-1', 'tags': {'global-tag': 'global-tag-value'},
                         'stacks': {'any-stack': {'template-url': 'foo.json', 'tags': {'any-tag': 'any-tag-value'},
                                                  'parameters': {'any-parameter': 'any-value'}}}})
        self.assertEqual('eu-west-1', config.region)
        self.assertEqual(1, len(config.stacks.keys()))
        self.assertTrue(isinstance(config.stacks['any-stack'], StackConfig))
        self.assertEqual('foo.json', config.stacks['any-stack'].template_url)
        self.assertEqual({'any-tag': 'any-tag-value'}, config.stacks['any-stack'].tags)
        self.assertEqual({'global-tag': 'global-tag-value'}, config.tags)
        self.assertEqual({'any-parameter': 'any-value'}, config.stacks['any-stack'].parameters)

    def test_raises_exception_if_no_region_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'foo': '', 'stacks': {'any-stack': {'template': 'foo.json'}}})

    def test_raises_exception_if_no_stacks_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'region': 'eu-west-1'})

    def test_properties_parsing_cli_params(self):
        config = Config(cli_params="stack1:p1=v1,stack1:p2=v2",
                        config_dict={'region': 'eu-west-1', 'stacks': {'foo': {'template-url': 'foo.json'}}})
        self.assertTrue('p1' in config.cli_params['stack1'])
        self.assertTrue('p2' in config.cli_params['stack1'])
        self.assertTrue('v1' in config.cli_params['stack1'].values())
        self.assertTrue('v2' in config.cli_params['stack1'].values())

    def test_properties_parsing_invalid_cli_params(self):
        with self.assertRaises(BadConfigException):
            Config(cli_params="foobar",
                   config_dict={'region': 'eu-west-1', 'stacks': {'foo': {'template-url': 'foo.json'}}})

    def test_properties_parsing_just_config_file_and_cli_params(self):
        with self.assertRaises(NoConfigException):
            Config(cli_params="stack1:p1=v1,stack1:p2=v2", config_dict={'region': 'eu-west-1'})

    def test_properties_parsing_just_cli_params(self):
        with self.assertRaises(NoConfigException):
            Config(cli_params="p1=v1,p2=v2")
