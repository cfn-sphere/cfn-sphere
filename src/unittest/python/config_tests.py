import unittest2
from cfn_sphere.config import Config, StackConfig, NoConfigException


class ConfigTests(unittest2.TestCase):
    def test_region_property_is_parsed_correctly(self):
        config = Config(config_dict={'region': 'eu-west-1'})
        self.assertEqual('eu-west-1', config.region)

    def test_raises_exception_if_no_region_key(self):
        with self.assertRaises(NoConfigException):
            config = Config(config_dict={'foo':''})
            config.region
