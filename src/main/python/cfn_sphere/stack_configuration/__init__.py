import os
from collections import defaultdict

import yaml
from git.exc import InvalidGitRepositoryError
from git.repo.base import Repo
from yaml.scanner import ScannerError

from cfn_sphere.exceptions import InvalidConfigException, CfnSphereException
from cfn_sphere.util import get_logger


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
        self.region = config_dict.get('region')
        self.default_service_role = config_dict.get('service-role')
        self.default_stack_policy_url = config_dict.get('stack-policy-url')
        self.tags = config_dict.get('tags', {})
        self.tags = self._add_git_remote_url_tag(self.tags, self.working_dir)
        self.stacks = self._parse_stack_configs(config_dict)

        self._validate()

    def _add_git_remote_url_tag(self, tags, working_dir):
        if not working_dir:
            return tags
        return self._find_git_repo_root(tags, working_dir)

    def _find_git_repo_root(self, tags, working_dir):
        try:
            repo = Repo(working_dir)
            tags['config-git-repository'] = repo.remotes.origin.url
            self.logger.info('Stack config located in git repository, adding tag "config-git-repository": "%s"'
                             % repo.remotes.origin.url)
            return tags
        except InvalidGitRepositoryError as e:
            self.logger.debug(e, exc_info=True)
            (head, tail) = os.path.split(working_dir)
            if tail:
                return self._find_git_repo_root(tags, head)
            else:
                self.logger.info("Stack config not located in a git repository")
                return tags

    def _validate(self):
        try:
            assert self.region, "Please specify region in config file"
            assert isinstance(self.region, str), "Region must be of type str, not {0}".format(type(self.region))
            assert self.stacks, "Please specify stacks in config file"
            for cli_stack in self.cli_params.keys():
                assert cli_stack in self.stacks.keys(), 'Stack "{0}" does not exist in config'.format(cli_stack)
        except AssertionError as e:
            raise InvalidConfigException(e)

    def _parse_stack_configs(self, config_dict):
        """
        Create a StackConfig Object for each stack defined in config
        :param config_dict: dict
        :return: dict(stack_name: StackConfig)
        """
        stacks_dict = {}
        for key, value in config_dict.get('stacks', {}).items():
            stacks_dict[key] = StackConfig(value,
                                           working_dir=self.working_dir,
                                           default_tags=self.tags,
                                           default_service_role=self.default_service_role,
                                           default_stack_policy_url=self.default_stack_policy_url)
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
                    raise InvalidConfigException(
                        "Config file {0} has invalid content, top level element must be a dict".format(config_file))

                return config_dict
        except ScannerError as e:
            raise InvalidConfigException("Could not parse {0}: {1} {2}".format(config_file, e.problem, e.problem_mark))
        except Exception as e:
            raise InvalidConfigException("Could not read yaml file {0}: {1}".format(config_file, e))

    def __eq__(self, other):
        try:
            stacks_equal = self.stacks == other.stacks

            if (self.cli_params == other.cli_params
                and self.region == other.region
                and self.tags == other.tags
                and stacks_equal):
                return True
        except AttributeError:
            return False

    def __ne__(self, other):
        return not self == other


class StackConfig(object):
    def __init__(self, stack_config_dict, working_dir=None, default_tags=None, default_service_role=None,
                 default_stack_policy_url=None):
        if default_tags is None:
            default_tags = {}
        self.parameters = stack_config_dict.get('parameters', {})
        self.tags = {}
        self.tags.update(default_tags)
        self.tags.update(stack_config_dict.get('tags', {}))
        self.service_role = stack_config_dict.get('service-role', default_service_role)
        self.stack_policy_url = stack_config_dict.get('stack-policy-url', default_stack_policy_url)
        self.timeout = stack_config_dict.get('timeout', 600)
        self.working_dir = working_dir
        self.template_url = stack_config_dict.get('template-url')

        self.validate()

    def validate(self):
        try:
            assert self.template_url, "Stack config needs a template-url key"
            if self.service_role:
                assert isinstance(self.service_role, basestring)
                assert str(self.service_role).lower().startswith("arn:aws:iam:"), \
                    "service-role must start with 'arn:aws:iam:'"
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
                and self.template_url == other.template_url):
                return True
        except AttributeError:
            return False

        return False

    def __ne__(self, other):
        return not self == other
