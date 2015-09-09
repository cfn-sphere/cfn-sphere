from cfn_sphere.exceptions import NoConfigException
from yaml.scanner import ScannerError
import yaml
import os





class Config(object):
    def __init__(self, config_file=None, config_dict=None):

        if config_dict:
            self.dict = config_dict
            self.working_dir = None
        else:
            self.dict = self._read_config_file(config_file)
            self.working_dir = os.path.dirname(os.path.realpath(config_file))

        if not isinstance(self.dict, dict):
            raise NoConfigException("Config has invalid content, must be of type dict/yaml")

        self.region = self.dict.get('region')
        self.stacks = self._parse_stack_configs(self.dict)

        self._validate()

    def _validate(self):
        try:
            assert self.region, "Please specify region in config file"
            assert isinstance(self.region, str), "Region must be of type str, not {0}".format(type(self.region))
            assert self.stacks, "Please specify stacks in config file"
        except AssertionError as e:
            raise NoConfigException(e)

    def _parse_stack_configs(self, config_dict):
        stacks_dict = {}
        for key, value in config_dict.get('stacks', {}).items():
            stacks_dict[key] = StackConfig(value, self.working_dir)
        return stacks_dict

    @staticmethod
    def _read_config_file(config_file):
        try:
            with open(config_file, 'r') as f:
                return yaml.load(f.read())
        except IOError as e:
            raise NoConfigException("Could not read yaml file: {0}".format(e))
        except ScannerError as e:
            raise NoConfigException("Could not parse yaml {0}: {1}".format(e.problem_mark, e.problem))

    def get(self):
        return self.dict


class StackConfig(object):
    def __init__(self, stack_config_dict, working_dir=None):
        self.parameters = stack_config_dict.get('parameters', {})
        self.timeout = stack_config_dict.get('timeout', 600)
        self.working_dir = working_dir

        try:
            self.template_url = stack_config_dict['template-url']
        except KeyError as e:
            raise NoConfigException("Stack config needs a {0} key".format(e))


if __name__ == "__main__":
    reader = Config("resources/myapp.yml")
    print(reader.get())
