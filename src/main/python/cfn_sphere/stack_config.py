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
                return yaml.load(config_file.read())["stacks"]
        except IOError as e:
            self.logger.error("Could not read yaml file: {0}".format(e))
            raise NoConfigException
        except KeyError as e:
            self.logger.error("Yaml file does not contain stacks as first key")
            raise NoConfigException
        except ScannerError as e:
            self.logger.error("Could not parse yaml {0}: {1}".format(e.problem_mark, e.problem))
            raise NoConfigException

    def _validate(self):
        for name, data in self.config.items():
            try:
                assert isinstance(name, str), "Stackname must be a string!"
                assert name, "Stackname must not be empty!"
                assert data["region"], "You need to specify a region for your stack to run in!"
                assert data["template"], "You need to specify a template source for your stack!"
            except AssertionError as e:
                self.logger.error(e)
                raise NoConfigException
            except KeyError as e:
                self.logger.error("You need to specify a {0} for stack {1}".format(e, name))
                raise NoConfigException

    def get(self):
        return self.config


if __name__ == "__main__":
    reader = StackConfig("resources/myapp.yml")
    print(reader.get())