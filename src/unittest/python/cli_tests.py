from cfn_sphere.cli import get_first_account_alias_or_account_id, kv_list_to_dict
from cfn_sphere.exceptions import CfnSphereException

try:
    from unittest2 import TestCase
    from mock import patch, Mock
except ImportError:
    from unittest import TestCase
    from mock import patch, Mock


class CliTests(TestCase):
    @patch("boto3.client")
    def test_get_first_account_alias_or_account_id_returns_first_account_alias(self, boto_mock):
        boto_mock.return_value.list_account_aliases.return_value = {"AccountAliases": ["a", "b", "c"]}

        result = get_first_account_alias_or_account_id()
        self.assertEqual("a", result)

    @patch("boto3.client")
    def test_get_first_account_alias_or_account_id_returns_account_id_if_no_alias_found(self, boto_mock):
        boto_mock.return_value.list_account_aliases.return_value = {"AccountAliases": []}
        boto_mock.return_value.get_caller_identity.return_value = {"Arn": "arn:aws:iam::ACCOUNT_ID:user/USERNAME"}

        result = get_first_account_alias_or_account_id()
        self.assertEqual("ACCOUNT_ID", result)

    def test_kv_list_to_dict_returns_empty_dict_for_empty_list(self):
        result = kv_list_to_dict([])
        self.assertEqual({}, result)

    def test_kv_list_to_dict(self):
        result = kv_list_to_dict(["k1=v1", "k2=v2"])
        self.assertEqual({"k1": "v1", "k2": "v2"}, result)

    def test_kv_list_to_dict_raises_exception_on_syntax_error(self):
        with self.assertRaises(CfnSphereException):
            kv_list_to_dict(["k1=v1", "k2:v2"])
