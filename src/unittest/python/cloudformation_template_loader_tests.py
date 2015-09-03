import unittest2
from mock import patch
from cfn_sphere.aws.cloudformation.template_loader import CloudFormationTemplateLoader
from cfn_sphere.exceptions import TemplateErrorException


class CloudFormationTemplateLoaderTests(unittest2.TestCase):
    @patch("cfn_sphere.aws.cloudformation.template_loader.CloudFormationTemplateLoader._fs_get_template")
    def test_load_template_calls_fs_get_template_for_fs_url(self, mock):
        url = "/tmp/template.json"

        loader = CloudFormationTemplateLoader
        loader.get_template_from_url(url, None)

        mock.assert_called_with(url, None)

    @patch("cfn_sphere.aws.cloudformation.template_loader.CloudFormationTemplateLoader._s3_get_template")
    def test_load_template_calls_s3_get_template_for_s3_url(self, mock):
        url = "s3://my-bucket.amazon.com/foo.json"

        loader = CloudFormationTemplateLoader
        loader.get_template_from_url(url, None)

        mock.assert_called_with(url)

    def test_load_template_raises_exception_on_unknown_protocol(self):
        url = "xxx://foo.json"

        loader = CloudFormationTemplateLoader

        with self.assertRaises(TemplateErrorException):
            loader.get_template_from_url(url, None)