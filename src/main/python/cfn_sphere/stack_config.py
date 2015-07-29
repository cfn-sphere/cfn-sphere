__author__ = 'mhoyer'

from yaml.scanner import ScannerError
import yaml
import logging


class NoConfigException(Exception):
    pass


class StackConfig(object):
    def __init__(self, stack_config_file):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.stack_config_file = stack_config_file
        self.config = self._read_config()
        self._validate()

    def _read_config(self):
        try:
            with open(self.stack_config_file, 'r') as config_file:
                return yaml.load(config_file.read())
        except IOError as e:
            raise NoConfigException("Could not read yaml file: {0}".format(e))
        except ScannerError as e:
            raise NoConfigException("Could not parse yaml {0}: {1}".format(e.problem_mark, e.problem))

    def _validate(self):
        try:
            assert (self.config.get('region')), "Missing required property 'region'"
            assert (self.config.get('stacks')), "Missing required property 'stacks'"

            for key, value in self.config['stacks'].items():
                assert value, "No configuration found for stack '{}'".format(key)
                assert (value.get('template')), "Missing required property 'template' in stack '{}'".format(key)
        except AssertionError as e:
            self.logger.error(e)
            raise NoConfigException

    def get(self):
        return self.config


if __name__ == "__main__":
    reader = StackConfig("resources/myapp.yml")
    print(reader.get())