import unittest2

from cfn_sphere.stack_configuration import Config, StackConfig, NoConfigException


class ConfigTests(unittest2.TestCase):
    def test_properties_parsing(self):
        config = Config(config_dict={'region': 'eu-west-1', 'tags': {'global-tag': 'global-tag-value'}, 'stacks': {'any-stack': {'template-url': 'foo.json', 'tags': {'any-tag': 'any-tag-value'}, 'parameters': {'any-parameter': 'any-value'}}}})
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
