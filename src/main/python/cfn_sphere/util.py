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
        convert = convert_json_to_yaml_string
    elif file_path.lower().endswith('.yml'):
        convert = convert_yaml_to_json_string
    elif file_path.lower().endswith('.yaml'):
        convert = convert_yaml_to_json_string
    else:
        raise Exception('Unknown file extension. Please use .yaml, .yml or .json!')

    with open(file_path, 'r') as filestream:
        return convert(filestream.read())


def convert_json_to_yaml_string(data):
    if not data:
        return ''
    return yaml.safe_dump(json.loads(data), default_flow_style=False)


def convert_yaml_to_json_string(data):
    if not data:
        return '{}'
    return json.dumps(yaml.load(data), indent=2)

def convert_dict_to_json_string(data):
    return json.dumps(data, indent=2)

def get_message_from_boto_server_error(boto_server_error):
    return boto_server_error.message