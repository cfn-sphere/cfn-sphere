import tempfile

from git import InvalidGitRepositoryError

try:
    from unittest2 import TestCase
    from mock import patch, Mock
except ImportError:
    from unittest import TestCase
    from mock import patch, Mock

import textwrap
from datetime import datetime

from botocore.exceptions import ClientError
from dateutil.tz import tzutc

from cfn_sphere import util, CloudFormationStack
from cfn_sphere.exceptions import CfnSphereException, CfnSphereBotoError
from cfn_sphere.template import CloudFormationTemplate


class UtilTests(TestCase):
    def test_convert_yaml_to_json_string_returns_valid_json_string(self):
        data = textwrap.dedent("""
        foo:
          foo: baa
        """)

        print(util.convert_yaml_to_json_string(data))
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
        expected_timestamp = datetime(year=2015, month=9, day=21, hour=17, minute=17, second=26, tzinfo=tzutc())
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
            exception = CfnSphereBotoError(
                ClientError(error_response={"Error": {"Code": "Throttling", "Message": "Rate exceeded"}},
                            operation_name="DescribeStacks"))
            raise exception

        with self.assertRaises(CfnSphereBotoError):
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

    def test_with_boto_retry_does_not_retry_for_another_boto_client_error(self):
        count_func = Mock()

        @util.with_boto_retry(max_retries=1, pause_time_multiplier=1)
        def my_retried_method(count_func):
            count_func()
            exception = ClientError(error_response={"Error": {"Code": "Another Error", "Message": "Foo"}},
                                    operation_name="DescribeStacks")
            raise exception

        with self.assertRaises(ClientError):
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

    def test_get_pretty_stack_outputs_returns_proper_table(self):
        outputs = [
            {
                'OutputKey': 'key1',
                'OutputValue': 'value1',
                'Description': 'desc1'
            }, {
                'OutputKey': 'key2',
                'OutputValue': 'value2',
                'Description': 'desc2'
            }, {
                'OutputKey': 'key3',
                'OutputValue': 'value3',
                'Description': 'desc3'
            }
        ]

        expected = """+--------+--------+
| Output | Value  |
+--------+--------+
|  key1  | value1 |
|  key2  | value2 |
|  key3  | value3 |
+--------+--------+"""

        result = util.get_pretty_stack_outputs(outputs)
        self.assertEqual(expected, result)

    def test_strip_string_strips_string(self):
        s = "sfsdklgashgslkadghkafhgaknkbndkjfbnwurtqwhgsdnkshGLSAKGKLDJFHGSKDLGFLDFGKSDFLGKHAsdjdghskjdhsdcxbvwerA323"
        result = util.strip_string(s)
        self.assertEqual(
            "sfsdklgashgslkadghkafhgaknkbndkjfbnwurtqwhgsdnkshGLSAKGKLDJFHGSKDLGFLDFGKSDFLGKHAsdjdghskjdhsdcxbvwe...",
            result)

    def test_strip_string_doesnt_strip_short_strings(self):
        s = "my-short-string"
        result = util.strip_string(s)
        self.assertEqual("my-short-string...", result)

    @patch("cfn_sphere.util.Repo")
    def test_get_git_repository_remote_url_returns_none_if_no_repository_present(self, repo_mock):
        repo_mock.side_effect = InvalidGitRepositoryError
        self.assertEqual(None, util.get_git_repository_remote_url(tempfile.mkdtemp()))

    @patch("cfn_sphere.util.Repo")
    def test_get_git_repository_remote_url_returns_repo_url(self, repo_mock):
        url = "http://config.repo.git"
        repo_mock.return_value.remotes.origin.url = url
        self.assertEqual(url, util.get_git_repository_remote_url(tempfile.mkdtemp()))

    @patch("cfn_sphere.util.Repo")
    def test_get_git_repository_remote_url_returns_repo_url_from_parent_dir(self, repo_mock):
        url = "http://config.repo.git"
        repo_object_mock = Mock()
        repo_object_mock.remotes.origin.url = url
        repo_mock.side_effect = [InvalidGitRepositoryError, repo_object_mock]

        self.assertEqual(url, util.get_git_repository_remote_url(tempfile.mkdtemp()))

    def test_get_git_repository_remote_url_returns_none_for_none_working_dir(self):
        self.assertEqual(None, util.get_git_repository_remote_url(None))

    def test_get_git_repository_remote_url_returns_none_for_empty_string_working_dir(self):
        self.assertEqual(None, util.get_git_repository_remote_url(""))

    def test_kv_list_to_dict_returns_empty_dict_for_empty_list(self):
        result = util.kv_list_to_dict([])
        self.assertEqual({}, result)

    def test_kv_list_to_dict(self):
        result = util.kv_list_to_dict(["k1=v1", "k2=v2"])
        self.assertEqual({"k1": "v1", "k2": "v2"}, result)

    def test_kv_list_to_dict_raises_exception_on_syntax_error(self):
        with self.assertRaises(CfnSphereException):
            util.kv_list_to_dict(["k1=v1", "k2:v2"])
