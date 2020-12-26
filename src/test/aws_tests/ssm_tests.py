try:
    from unittest2 import TestCase
    from mock import patch
except ImportError:
    from unittest import TestCase
    from mock import patch

from cfn_sphere.aws.ssm import SSM


class SSMTests(TestCase):
    @patch('cfn_sphere.aws.ssm.boto3.client')
    def test_decrypt_value(self, boto_mock):
        boto_mock.return_value.get_parameter.return_value = {'Parameter': { 'Value': 'decryptedValue'} }

        self.assertEqual('decryptedValue', SSM().get_parameter('/test'))
        boto_mock.return_value.get_parameter.assert_called_once_with(Name='/test', WithDecryption=True)
