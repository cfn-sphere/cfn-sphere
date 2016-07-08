# -*- coding: utf-8 -*-

import boto3
import unittest2

from cfn_sphere.aws.kms import KMS
from cfn_sphere.exceptions import CfnSphereBotoError


class KMSTests(unittest2.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create a KMS key, unless it already exists. Simple create&delete is
        # not possible for KMS, the earliest you can delete a newly created key
        # is 7 days later.
        cls.key_alias = "alias/cfn-sphere-integrationtests"

        kms_client = boto3.client('kms', region_name='eu-west-1')
        existing_aliases = [item['AliasName'] for item in kms_client.list_aliases()['Aliases']]
        if cls.key_alias in existing_aliases:
            return

        response = kms_client.create_key(
            Description=('A key used by the integration tests of cfn-sphere.'
                         'You can safely delete it.')
        )
        key_arn = response['KeyMetadata']['Arn']
        kms_client.create_alias(AliasName=cls.key_alias, TargetKeyId=key_arn)

    def test_encrypt_decrypt_unicode_data(self):
        before = u"abcd$%&öäüß"
        kms_client = KMS()
        ciphertext = kms_client.encrypt(self.key_alias, before)
        after = kms_client.decrypt(ciphertext)
        self.assertEqual(before, after)

    def test_encrypt_with_invalid_key_id(self):
        kms_client = KMS()
        self.assertRaises(CfnSphereBotoError,
                          kms_client.encrypt, "invalid or nonexsting ID", "x")


if __name__ == "__main__":
    unittest2.main()
