import unittest2

from cfn_sphere.stack_configuration import Config, StackConfig, NoConfigException


class ConfigTests(unittest2.TestCase):
    def test_properties_parsing(self):
        config = Config(config_dict={'region': 'eu-west-1', 'stacks': {'foo': {'template-url': 'foo.json'}}})
        self.assertEqual('eu-west-1', config.region)
        self.assertEqual(1, len(config.stacks.keys()))
        self.assertTrue(isinstance(config.stacks['foo'], StackConfig))
        self.assertEqual('foo.json', config.stacks['foo'].template_url)

    def test_raises_exception_if_no_region_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'foo': '', 'stacks': {'foo': {'template': 'foo.json'}}})

    def test_raises_exception_if_no_stacks_key(self):
        with self.assertRaises(NoConfigException):
            Config(config_dict={'region': 'eu-west-1'})
