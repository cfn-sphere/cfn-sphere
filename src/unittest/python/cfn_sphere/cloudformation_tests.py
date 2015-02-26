__author__ = 'mhoyer'

import unittest2
from cfn_sphere.connector.cloudformation import CloudFormationTemplate
from mock import patch, Mock


class CloudFormationTemplateTests(unittest2.TestCase):

    def setUp(self):
        self.cfn_template = CloudFormationTemplate("", template_body={"bla": "foo"})

    @patch("cfn_sphere.connector.cloudformation.CloudFormationTemplate._fs_get_template")
    def test_load_template_calls_fs_get_template_for_fs_url(self, mock):
        URL = "/tmp/template.json"

        self.cfn_template._load_template(URL)
        mock.assert_called_with(URL)

    @patch("cfn_sphere.connector.cloudformation.CloudFormationTemplate._s3_get_template")
    def test_load_template_calls_s3_get_template_for_s3_url(self, mock):
        URL = "s3://my-bucket.amazon.com/foo.json"

        self.cfn_template._load_template(URL)
        mock.assert_called_with(URL)

    def test_load_template_raises_exception_on_unknown_protocol(self):
        URL = "xxx://foo.json"
        with self.assertRaises(IOError):
            self.cfn_template._load_template(URL)