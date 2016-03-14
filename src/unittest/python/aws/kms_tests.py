import base64

import unittest2
from boto.kms.exceptions import InvalidCiphertextException
from mock import patch

from cfn_sphere.aws.kms import KMS
from cfn_sphere.exceptions import InvalidEncryptedValueException


class KMSTests(unittest2.TestCase):
    @patch('cfn_sphere.aws.kms.kms.connect_to_region')
    def test_decrypt_value(self, kms_mock):
        kms_mock.return_value.decrypt.return_value = {'Plaintext': bytes('decryptedValue', encoding='utf-8')}

        self.assertEqual('decryptedValue', KMS().decrypt("ZW5jcnlwdGVkVmFsdWU="))
        kms_mock.return_value.decrypt.assert_called_once_with(base64.b64decode("ZW5jcnlwdGVkVmFsdWU=".encode()))

    @patch('cfn_sphere.aws.kms.kms.connect_to_region')
    def test_invalid_base64(self, kms_mock):
        with self.assertRaises(InvalidEncryptedValueException):
            KMS().decrypt("asdqwda")

    @patch('cfn_sphere.aws.kms.kms.connect_to_region')
    def test_invalid_kms_key(self, kms_mock):
        kms_mock.return_value.decrypt.side_effect = InvalidCiphertextException("400", "Bad Request")

        with self.assertRaises(InvalidEncryptedValueException):
            KMS().decrypt("ZW5jcnlwdGVkVmFsdWU=")
