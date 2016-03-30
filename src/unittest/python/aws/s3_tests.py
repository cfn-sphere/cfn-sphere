from botocore.response import StreamingBody
import unittest2


try:
    from unittest2 import TestCase
    from mock import Mock, patch
except ImportError:
    from unittest import TestCase
    from unittest.mock import Mock, patch

from cfn_sphere.aws.s3 import S3


class S3Tests(unittest2.TestCase):
    def test_parse_url_properly_parses_s3_url(self):
        (protocol, bucket_name, key_name) = S3._parse_url('s3://my-bucket/my/key/file.json')
        self.assertEqual('s3', protocol)
        self.assertEqual('my-bucket', bucket_name)
        self.assertEqual('my/key/file.json', key_name)

    @patch('cfn_sphere.aws.s3.boto3.resource')
    def test_get_contents_from_url_returns_string_content(self, resource_mock):
        body_mock = Mock(spec=StreamingBody)
        body_mock.read.return_value = b'Foo'

        resource_mock.return_value.Object.return_value.get.return_value = {"Body": body_mock}

        result = S3().get_contents_from_url('s3://my-bucket/my/key/file.json')
        self.assertEqual("Foo", result)

