
import logging
import json
import yaml


def get_logger():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                        datefmt='%d.%m.%Y %H:%M:%S',
                        level=logging.INFO)
    return logging.getLogger(__name__)


def convert_json_to_yaml(data):
    return yaml.dump(json.loads(data))


def convert_yaml_to_json(data):
    return json.dumps(yaml.parse(data))