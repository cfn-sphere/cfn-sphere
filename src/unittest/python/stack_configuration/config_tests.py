try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase

from mock import patch, Mock
from git.exc import InvalidGitRepositoryError

from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.stack_configuration import Config, StackConfig, NoConfigException


class ConfigTests(TestCase):
    def setUp(self):
        self.config_a = self.create_config_object()
        self.config_b = self.create_config_object()
        self.stack_config_a = self.create_stack_config()
        self.stack_config_b = self.create_stack_config()

    def create_config_object(self):
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
                        config_dict={'region': 'eu-west-1', 'stacks': {'stack1': {'template-url': 'foo.json'}}})
        self.assertTrue('p1' in config.cli_params['stack1'])
        self.assertTrue('p2' in config.cli_params['stack1'])
        self.assertTrue('v1' in config.cli_params['stack1'].values())
        self.assertTrue('v2' in config.cli_params['stack1'].values())

    def test_raises_exception_for_cli_param_on_non_configured_stack(self):
        with self.assertRaises(NoConfigException):
            Config(cli_params=("stack1.p1=v1",),
                   config_dict={'region': 'eu-west-1', 'stacks': {'stack2': {'template-url': 'foo.json'}}})

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

    def test_equals_Config(self):
        config_a_I = self.create_config_object()

        self.assertEquals(config_a_I, config_a_I)
        self.assertNotEquals(config_a_I, 'any string')

        config_a_II = self.create_config_object()

        self.assertEquals(config_a_I, config_a_II)

    def test_equals_Config_region(self):
        config_a_I = self.create_config_object()
        config_b_region = self.create_config_object()
        config_b_region.region = 'region b'

        self.assertNotEquals(config_a_I, config_b_region)

    def test_equals_Config_tags(self):
        config_a_I = self.create_config_object()
        config_b_tags = self.create_config_object()
        config_b_tags.tags = {}

        self.assertNotEquals(config_a_I, config_b_tags)

    def test_equals_Config_cli_params(self):
        config_a_I = self.create_config_object()
        config_b_cli_params = self.create_config_object()
        config_b_cli_params.cli_params = {}

        self.assertNotEquals(config_a_I, config_b_cli_params)

    def test_equals_Config_stacks(self):
        config_a_I = self.create_config_object()
        config_b_cli_stacks = self.create_config_object()
        config_b_cli_stacks.stacks = {}

        self.assertNotEquals(config_a_I, config_b_cli_stacks)

    def test_equals_StackConfig(self):
        self.stack_config_a = self.create_stack_config()

        self.assertEquals(self.stack_config_a == self.stack_config_a, True)
        self.assertNotEquals(self.stack_config_a, 'any string')

        stack_config_a_II = self.create_stack_config()

        self.assertEquals(self.stack_config_a, stack_config_a_II)

    def test_equals_StackConfig_parameters(self):
        self.stack_config_b.parameters = {}
        self.assertEquals(self.stack_config_a == self.stack_config_b, False)

    def test_equals_StackConfig_tags(self):
        self.stack_config_b.tags = {}
        self.assertEquals(self.stack_config_a == self.stack_config_b, False)

    def test_equals_StackConfig_timeout(self):
        self.stack_config_b.timeout = 999
        self.assertEquals(self.stack_config_a == self.stack_config_b, False)

    def test_equals_StackConfig_working_dir(self):
        self.stack_config_b.working_dir = ''
        self.assertEquals(self.stack_config_a == self.stack_config_b, False)

    @patch("cfn_sphere.stack_configuration.Repo")
    def test_add_git_remote_url_tag_without_repo(self, repo_mock):
        tags = { 'bla': 'blub' }
        repo_mock.side_effect = InvalidGitRepositoryError
        config = Config(config_dict={'region': 'eu-west-1',
                                     'tags': tags,
                                     'stacks': {'stack1': {'template-url': 'foo.json'}}})
        self.assertDictEqual(config.tags, tags)

    @patch("cfn_sphere.stack_configuration.Repo")
    def test_add_git_remote_url_tag_with_repo(self, repo_mock):
        url = "http://config.repo.git"
        repo_mock.return_value.remotes.origin.url = url
        config = Config(config_dict={'region': 'eu-west-1', 'stacks': {'stack1': {'template-url': 'foo.json'}}})
        self.assertDictEqual(config.tags, {'config-git-repository': url})
