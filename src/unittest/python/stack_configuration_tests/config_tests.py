import os

try:
    from unittest import TestCase
except ImportError:
    from unittest import TestCase

from mock import patch

from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.stack_configuration import Config, StackConfig, InvalidConfigException


class ConfigTests(TestCase):
    def setUp(self):
        self.stack_config_a = self.create_stack_config()
        self.stack_config_b = self.create_stack_config()

    @staticmethod
    def create_config_object():
        config_dict = {
            'region': 'region a',
            'tags': {'key_a': 'value a'},
            'stacks': {
                'stack_a': {
                    'template-url': 'template_a',
                    'parameters': 'any parameters'
                }
            }
        }

        return Config(config_dict=config_dict, cli_params=['stack_a.cli_parameter_a=cli_value_a'])

    def create_stack_config(self):
        return StackConfig({'template-url': 'any url',
                            'timeout': 1,
                            'parameters': {'any parameter': 'any value'}
                            },
                           'any dir', {'any tag': 'any value'})

    def test_config_properties_parsing(self):
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
        self.assertDictContainsSubset({'global-tag': 'global-tag-value'}, config.default_tags)
        self.assertDictContainsSubset({'any-parameter': 'any-value'}, config.stacks['any-stack'].parameters)
        self.assertEqual(99, config.stacks['any-stack'].timeout)

    def test_default_service_role_is_used_if_not_overwritten_by_stack_config(self):
        config = Config(
            config_dict={
                'region': 'eu-west-1',
                'service-role': 'arn:aws:iam::123456789:role/my-role1',
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

        self.assertEqual('arn:aws:iam::123456789:role/my-role1', config.stacks["any-stack"].service_role)

    def test_default_service_role_is_overwritten_by_stack_config(self):
        config = Config(
            config_dict={
                'region': 'eu-west-1',
                'service-role': 'arn:aws:iam::123456789:role/my-role1',
                'tags': {
                    'global-tag': 'global-tag-value'
                },
                'stacks': {
                    'any-stack': {
                        'timeout': 99,
                        'template-url': 'foo.json',
                        'service-role': 'arn:aws:iam::123456789:role/my-role2',
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

        self.assertEqual('arn:aws:iam::123456789:role/my-role2', config.stacks["any-stack"].service_role)

    def test_a_stacks_service_role_is_none_if_not_configured(self):
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
        self.assertIsNone(config.stacks["any-stack"].service_role)

    def test_a_stacks_timeout_is_set_if_not_configured(self):
        config = Config(
            config_dict={
                'region': 'eu-west-1',
                'tags': {
                    'global-tag': 'global-tag-value'
                },
                'stacks': {
                    'any-stack': {
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
        self.assertTrue(isinstance(config.stacks["any-stack"].timeout, int))

    def test_validate_raises_exception_on_invalid_service_role_value(self):
        with self.assertRaises(InvalidConfigException):
            Config._validate(config_dict={'region': 'eu-west-1',
                                          'service-role': 'my-role',
                                          'stacks': {'any-stack': {'template': 'foo.json'}}})

    def test_validate_passes_on_valid_service_role_value(self):
        Config._validate(config_dict={'region': 'eu-west-1',
                                      'service-role': 'arn:aws:iam::123456789:role/my-role',
                                      'stacks': {'any-stack': {'template': 'foo.json'}}})

    def test_validate_raises_exception_if_no_region_key(self):
        with self.assertRaises(InvalidConfigException):
            Config._validate(config_dict={'foo': '', 'stacks': {'any-stack': {'template': 'foo.json'}}})

    def test_validate_raises_exception_if_no_stacks_key(self):
        with self.assertRaises(InvalidConfigException):
            Config._validate(config_dict={'region': 'eu-west-1'})

    def test_validate_raises_exception_for_invalid_config_key(self):
        with self.assertRaises(InvalidConfigException):
            Config._validate(config_dict={'invalid-key': 'some-value', 'region': 'eu-west-1',
                                          'stacks': {'stack2': {'template-url': 'foo.json'}}})

    def test_validate_raises_exception_for_invalid_stack_config_key(self):
        with self.assertRaises(InvalidConfigException):
            Config._validate(config_dict={'invalid-key': 'some-value', 'region': 'eu-west-1',
                                          'stacks': {'stack2': {'invalid-key': 'some-value'}}})

    def test_validate_raises_exception_for_empty_stack_config(self):
        with self.assertRaises(InvalidConfigException):
            Config._validate(config_dict={'invalid-key': 'some-value', 'region': 'eu-west-1',
                                          'stacks': {'stack2': None}})

    def test_validate_raises_exception_for_cli_param_on_non_configured_stack(self):
        with self.assertRaises(InvalidConfigException):
            Config._validate_cli_params(cli_params={"stack1": {"p1": "v1"}}, stacks={"stack2": {}})

    def test_config_verifies_cli_parameters_correctly_when_suffix_is_set(self):
        result = Config(cli_params=("stack.p1=v1",),
                        config_dict={'region': 'eu-west-1', 'stacks': {'stack': {'template-url': 'foo.json'}}},
                        stack_name_suffix="-suffix")

        self.assertIsNotNone(result.stacks.get("stack-suffix"))

    def test_parse_cli_parameters(self):
        config = Config(cli_params=("stack1.p1=v1", "stack1.p2=v2"),
                        config_dict={'region': 'eu-west-1', 'stacks': {'stack1': {'template-url': 'foo.json'}}})
        self.assertTrue('p1' in config.cli_params['stack1'])
        self.assertTrue('p2' in config.cli_params['stack1'])
        self.assertTrue('v1' in config.cli_params['stack1'].values())
        self.assertTrue('v2' in config.cli_params['stack1'].values())

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

    def test_equals_Config(self):
        config_a_I = self.create_config_object()

        self.assertEqual(config_a_I, config_a_I)
        self.assertNotEqual(config_a_I, 'any string')

        config_a_II = self.create_config_object()

        self.assertEqual(config_a_I, config_a_II)

    def test_equals_Config_region(self):
        config_a_I = self.create_config_object()
        config_b_region = self.create_config_object()
        config_b_region.region = 'region b'

        self.assertNotEqual(config_a_I, config_b_region)

    def test_equals_Config_tags(self):
        config_a_I = self.create_config_object()
        config_b_tags = self.create_config_object()
        config_b_tags.default_tags = {}

        self.assertNotEqual(config_a_I, config_b_tags)

    def test_equals_Config_cli_params(self):
        config_a_I = self.create_config_object()
        config_b_cli_params = self.create_config_object()
        config_b_cli_params.cli_params = {}

        self.assertNotEqual(config_a_I, config_b_cli_params)

    def test_equals_Config_stacks(self):
        config_a_I = self.create_config_object()
        config_b_cli_stacks = self.create_config_object()
        config_b_cli_stacks.stacks = {}

        self.assertNotEqual(config_a_I, config_b_cli_stacks)

    def test_equals_StackConfig(self):
        self.stack_config_a = self.create_stack_config()

        self.assertEqual(self.stack_config_a == self.stack_config_a, True)
        self.assertNotEqual(self.stack_config_a, 'any string')

        stack_config_a_II = self.create_stack_config()

        self.assertEqual(self.stack_config_a, stack_config_a_II)

    def test_equals_StackConfig_parameters(self):
        self.stack_config_b.parameters = {}
        self.assertEqual(self.stack_config_a == self.stack_config_b, False)

    def test_equals_StackConfig_tags(self):
        self.stack_config_b.tags = {}
        self.assertEqual(self.stack_config_a == self.stack_config_b, False)

    def test_equals_StackConfig_timeout(self):
        self.stack_config_b.timeout = 999
        self.assertEqual(self.stack_config_a == self.stack_config_b, False)

    def test_equals_StackConfig_working_dir(self):
        self.stack_config_b.working_dir = ''
        self.assertEqual(self.stack_config_a == self.stack_config_b, False)

    def test_apply_stack_name_suffix_to_cli_parameters_appends_suffix_to_all_stack_names(self):
        cli_parameters = {'stack1': {'p1': 'v1', 'p2': 'v2'}, 'stack2': {'p1': 'v1'}}
        result = Config._apply_stack_name_suffix_to_cli_parameters(cli_parameters, "-test")
        stack_names = list(result.keys())
        stack_names.sort()
        self.assertEqual(stack_names, ['stack1-test', 'stack2-test'])

    def test_apply_stack_name_suffix_to_cli_parameters_does_not_append_none_suffix(self):
        cli_parameters = {'stack1': {'p1': 'v1', 'p2': 'v2'}, 'stack2': {'p1': 'v1'}}
        result = Config._apply_stack_name_suffix_to_cli_parameters(cli_parameters, None)
        stack_names = list(result.keys())
        stack_names.sort()
        self.assertEqual(stack_names, ['stack1', 'stack2'])

    def test_apply_stack_name_suffix_to_stacks_appends_suffix_to_all_stacks(self):
        stacks = {
            "stack-a": StackConfig({"template-url": "some-url", "parameters": {"a": 1, "b": "|ref|stack-b.a"}}),
            "stack-b": StackConfig({"template-url": "some-url", "parameters": {"a": 1, "b": "foo"}})
        }

        result = Config._apply_stack_name_suffix_to_stacks(stacks, "-test")

        self.assertEqual(result["stack-a-test"].parameters["a"], 1)
        self.assertEqual(result["stack-a-test"].parameters["b"], "|ref|stack-b-test.a")
        self.assertEqual(result["stack-b-test"].parameters["a"], 1)
        self.assertEqual(result["stack-b-test"].parameters["b"], "foo")

    def test_apply_stack_name_suffix_to_stacks_appends_number_suffix_to_all_stacks(self):
        stacks = {
            "stack-a": StackConfig({"template-url": "some-url", "parameters": {"a": 1, "b": "|ref|stack-b.a"}}),
            "stack-b": StackConfig({"template-url": "some-url", "parameters": {"a": 1, "b": "foo"}})
        }

        result = Config._apply_stack_name_suffix_to_stacks(stacks, 3)

        self.assertEqual(result["stack-a3"].parameters["a"], 1)
        self.assertEqual(result["stack-a3"].parameters["b"], "|ref|stack-b3.a")
        self.assertEqual(result["stack-b3"].parameters["a"], 1)
        self.assertEqual(result["stack-b3"].parameters["b"], "foo")

    def test_apply_stack_name_suffix_to_stacks_does_not_modify_externally_referenced_stacks(self):
        stacks = {
            "stack-c": StackConfig({"template-url": "some-url", "parameters": {"a": 1, "b": "|ref|external_stack.a"}})
        }

        result = Config._apply_stack_name_suffix_to_stacks(stacks, "-test")

        self.assertEqual(result["stack-c-test"].parameters["a"], 1)
        self.assertEqual(result["stack-c-test"].parameters["b"], "|ref|external_stack.a")

    def test_apply_stack_name_suffix_to_stacks_does_not_append_none_suffix(self):
        stacks = {
            "stack-d": StackConfig({"template-url": "some-url"})
        }

        result = Config._apply_stack_name_suffix_to_stacks(stacks, None)
        self.assertEqual(result, stacks)

    def test_apply_stack_name_suffix_to_stacks_applies_suffix_to_sublist_items(self):
        stacks = {
            "stack-a": StackConfig(
                {"template-url": "some-url", "parameters": {"alist": ["|ref|stack-b.a", "|ref|stack-b.b"]}}),
            "stack-b": StackConfig({"template-url": "some-url"})
        }

        result = Config._apply_stack_name_suffix_to_stacks(stacks, "-test")

        self.assertEqual(result["stack-a-test"].parameters["alist"][0], "|ref|stack-b-test.a")
        self.assertEqual(result["stack-a-test"].parameters["alist"][1], "|ref|stack-b-test.b")

    @patch("cfn_sphere.stack_configuration.os.getcwd")
    @patch("cfn_sphere.stack_configuration.FileLoader.get_yaml_or_json_file")
    def test_config_reads_config_from_file(self, get_file_mock, getcwd_mock):
        getcwd_mock.return_value = "/home/user/something"
        get_file_mock.return_value = {"region": "eu-west-1", "stacks": {
            "some-stack": {"template-url": "some-template.yml"}}}

        Config("my-stacks/stacks.yml")
        get_file_mock.assert_called_once_with("my-stacks/stacks.yml", working_dir="/home/user/something")

    def test_config_accepts_unicode_values(self):
        config_dict = {u"region": u"eu-west-1", u"stacks": {
            u"some-stack": {u"template-url": u"some-template.yml"}}}

        config = Config(config_dict=config_dict)
        self.assertEqual(config.region, "eu-west-1")

    @patch("cfn_sphere.stack_configuration.os.getcwd")
    def test_config_reads_config_from_example_yml_file(self, getcwd_mock):
        getcwd_mock.return_value = os.path.dirname(os.path.realpath(__file__))

        config = Config("../../resources/example-stack-config.yml")
        self.assertEqual(config.region, "eu-west-1")
        self.assertEqual(list(config.stacks.keys()), ["my-stack"])

    @patch("cfn_sphere.stack_configuration.os.getcwd")
    def test_config_reads_config_from_example_json_file(self, getcwd_mock):
        getcwd_mock.return_value = os.path.dirname(os.path.realpath(__file__))

        config = Config("../../resources/example-stack-config.json")
        self.assertEqual(config.region, "eu-west-1")
        self.assertEqual(list(config.stacks.keys()), ["my-stack"])
