try:
    from unittest2 import TestCase
    from mock import Mock, patch
except ImportError:
    from unittest import TestCase
    from unittest.mock import Mock, patch

import datetime

from cfn_sphere.aws.ec2 import Ec2Api
from cfn_sphere.exceptions import CfnSphereException


class Ec2ApiTests(TestCase):
    @patch("cfn_sphere.aws.ec2.boto3.client")
    def test_get_images_raises_exception_on_empty_response(self, boto_client):
        boto_client.return_value.describe_images.return_value = {'Images': []}

        with self.assertRaises(CfnSphereException):
            print(Ec2Api().get_images("foo"))

    def test_get_latest_image_id_returns_the_most_recent_image_id(self):
        images = [
            {'ImageId': 'image1', 'CreationDate': datetime.datetime(2015, 1, 6, 15, 1, 24, 78915)},
            {'ImageId': 'image2', 'CreationDate': datetime.datetime(2015, 1, 6, 15, 8, 24, 78915)},
            {'ImageId': 'image3', 'CreationDate': datetime.datetime(2012, 11, 6, 15, 7, 24, 78915)}
        ]

        result = Ec2Api.get_latest_image_id(images)
        self.assertEqual('image2', result)

    def test_get_latest_image_id_returns_id_of_single_image(self):
        images = [
            {'ImageId': 'image1', 'CreationDate': datetime.datetime(2015, 1, 6, 15, 1, 24, 78915)}
        ]

        result = Ec2Api.get_latest_image_id(images)
        self.assertEqual('image1', result)
