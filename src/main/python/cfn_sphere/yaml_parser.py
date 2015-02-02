__author__ = 'mhoyer'

import yaml


class YamlReader(object):

    def read_file(self, file):
        with open(file, 'r') as f:
            return yaml.load(f)
