import os
from six import string_types
from collections import defaultdict

from cfn_sphere.file_loader import FileLoader
from cfn_sphere.exceptions import InvalidConfigException, CfnSphereException
from cfn_sphere.util import get_logger
from cfn_sphere.stack_configuration.dependency_resolver import DependencyResolver

ALLOWED_CONFIG_KEYS = ["region", "stacks", "service-role", "stack-policy-url", "timeout", "tags", "on_failure",
                       "disable_rollback"]


class Config(object):
    def __init__(self, config_file=None, config_dict=None, cli_params=None, cli_tags=None, stack_name_suffix=None):
        self.logger = get_logger()

        if isinstance(config_dict, dict):
            self.stack_config_base_dir = None
        elif config_file:
            self.stack_config_base_dir = os.path.dirname(os.path.realpath(config_file))
            config_dict = FileLoader.get_yaml_or_json_file(config_file, working_dir=os.getcwd())
        else:
            raise InvalidConfigException(
                "You need to pass either config_file (path to a file) or config_dict (python dict) property")

        self._validate(config_dict)

        cli_parameters = self._parse_cli_parameters(cli_params)
        self.cli_params = self._apply_stack_name_suffix_to_cli_parameters(cli_parameters, stack_name_suffix)

        self.cli_tags = self._parse_cli_tags(cli_tags)

        self.region = config_dict.get("region")
        self.stack_name_suffix = stack_name_suffix

        self.default_service_role = config_dict.get("service-role")
        self.default_stack_policy_url = config_dict.get("stack-policy-url")
        self.default_timeout = config_dict.get("timeout", 600)
        self.default_tags = config_dict.get("tags", {})
        self.default_tags.update(self.cli_tags)
        self.default_failure_action = config_dict.get("on_failure", "ROLLBACK")
        self.default_disable_rollback = config_dict.get("disable_rollback", False)
        self.default_termination_protection = config_dict.get("termination_protection", False)

        stacks = self._parse_stack_configs(config_dict)
        self.stacks = self._apply_stack_name_suffix_to_stacks(stacks, stack_name_suffix)

        self._validate_cli_params(self.cli_params, self.stacks)

    @staticmethod
    def _validate(config_dict):
        try:
            for key in config_dict.keys():
                assert str(key).lower() in ALLOWED_CONFIG_KEYS, \
                    "Invalid syntax, {0} is not allowed as top level config key".format(key)

            region = config_dict.get("region")
            assert region, "Please specify region in config file"
            assert isinstance(region, string_types), "Region must be a string, not {0}".format(type(region))

            stacks = config_dict.get("stacks")
            assert stacks, "Please specify stacks in config file"
            assert isinstance(stacks, dict), "Stacks must be of type dict, not {0}".format(type(stacks))

            service_role = config_dict.get("service-role")
            if service_role:
                assert isinstance(service_role, string_types), "service-role must be of type str, not {0}".format(type(service_role))
                assert service_role.startswith("arn:aws:iam"), "service role must be an AWS ARN like arn:aws:iam::123456789:role/my-role"

        except AssertionError as e:
            raise InvalidConfigException(e)

    @staticmethod
    def _validate_cli_params(cli_params, stacks):
        try:
            for cli_param_stack_name in cli_params.keys():
                assert cli_param_stack_name in stacks.keys(), \
                    "Stack '{0}' referenced in cli parameter does not exist in config".format(cli_param_stack_name)
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
                    and self.default_disable_rollback == other.default_disable_rollback
                    and self.default_termination_protection == other.default_termination_protection
                    and stacks_equal):
                return True
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self == other

    @staticmethod
    def _parse_cli_tags(cli_tags):
        tags = {}
        if not cli_tags:
            return tags
        pairs = cli_tags.split(" ")
        for pair in pairs:
            k, p, v = pair.partition("=")
            if p != '=':
                raise CfnSphereException("Invalid cli tag detected: " + pair)
            tags[k] = v
        return tags

        

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
                                               working_dir=self.stack_config_base_dir,
                                               default_tags=self.default_tags,
                                               default_timeout=self.default_timeout,
                                               default_service_role=self.default_service_role,
                                               default_stack_policy_url=self.default_stack_policy_url,
                                               default_failure_action=self.default_failure_action,
                                               default_disable_rollback=self.default_disable_rollback,
                                               default_termination_protection=self.default_termination_protection)

            except InvalidConfigException as e:
                raise InvalidConfigException("Invalid config for stack {0}: {1}".format(key, e))

        return stacks_dict

    @classmethod
    def _apply_stack_name_suffix_to_cli_parameters(cls, cli_parameters, suffix):
        if not suffix:
            return cli_parameters

        result = {}
        for stack_name, parameter in cli_parameters.items():
            result[stack_name + suffix] = parameter

        return result

    @classmethod
    def _apply_stack_name_suffix_to_stacks(cls, stacks, suffix):
        """
        Apply a stack name suffix to a given set of stacks
        :param stacks: dict(stack_name -> stack_config)
        :param suffix: str
        :return dict(stack_name -> stack_config)
        """
        if not suffix:
            return stacks

        new_stacks = {}
        managed_stack_names = stacks.keys()

        for original_stack_name, stack_config in stacks.items():
            parameters = stack_config.parameters

            for key, value in parameters.items():
                list_value = []
                if isinstance(value, list):
                    for item in value:
                        list_value.append(cls._transform_value(item, suffix, managed_stack_names))

                    parameters[key] = list_value
                else:
                    parameters[key] = cls._transform_value(value, suffix, managed_stack_names)

            new_stack_name = "{0}{1}".format(original_stack_name, suffix)
            stack_config.parameters = parameters

            new_stacks[new_stack_name] = stack_config

        return new_stacks

    @staticmethod
    def _transform_value(value, suffix, managed_stack_names):
        result = value

        if DependencyResolver.is_parameter_reference(value):
            stack_name, output_name = DependencyResolver.parse_stack_reference_value(value)
            if stack_name in managed_stack_names:
                result = "|ref|{0}{1}.{2}".format(stack_name, suffix, output_name)

        return result

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


class StackConfig(object):
    STACK_CONFIG_ALLOWED_CONFIG_KEYS = ALLOWED_CONFIG_KEYS + ["parameters", "template-url"]

    def __init__(self, stack_config_dict, working_dir=None, default_tags=None, default_timeout=600,
                 default_service_role=None, default_stack_policy_url=None, default_failure_action="ROLLBACK",
                 default_disable_rollback=False, default_termination_protection=False):

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
        self.termination_protection = stack_config_dict.get("termination_protection", default_termination_protection)

        self.working_dir = working_dir
        self._stack_config_dict = stack_config_dict

        self._validate()

    def _validate(self):
        try:
            for key in self._stack_config_dict.keys():
                assert str(key).lower() in self.STACK_CONFIG_ALLOWED_CONFIG_KEYS, \
                    "Invalid syntax, {0} is not allowed as stack config key".format(key)

            assert self.template_url, "Stack config needs a template-url key"
            assert isinstance(self.template_url, string_types), \
                "template-url must be of type str, not {0}".format(type(self.template_url))

            assert isinstance(self.timeout, int), "timeout must be of type dict, not {0}".format(type(self.timeout))

            if self.service_role:
                assert isinstance(self.service_role, string_types), \
                    "service-role must be of type str, not {0}".format(type(self.template_url))
                assert str(self.service_role).lower().startswith("arn:aws:iam:"), \
                    "service-role must start with 'arn:aws:iam:'"

            if self.stack_policy_url:
                assert isinstance(self.stack_policy_url, string_types), \
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
