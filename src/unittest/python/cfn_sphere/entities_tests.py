__author__ = 'mhoyer'

import unittest2
import inspect
from cfn_sphere.connector.cloudformation import CloudFormationTemplate
from mock import patch, MagicMock


class CloudFormationTemplateTests(unittest2.TestCase):

    def setUp(self):
        self.cfn_template = CloudFormationTemplate("", template_body={"bla": "foo"})

    def test_get_protocol_handler_returns_none_for_invalid_protocol(self):
        self.assertIsNone(self.cfn_template._load_template("bbbb://cc.de"))

    def test_get_protocol_handler_returns_s3_handler(self):
        self.assertEqual("_s3_get_template", self.cfn_template._load_template("s3://cc.de").__name__)

    def test_get_protocol_handler_returns_http_handler(self):
        self.assertEqual("_http_get_template", self.cfn_template._load_template("http://cc.de").__name__)

    @patch('__builtin__.open')
    def test_get_protocol_handler_returns_fs_handler(self, mock_open):
        mock_open.return_value = MagicMock(spec=file)
        self.assertEqual("_fs_get_template", self.cfn_template._load_template("/tmp/foo.json").__name__)

    def test_get_protocol_handler_returns_method(self):
        self.assertTrue(inspect.ismethod(self.cfn_template._load_template("s3://cc.de")))