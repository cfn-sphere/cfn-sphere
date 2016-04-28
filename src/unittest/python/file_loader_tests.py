try:
    from unittest2 import TestCase
    from mock import patch
except ImportError:
    from unittest import TestCase
    from mock import patch

from yaml.scanner import ScannerError

from cfn_sphere.exceptions import TemplateErrorException
from cfn_sphere.file_loader import FileLoader


class FileLoaderTests(TestCase):
    @patch("cfn_sphere.file_loader.yaml")
    @patch("cfn_sphere.file_loader.open")
    def test_fs_get_file_raises_exception_on_yaml_error(self, _, yaml_mock):
        yaml_mock.load.side_effect = ScannerError()

        with self.assertRaises(TemplateErrorException):
            FileLoader._fs_get_file('foo.yml', 'baa')

    @patch("cfn_sphere.file_loader.yaml")
    @patch("cfn_sphere.file_loader.open")
    def test_fs_get_file_raises_exception_on_json_error(self, _, yaml_mock):
        yaml_mock.load.side_effect = ValueError()

        with self.assertRaises(TemplateErrorException):
            FileLoader._fs_get_file('foo.json', 'baa')

    def test_fs_get_file_raises_exception_on_unknown_filetype(self):
        with self.assertRaises(TemplateErrorException):
            FileLoader._fs_get_file('bla.blub', 'baa')

    @patch("cfn_sphere.file_loader.FileLoader._fs_get_file")
    def test_load_template_calls_fs_get_file_for_fs_url(self, mock):
        url = "/tmp/template.json"

        loader = FileLoader
        loader.get_file_from_url(url, None)

        mock.assert_called_with(url, None)

    @patch("cfn_sphere.file_loader.FileLoader._s3_get_file")
    def test_load_template_calls_s3_get_file_for_s3_url(self, mock):
        url = "s3://my-bucket.amazon.com/foo.json"

        loader = FileLoader
        loader.get_file_from_url(url, None)

        mock.assert_called_with(url)

    def test_load_template_raises_exception_on_unknown_protocol(self):
        url = "xxx://foo.json"

        loader = FileLoader

        with self.assertRaises(TemplateErrorException):
            loader.get_file_from_url(url, None)

    @patch('cfn_sphere.file_loader.yaml.load')
    @patch('cfn_sphere.file_loader.json.loads')
    @patch('cfn_sphere.file_loader.S3')
    def test_s3_get_file_returns_parses_json_for_json_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        FileLoader._s3_get_file('s3://foo/baa.json')
        json_mock.assert_called_once_with("{}")
        yaml_mock.assert_not_called()

    @patch('cfn_sphere.file_loader.yaml.load')
    @patch('cfn_sphere.file_loader.json.loads')
    @patch('cfn_sphere.file_loader.S3')
    def test_s3_get_file_parses_yaml_for_yaml_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        FileLoader._s3_get_file('s3://foo/baa.yaml')
        json_mock.assert_not_called()
        yaml_mock.assert_called_once_with("{}")

    @patch('cfn_sphere.file_loader.yaml.load')
    @patch('cfn_sphere.file_loader.json.loads')
    @patch('cfn_sphere.file_loader.S3')
    def test_s3_get_file_parses_yaml_for_yml_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        FileLoader._s3_get_file('s3://foo/baa.yml')
        json_mock.assert_not_called()
        yaml_mock.assert_called_once_with("{}")

    @patch('cfn_sphere.file_loader.yaml.load')
    @patch('cfn_sphere.file_loader.json.loads')
    @patch('cfn_sphere.file_loader.S3')
    def test_s3_get_file__raises_exception_for_unknown_suffix(self, s3_mock, json_mock, yaml_mock):
        s3_mock.return_value.get_contents_from_url.return_value = "{}"

        with self.assertRaises(TemplateErrorException):
            FileLoader._s3_get_file('s3://foo/baa.foo')
