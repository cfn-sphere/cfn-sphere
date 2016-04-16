import json
import logging
import time
from functools import wraps

from botocore.exceptions import ClientError
import yaml
from prettytable import PrettyTable
from dateutil import parser

from six.moves.urllib import request as urllib2
from cfn_sphere.exceptions import CfnSphereException


def timed(function):
    logger = logging.getLogger(__name__)

    @wraps(function)
    def wrapper(*args, **kwds):
        start = time.time()
        result = function(*args, **kwds)
        elapsed = time.time() - start
        logger.debug("{0} hat {1} Sekunden benoetigt".format(function.__name__, round(elapsed, 2)))
        return result

    return wrapper


def get_logger(root=False):
    logging.basicConfig(format='%(asctime)s %(levelname)s: %(message)s',
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


def get_pretty_parameters_string(stack):
    table = PrettyTable(["Parameter", "Value"])

    parameters = stack.parameters
    no_echo_parameter_keys = stack.template.get_no_echo_parameter_keys()

    for key, value in parameters.items():
        if key in no_echo_parameter_keys:
            table.add_row([key, "***"])
        else:
            table.add_row([key, value])

    return table.get_string(sortby="Parameter")


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


def get_cfn_api_server_time():
    url = "http://aws.amazon.com"

    try:
        header_date = urllib2.urlopen(url).info().get('Date')
        return parser.parse(header_date)
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


def with_boto_retry(max_retries=3, pause_time_multiplier=5):
    logger = get_logger()
    retry_codes = ["Throttling"]

    def decorator(function):
        @wraps(function)
        def wrapper(*args, **kwds):
            retries = 0

            while True:
                try:
                    return function(*args, **kwds)
                except ClientError as e:
                    code = e.response.get("Error", {}).get("Code")
                    if code not in retry_codes or retries >= max_retries:
                        raise e

                    sleep_time = pause_time_multiplier * (2 ** retries)
                    logger.warn(
                        "{0} failed because of {1}. Will retry in {2}s".format(function.__name__, code, sleep_time))
                    time.sleep(sleep_time)
                    retries += 1

        return wrapper

    return decorator

if __name__ == "__main__":
    print(get_cfn_api_server_time())