import logging
import json
import yaml
import urllib2
import datetime
from cfn_sphere.exceptions import CfnSphereException


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


def get_pretty_parameters_string(parameter_dict):
    parameters_string = ""
    for key, value in parameter_dict.items():
        parameters_string = parameters_string + "{0} = {1}\n".format(key, value)

    return parameters_string


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


def get_cfn_api_server_time():
    url = "http://aws.amazon.com"

    try:
        header_date = urllib2.urlopen(url).info().get('Date')
        return datetime.datetime.strptime(header_date, '%a, %d %b %Y %H:%M:%S GMT')
    except Exception as e:
        raise CfnSphereException("Could not get AWS server time from {0}. Error: {1}".format(url, e))


def get_latest_version():
    try:
        package_info = get_pypi_package_description()
        return package_info["info"]["version"]
    except Exception:
        return None


def get_pypi_package_description():
    url = "https://pypi.python.org/pypi/cfn-sphere/json"

    response = urllib2.urlopen(url, timeout=2)
    return json.load(response)
