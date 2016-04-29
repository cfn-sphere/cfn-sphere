import os
from collections import defaultdict

import yaml
from yaml.scanner import ScannerError

from cfn_sphere.exceptions import NoConfigException, CfnSphereException


class Config(object):
    def __init__(self, config_file=None, config_dict=None, cli_params=None):

        if isinstance(config_dict, dict):
            self.working_dir = None
        elif config_file:
            config_dict = self._read_config_file(config_file)
            self.working_dir = os.path.dirname(os.path.realpath(config_file))
        else:
            raise NoConfigException("No config_file or valid config_dict provided")

        self.cli_params = self._parse_cli_parameters(cli_params)
        self.region = config_dict.get('region')
        self.tags = config_dict.get('tags', {})
        self.stacks = self._parse_stack_configs(config_dict)

        self._validate()

    def _validate(self):
        try:
            assert self.region, "Please specify region in config file"
            assert isinstance(self.region, str), "Region must be of type str, not {0}".format(type(self.region))
            assert self.stacks, "Please specify stacks in config file"
            for cli_stack in self.cli_params.keys():
                assert cli_stack in self.stacks.keys(), 'Stack "{0}" does not exist in config'.format(cli_stack)
        except AssertionError as e:
            raise NoConfigException(e)

    def _parse_stack_configs(self, config_dict):
        """
        Create a StackConfig Object for each stack defined in config
        :param config_dict: dict
        :return: dict(stack_name: StackConfig)
        """
        stacks_dict = {}
        for key, value in config_dict.get('stacks', {}).items():
            stacks_dict[key] = StackConfig(value, working_dir=self.working_dir, default_tags=self.tags)
        return stacks_dict

    @staticmethod
    def _parse_cli_parameters(parameters):
        """
        Parse clix parameter tuple
        :param parameters: tuple with n elements where n is number of cli parameters
        :return: dict of stacks with k-v parameters
        """
        param_dict = defaultdict(dict)
        if parameters:
            try:
                for key_value_parameter_pair in parameters:
                    stack_and_parameter_key, parameter_value = key_value_parameter_pair.split('=', 1)
                    stack, parameter_key = stack_and_parameter_key.split('.', 1)

                    stack_parameter = {parameter_key.strip(): parameter_value.strip()}
                    param_dict[stack.strip()].update(stack_parameter)
            except (KeyError, ValueError):
                raise CfnSphereException("""Format of input parameters is faulty.
                        Use 'stack1.param=value,stack2.param=value'""")

        return param_dict

    @staticmethod
    def _read_config_file(config_file):
        try:
            with open(config_file, 'r') as f:
                config_dict = yaml.safe_load(f.read())
                if not isinstance(config_dict, dict):
                    raise NoConfigException(
                        "Config file {0} has invalid content, top level element must be a dict".format(config_file))

                return config_dict
        except ScannerError as e:
            raise NoConfigException("Could not parse {0}: {1} {2}".format(config_file, e.problem, e.problem_mark))
        except Exception as e:
            raise NoConfigException("Could not read yaml file {0}: {1}".format(config_file, e))


class StackConfig(object):
    def __init__(self, stack_config_dict, working_dir=None, default_tags={}):
        self.parameters = stack_config_dict.get('parameters', {})
        self.tags = {}
        self.tags.update(default_tags)
        self.tags.update(stack_config_dict.get('tags', {}))
        self.timeout = stack_config_dict.get('timeout', 600)
        self.working_dir = working_dir

        try:
            self.template_url = stack_config_dict['template-url']
        except KeyError as e:
            raise NoConfigException("Stack config needs a {0} key".format(e))
