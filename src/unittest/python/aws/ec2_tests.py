try: 
    from unittest2 import TestCase
    from mock import Mock, patch
except ImportError:
    from unittest import TestCase
    from unittest.mock import Mock, patch
    
import datetime
from cfn_sphere.aws.ec2 import Ec2Api
from cfn_sphere.exceptions import CfnSphereException
from boto.ec2.image import Image


class Ec2ApiTests(TestCase):
    @patch('cfn_sphere.aws.ec2.ec2.connect_to_region')
    def test_get_taupage_images_raises_exception_on_empty_response(self, ec2_mock):
        ec2_mock.return_value.get_all_images.return_value = []
        with self.assertRaises(CfnSphereException):
            Ec2Api().get_taupage_images()

    @patch('cfn_sphere.aws.ec2.ec2.connect_to_region')
    @patch('cfn_sphere.aws.ec2.Ec2Api.get_taupage_images')
    def test_get_latest_taupage_image_id_returns_id_of_eldest_image(self, get_taupage_images_mock, _):
        image_1 = Mock(spec=Image)
        image_1.id = "image1"
        image_1.creationDate = datetime.datetime(2015, 1, 6, 15, 1, 24, 78915)
        image_2 = Mock(spec=Image)
        image_2.id = "image2"
        image_2.creationDate = datetime.datetime(2015, 1, 6, 15, 8, 24, 78915)
        image_3 = Mock(spec=Image)
        image_3.id = "image3"
        image_3.creationDate = datetime.datetime(2015, 1, 6, 15, 7, 24, 78915)

        get_taupage_images_mock.return_value = [image_1, image_2, image_3]

        self.assertEqual('image2', Ec2Api().get_latest_taupage_image_id())

    @patch('cfn_sphere.aws.ec2.ec2.connect_to_region')
    @patch('cfn_sphere.aws.ec2.Ec2Api.get_taupage_images')
    def test_get_latest_taupage_image_id_returns_only_image(self, get_taupage_images_mock, _):
        image_1 = Mock(spec=Image)
        image_1.id = "image1"
        image_1.creationDate = datetime.datetime(2015, 1, 6, 15, 1, 24, 78915)

        get_taupage_images_mock.return_value = [image_1]

        self.assertEqual('image1', Ec2Api().get_latest_taupage_image_id())
