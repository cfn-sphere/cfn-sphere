import textwrap
import unittest2
from mock import patch, Mock
from datetime import datetime
from cfn_sphere import util, CloudFormationStack
from cfn_sphere.exceptions import CfnSphereException, BadConfigException
from boto.exception import BotoServerError
from cfn_sphere.template import CloudFormationTemplate


class StackConfigTests(unittest2.TestCase):
    def test_convert_yaml_to_json_string_returns_valid_json_string(self):
        data = textwrap.dedent("""
        foo:
          foo: baa
        """)

        self.assertEqual('{\n  "foo": {\n    "foo": "baa"\n  }\n}', util.convert_yaml_to_json_string(data))

    def test_convert_yaml_to_json_string_returns_valid_json_string_on_empty_string_input(self):
        data = ""
        self.assertEqual('{}', util.convert_yaml_to_json_string(data))

    def test_convert_json_to_yaml_string_returns_valid_yaml_string(self):
        data = textwrap.dedent("""
        {
            "foo": {
                "foo": "baa"
            }
        }
        """)

        self.assertEqual('foo:\n  foo: baa\n', util.convert_json_to_yaml_string(data))

    def test_convert_json_to_yaml_string_returns_empty_string_on_empty_json_input(self):
        data = {}
        self.assertEqual('', util.convert_json_to_yaml_string(data))

    @patch("cfn_sphere.util.urllib2.urlopen")
    def test_get_cfn_api_server_time_returns_gmt_datetime(self, urlopen_mock):
        urlopen_mock.return_value.info.return_value.get.return_value = "Mon, 21 Sep 2015 17:17:26 GMT"
        expected_timestamp = datetime(year=2015, month=9, day=21, hour=17, minute=17, second=26)
        self.assertEqual(expected_timestamp, util.get_cfn_api_server_time())

    @patch("cfn_sphere.util.urllib2.urlopen")
    def test_get_cfn_api_server_time_raises_exception_on_empty_date_header(self, urlopen_mock):
        urlopen_mock.return_value.info.return_value.get.return_value = ""
        with self.assertRaises(CfnSphereException):
            util.get_cfn_api_server_time()

    def test_with_boto_retry_retries_method_call_for_throttling_exception(self):
        count_func = Mock()

        @util.with_boto_retry(max_retries=1, pause_time_multiplier=1)
        def my_retried_method(count_func):
            count_func()
            exception = BotoServerError("400", "error")
            exception.code = 'Throttling'
            raise exception

        with self.assertRaises(BotoServerError):
            my_retried_method(count_func)

        self.assertEqual(2, count_func.call_count)

    def test_with_boto_retry_does_not_retry_for_simple_exception(self):
        count_func = Mock()

        @util.with_boto_retry(max_retries=1, pause_time_multiplier=1)
        def my_retried_method(count_func):
            count_func()
            raise Exception

        with self.assertRaises(Exception):
            my_retried_method(count_func)

        self.assertEqual(1, count_func.call_count)

    def test_with_boto_retry_does_not_retry_for_another_boto_server_error(self):
        count_func = Mock()

        @util.with_boto_retry(max_retries=1, pause_time_multiplier=1)
        def my_retried_method(count_func):
            count_func()
            exception = BotoServerError("400", "error")
            exception.code = 'ValidationError'
            raise exception

        with self.assertRaises(BotoServerError):
            my_retried_method(count_func)

        self.assertEqual(1, count_func.call_count)

    def test_with_boto_retry_does_not_retry_without_exception(self):
        count_func = Mock()

        @util.with_boto_retry(max_retries=1, pause_time_multiplier=1)
        def my_retried_method(count_func):
            count_func()
            return "foo"

        self.assertEqual("foo", my_retried_method(count_func))
        self.assertEqual(1, count_func.call_count)

    def test_get_pretty_parameters_string(self):
        template_body = {
            'Parameters': {
                'myParameter1': {
                    'Type': 'String',
                    'NoEcho': True
                },
                'myParameter2': {
                    'Type': 'String'
                },
                'myParameter3': {
                    'Type': 'Number',
                    'NoEcho': 'true'
                },
                'myParameter4': {
                    'Type': 'Number',
                    'NoEcho': 'false'
                },
                'myParameter5': {
                    'Type': 'Number',
                    'NoEcho': False
                }
            }
        }

        parameters = {
            'myParameter1': 'super-secret',
            'myParameter2': 'not-that-secret',
            'myParameter3': 'also-super-secret',
            'myParameter4': 'could-be-public',
            'myParameter5': 'also-ok'
        }

        template = CloudFormationTemplate(template_body, 'just-another-template')
        stack = CloudFormationStack(template, parameters, 'just-another-stack', 'eu-west-1')

        expected_string = """+--------------+-----------------+
|  Parameter   |      Value      |
+--------------+-----------------+
| myParameter1 |       ***       |
| myParameter2 | not-that-secret |
| myParameter3 |       ***       |
| myParameter4 | could-be-public |
| myParameter5 |     also-ok     |
+--------------+-----------------+"""

        self.assertEqual(expected_string, util.get_pretty_parameters_string(stack))

    def test_parse_parameters_parsing_cli_params(self):
        self.assertEqual(cmp(util.split_parameters_by_stack("stack1:p1=v1,stack1:p2=v2"),
                             {'stack1': {'p1': 'v1', 'p2': 'v2'}}), 0)

    def test_parse_parameters_parsing_invalid_cli_params_throws_exception(self):
        with self.assertRaises(BadConfigException):
            util.split_parameters_by_stack("foobar")

    def test_split_parameters_by_stack(self):
        self.assertEqual(cmp(util.split_parameters_by_stack("stack1:p1=v1,stack1:p2=v2,stack2:p1=v1"),
                         {'stack1': {'p1': 'v1', 'p2': 'v2'}, 'stack2': {'p1': 'v1'}}), 0)
