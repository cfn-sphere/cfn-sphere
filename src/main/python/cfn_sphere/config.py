from yaml.scanner import ScannerError
import yaml
import logging


class NoConfigException(Exception):
    pass


class Config(object):
    def __init__(self, config_file=None, config_dict=None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        if config_dict:
            self.dict = config_dict
        else:
            self.dict = self._read_config_file(config_file)

        self.region = self.dict.get('region')
        self.stacks = self._parse_stack_configs(self.dict)

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
        self.parameters = stack_config_dict.get('parameters')
        self.template = stack_config_dict.get('template')


if __name__ == "__main__":
    reader = Config("resources/myapp.yml")
    print(reader.get())
