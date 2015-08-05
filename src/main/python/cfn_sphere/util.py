import logging
import json
import yaml


def get_logger(root=False):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                        datefmt='%d.%m.%Y %H:%M:%S')
    if root:
        return logging.getLogger('cfn_sphere')
    else:
        return logging.getLogger('cfn_sphere.{0}'.format(__name__))


def convert_file(file_path):
    if file_path.lower().endswith('.json'):
        convert = convert_json_to_yaml
    elif file_path.lower().endswith('.yml'):
        convert = convert_yaml_to_json
    elif file_path.lower().endswith('.yaml'):
        convert = convert_yaml_to_json
    else:
        raise Exception('Unknown file extension. Please use .yaml, .yml or .json!')

    with open(file_path, 'r') as filestream:
        return convert(filestream.read())


def convert_json_to_yaml(data):
    return yaml.dump(json.loads(data))


def convert_yaml_to_json(data):
    return json.dumps(yaml.load(data), indent=4, sort_keys=True)
