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

    @patch('cfn_sphere.aws.cloudformation.template_loader.yaml.load')
    @patch('cfn_sphere.aws.cloudformation.template_loader.json.loads')
    @patch('cfn_sphere.aws.cloudformation.template_loader.S3')
    def test_s3_get_template_returns_parses_json_for_json_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        CloudFormationTemplateLoader._s3_get_template('s3://foo/baa.json')
        json_mock.assert_called_once_with("{}")
        yaml_mock.assert_not_called()

    @patch('cfn_sphere.aws.cloudformation.template_loader.yaml.load')
    @patch('cfn_sphere.aws.cloudformation.template_loader.json.loads')
    @patch('cfn_sphere.aws.cloudformation.template_loader.S3')
    def test_s3_get_template_parses_yaml_for_yaml_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        CloudFormationTemplateLoader._s3_get_template('s3://foo/baa.yaml')
        json_mock.assert_not_called()
        yaml_mock.assert_called_once_with("{}")

    @patch('cfn_sphere.aws.cloudformation.template_loader.yaml.load')
    @patch('cfn_sphere.aws.cloudformation.template_loader.json.loads')
    @patch('cfn_sphere.aws.cloudformation.template_loader.S3')
    def test_s3_get_template_parses_yaml_for_yml_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        CloudFormationTemplateLoader._s3_get_template('s3://foo/baa.yml')
        json_mock.assert_not_called()
        yaml_mock.assert_called_once_with("{}")

    @patch('cfn_sphere.aws.cloudformation.template_loader.yaml.load')
    @patch('cfn_sphere.aws.cloudformation.template_loader.json.loads')
    @patch('cfn_sphere.aws.cloudformation.template_loader.S3')
    def test_s3_get_template__raises_exception_for_unknown_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateLoader._s3_get_template('s3://foo/baa.foo')