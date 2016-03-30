import unittest2
from moto import mock_s3
from cfn_sphere.aws.s3 import S3


class S3Tests(unittest2.TestCase):
    def test_parse_url_properly_parses_s3_url(self):
        (protocol, bucket_name, key_name) = S3._parse_url('s3://my-bucket/my/key/file.json')
        self.assertEqual('s3', protocol)
        self.assertEqual('my-bucket', bucket_name)
        self.assertEqual('my/key/file.json', key_name)

    @mock_s3
    def test(self):
        S3().get_contents_from_url('s3://my-bucket/my/key/file.json')
