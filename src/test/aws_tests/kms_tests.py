import base64
from cfn_sphere.aws.kms import KMS
from unittest.mock import patch
from unittest import TestCase


class KMSTests(TestCase):
    @patch('cfn_sphere.aws.kms.boto3.client')
    def test_decrypt_value(self, boto_mock):
        boto_mock.return_value.decrypt.return_value = {'Plaintext': b'decryptedValue'}

        self.assertEqual('decryptedValue', KMS().decrypt("ZW5jcnlwdGVkVmFsdWU="))
        boto_mock.return_value.decrypt.assert_called_once_with(CiphertextBlob=b'encryptedValue', EncryptionContext={})

    @patch('cfn_sphere.aws.kms.boto3.client')
    def test_decrypt_value_with_execution_context(self, boto_mock):
        boto_mock.return_value.decrypt.return_value = {'Plaintext': b'decryptedValue'}

        self.assertEqual('decryptedValue', KMS().decrypt("ZW5jcnlwdGVkVmFsdWU=", {"k1": "v1", "k2": "v2"}))
        boto_mock.return_value.decrypt.assert_called_once_with(CiphertextBlob=b'encryptedValue',
                                                               EncryptionContext={'k2': 'v2', 'k1': 'v1'})

    @patch('cfn_sphere.aws.kms.boto3.client')
    def test_decrypt_value_with_unicode_char(self, boto_mock):
        boto_mock.return_value.decrypt.return_value = {
            'Plaintext': b'(\xe2\x95\xaf\xc2\xb0\xe2\x96\xa1\xc2\xb0\xef\xbc\x89\xe2\x95\xaf\xef\xb8\xb5 \xe2\x94\xbb\xe2\x94\x81\xe2\x94\xbb'}

        self.assertEqual(u'(\u256f\xb0\u25a1\xb0\uff09\u256f\ufe35 \u253b\u2501\u253b',
                         KMS().decrypt("KOKVr8Kw4pahwrDvvInila/vuLUg4pS74pSB4pS7"))

        boto_mock.return_value.decrypt.assert_called_once_with(
            CiphertextBlob=base64.b64decode("KOKVr8Kw4pahwrDvvInila/vuLUg4pS74pSB4pS7".encode()), EncryptionContext={})
