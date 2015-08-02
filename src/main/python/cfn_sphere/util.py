
import logging
import json
import yaml
import os


def get_logger():
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                        datefmt='%d.%m.%Y %H:%M:%S',
                        level=logging.INFO)
    return logging.getLogger(__name__)


def convert_file(file_path: str):
    if file_path.lower().endswith('.json'):
        convert = convert_json_to_yaml
    elif file_path.lower().endswith('.yml'):
        convert = convert_yaml_to_json
    elif file_path.lower().endswith('.yaml'):
        convert = convert_yaml_to_json
    else:
        raise Exception('Unknown file extension. Please use .yaml, .yml or .json!')

    with open(file_path, 'r') as file:
        return convert(file.read())

def convert_json_to_yaml(data):
    return yaml.dump(json.loads(data))


def convert_yaml_to_json(data):
    return json.dumps(yaml.load(data), indent=4, sort_keys=True)