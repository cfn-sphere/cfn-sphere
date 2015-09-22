import unittest2
from mock import Mock, patch
from cfn_sphere.aws.ec2 import Ec2Api
from cfn_sphere.exceptions import CfnSphereException


class Ec2ApiTests(unittest2.TestCase):

    @patch('cfn_sphere.aws.ec2.ec2.connect_to_region')
    def test_get_latest_taupage_image_id_raises_exception_on_empty_response(self, ec2_mock):
        ec2_mock.return_value.get_all_images.return_value = []
        with self.assertRaises(CfnSphereException):
            Ec2Api().get_latest_taupage_image_id()


    @patch('cfn_sphere.aws.ec2.ec2.connect_to_region')
    def test_get_latest_taupage_image_id_returns_id_of_eldest_image(self, ec2_mock):
        ec2_mock.return_value.get_all_images.return_value = [Mock()]
        print Ec2Api().get_latest_taupage_image_id()