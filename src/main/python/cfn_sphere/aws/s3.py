import boto3
from boto3.exceptions import Boto3Error
from botocore.exceptions import BotoCoreError, ClientError
from six.moves.urllib.parse import urlparse

from cfn_sphere.exceptions import CfnSphereBotoError
from cfn_sphere.util import with_boto_retry


class S3(object):
    def __init__(self):
        self.s3 = boto3.resource('s3')

    @staticmethod
    def _parse_url(url):
        url_components = urlparse(url)
        protocol = url_components.scheme
        bucket_name = url_components.netloc
        key = url_components.path.strip('/')
        return protocol, bucket_name, key

    @with_boto_retry()
    def get_contents_from_url(self, url):
        try:
            (_, bucket_name, key_name) = self._parse_url(url)
            s3_object = self.s3.Object(bucket_name, key_name)
            return s3_object.get(ResponseContentEncoding='utf-8')["Body"].read().decode('utf-8')
        except (Boto3Error, BotoCoreError, ClientError) as e:
            raise CfnSphereBotoError(e)
