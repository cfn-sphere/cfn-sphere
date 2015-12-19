from boto import connect_s3
from six.moves.urllib.parse import urlparse
from boto.exception import BotoServerError
from cfn_sphere.exceptions import CfnSphereBotoError


class S3(object):
    def __init__(self):
        self.conn = connect_s3()

    @staticmethod
    def _parse_url(url):
        url_components = urlparse(url)
        protocol = url_components.scheme
        bucket_name = url_components.netloc
        key = url_components.path.strip('/')
        return protocol, bucket_name, key

    def get_contents_from_url(self, url):
        try:
            (_, bucket_name, key_name) = self._parse_url(url)
            bucket = self.conn.get_bucket(bucket_name)
            key = bucket.get_key(key_name)
            return key.get_contents_as_string()
        except BotoServerError as e:
            raise CfnSphereBotoError(e)
