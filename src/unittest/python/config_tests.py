import unittest2
from cfn_sphere.config import Config, StackConfig, NoConfigException, BadConfigException


class ConfigTests(unittest2.TestCase):
    def test_properties_parsing_config_dict(self):
        config = Config(config_dict={'region': 'eu-west-1', 'stacks': {'foo': {'template-url': 'foo.json'}}})
        self.assertEqual('eu-west-1', config.region)
        self.assertEqual(1, len(config.stacks.keys()))
        self.assertTrue(isinstance(config.stacks['foo'], StackConfig))
        self.assertEqual('foo.json', config.stacks['foo'].template_url)

    def test_properties_parsing_cli_params(self):
        config = Config(cli_params="p1=v1,p2=v2",
                        config_dict={'region': 'eu-west-1', 'stacks': {'foo': {'template-url': 'foo.json'}}})
        self.assertTrue('p1' in config.cli_params)
        self.assertTrue('p2' in config.cli_params)
        self.assertTrue('v1' in config.cli_params.values())
        self.assertTrue('v2' in config.cli_params.values())

    def test_properties_parsing_invalid_cli_params(self):
        with self.assertRaises(BadConfigException):
            Config(cli_params="foobar",
                   config_dict={'region': 'eu-west-1', 'stacks': {'foo': {'template-url': 'foo.json'}}})

    def test_properties_parsing_just_config_file_and_cli_params(self):
        with self.assertRaises(NoConfigException):
            Config(cli_params="p1=v1,p2=v2", config_dict={'region': 'eu-west-1'})

    def test_properties_parsing_just_cli_params(self):
        with self.assertRaises(NoConfigException):
            Config(cli_params="p1=v1,p2=v2")

    def test_raises_exception_if_no_region_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'foo': '', 'stacks': {'foo': {'template': 'foo.json'}}})

    def test_raises_exception_if_no_stacks_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'region': 'eu-west-1'})
