# Modifications copyright (C) 2017 KCOM
import os
from collections import defaultdict

import yaml
from yaml.scanner import ScannerError

from cfn_sphere.exceptions import InvalidConfigException, CfnSphereException
from cfn_sphere.util import get_logger

ALLOWED_CONFIG_KEYS = ["region", "stacks", "service-role", "stack-policy-url", "timeout", "tags", "on_failure",
                       "disable_rollback", "change_set"]


class Config(object):
    def __init__(self, config_file=None, config_dict=None, cli_params=None):
        self.logger = get_logger()

        if isinstance(config_dict, dict):
            self.working_dir = None
        elif config_file:
            config_dict = self._read_config_file(config_file)
            self.working_dir = os.path.dirname(os.path.realpath(config_file))
        else:
            raise InvalidConfigException("No config_file or valid config_dict provided")

        self.cli_params = self._parse_cli_parameters(cli_params)
        self.region = config_dict.get("region")

        self.change_set = config_dict.get("change_set")
        self.default_service_role = config_dict.get("service-role")
        self.default_stack_policy_url = config_dict.get("stack-policy-url")
        self.default_timeout = config_dict.get("timeout", 600)
        self.default_tags = config_dict.get("tags", {})
        self.default_failure_action = config_dict.get("on_failure", "ROLLBACK")
        self.default_disable_rollback = config_dict.get("disable_rollback", False)

        self.stacks = self._parse_stack_configs(config_dict)
        self._config_dict = config_dict

        self._validate()

    def _validate(self):
        try:
            for key in self._config_dict.keys():
                assert str(key).lower() in ALLOWED_CONFIG_KEYS, \
                    "Invalid syntax, {0} is not allowed as top level config key".format(key)

            assert self.region, "Please specify region in config file"
            assert isinstance(self.region, str), "Region must be of type str, not {0}".format(type(self.region))

            # stacks config file not required when executing a change set
            if self.change_set is None:
                assert self.stacks, "Please specify stacks in config file"
                assert isinstance(self.stacks, dict), "stacks must be of type dict, not {0}".format(type(self.stacks))

            for cli_stack in self.cli_params.keys():
                assert cli_stack in self.stacks.keys(), "Stack '{0}' does not exist in config".format(cli_stack)

        except AssertionError as e:
            raise InvalidConfigException(e)

    def __eq__(self, other):
        try:
            stacks_equal = self.stacks == other.stacks

            if (self.cli_params == other.cli_params
                and self.region == other.region
                and self.default_tags == other.default_tags
                and self.default_service_role == other.default_service_role
                and self.default_stack_policy_url == other.default_stack_policy_url
                and self.default_timeout == other.default_timeout
                and self.default_tags == other.default_tags
                and stacks_equal):
                return True
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self == other

    def _parse_stack_configs(self, config_dict):
        """
        Create a StackConfig Object for each stack defined in config
        :param config_dict: dict
        :return: dict(stack_name: StackConfig)
        """
        stacks_dict = {}
        for key, value in config_dict.get("stacks", {}).items():
            try:
                stacks_dict[key] = StackConfig(value,
                                               working_dir=self.working_dir,
                                               default_tags=self.default_tags,
                                               default_timeout=self.default_timeout,
                                               default_service_role=self.default_service_role,
                                               default_stack_policy_url=self.default_stack_policy_url,
                                               default_failure_action=self.default_failure_action,
                                               default_disable_rollback=self.default_disable_rollback)

            except InvalidConfigException as e:
                raise InvalidConfigException("Invalid config for stack {0}: {1}".format(key, e))

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
                    stack_and_parameter_key, parameter_value = key_value_parameter_pair.split("=", 1)
                    stack, parameter_key = stack_and_parameter_key.split(".", 1)

                    stack_parameter = {parameter_key.strip(): parameter_value.strip()}
                    param_dict[stack.strip()].update(stack_parameter)
            except (KeyError, ValueError):
                raise CfnSphereException("""Format of input parameters is faulty.
                        Use 'stack1.param=value,stack2.param=value'""")

        return param_dict

    @staticmethod
    def _read_config_file(config_file):
        try:
            with open(config_file, "r") as f:
                config_dict = yaml.safe_load(f.read())
                if not isinstance(config_dict, dict):
                    raise InvalidConfigException(
                        "Config file {0} has invalid content, top level element must be a dict".format(config_file))

                return config_dict
        except ScannerError as e:
            raise InvalidConfigException("Could not parse {0}: {1} {2}".format(config_file, e.problem, e.problem_mark))
        except Exception as e:
            raise InvalidConfigException("Could not read yaml file {0}: {1}".format(config_file, e))


class StackConfig(object):
    STACK_CONFIG_ALLOWED_CONFIG_KEYS = ALLOWED_CONFIG_KEYS + ["parameters", "template-url"]

    def __init__(self, stack_config_dict, working_dir=None, default_tags=None, default_timeout=600,
                 default_service_role=None, default_stack_policy_url=None, default_failure_action="ROLLBACK",
                 default_disable_rollback=False):

        if not stack_config_dict or not isinstance(stack_config_dict, dict):
            raise InvalidConfigException("Stack configuration must not be empty")

        if default_tags is None:
            default_tags = {}
        self.parameters = stack_config_dict.get("parameters", {})
        self.template_url = stack_config_dict.get("template-url")

        self.tags = {}
        self.tags.update(default_tags)
        self.tags.update(stack_config_dict.get("tags", {}))

        self.service_role = stack_config_dict.get("service-role", default_service_role)
        self.stack_policy_url = stack_config_dict.get("stack-policy-url", default_stack_policy_url)
        self.timeout = stack_config_dict.get("timeout", default_timeout)
        self.failure_action = stack_config_dict.get("on_failure", default_failure_action)
        self.disable_rollback = stack_config_dict.get("disable_rollback", default_disable_rollback)

        self.working_dir = working_dir
        self._stack_config_dict = stack_config_dict

        self._validate()

    def _validate(self):
        try:
            for key in self._stack_config_dict.keys():
                assert str(key).lower() in self.STACK_CONFIG_ALLOWED_CONFIG_KEYS, \
                    "Invalid syntax, {0} is not allowed as stack config key".format(key)

            assert self.template_url, "Stack config needs a template-url key"
            assert isinstance(self.template_url, str), \
                "template-url must be of type str, not {0}".format(type(self.template_url))

            assert isinstance(self.timeout, int), "timeout must be of type dict, not {0}".format(type(self.timeout))

            if self.service_role:
                assert isinstance(self.service_role, str), \
                    "service-role must be of type str, not {0}".format(type(self.template_url))
                assert str(self.service_role).lower().startswith("arn:aws:iam:"), \
                    "service-role must start with 'arn:aws:iam:'"

            if self.stack_policy_url:
                assert isinstance(self.stack_policy_url, str), \
                    "stack-policy-url must be of type str, not {0}".format(type(self.stack_policy_url))

            if self.timeout:
                assert isinstance(self.timeout, int), \
                    "timeout must be of type int, not {0}".format(type(self.timeout))

            if self.failure_action:
                assert str(self.failure_action).lower() in ['do_nothing', 'rollback', 'delete'], \
                    "on_failure property value must be one of 'DO_NOTHING'|'ROLLBACK'|'DELETE'"

            if self.disable_rollback:
                assert isinstance(self.disable_rollback, bool), "disable_rollback property value must be a boolean"

        except AssertionError as e:
            raise InvalidConfigException(e)

    def __eq__(self, other):
        try:
            if (self.parameters == other.parameters
                and self.tags == other.tags
                and self.timeout == other.timeout
                and self.working_dir == other.working_dir
                and self.service_role == other.service_role
                and self.stack_policy_url == other.stack_policy_url
                and self.template_url == other.template_url
                and self.failure_action == other.failure_action):
                return True
        except AttributeError:
            return False

        return False

    def __ne__(self, other):
        return not self == other
