__author__ = 'mhoyer'

from yaml.scanner import ScannerError
import yaml
import logging
import os


class NoConfigException(Exception):
    pass


class StackConfig(object):
    def __init__(self, path):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        self.path = path

    def get(self):
        try:
            with open(self.path, 'r') as config_file:
                return yaml.load(config_file)["stacks"]
        except IOError as e:
            self.logger.error("Could not read yaml file: {0}".format(e))
            raise NoConfigException
        except KeyError as e:
            self.logger.error("Yaml file does not contain stacks as first key")
            raise NoConfigException
        except ScannerError as e:
            self.logger.error("Could not parse yaml {0}: {1}".format(e.problem_mark, e.problem))
            raise NoConfigException


if __name__ == "__main__":
    reader = StackConfig("resources/stacks.yml")
    print reader.get()