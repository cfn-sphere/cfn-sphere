from yaml.scanner import ScannerError
import yaml


class NoConfigException(Exception):
    pass


class Config(object):
    def __init__(self, config_file=None, config_dict=None):
        if config_dict:
            self.dict = config_dict
        else:
            self.dict = self._read_config_file(config_file)

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

    @staticmethod
    def _parse_stack_configs(config_dict):
        stacks_dict = {}
        for key, value in config_dict.get('stacks', {}).items():
            stacks_dict[key] = StackConfig(value)
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
    def __init__(self, stack_config_dict):
        self.parameters = stack_config_dict.get('parameters', {})
        self.template = stack_config_dict.get('template')


if __name__ == "__main__":
    reader = Config("resources/myapp.yml")
    print(reader.get())
