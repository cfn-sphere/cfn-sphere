from unittest import TestCase

from mock import patch

from cfn_sphere.cli import get_first_account_alias_or_account_id


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
