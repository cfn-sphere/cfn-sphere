try:
    from unittest2 import TestCase
    from mock import patch, Mock
except ImportError:
    from unittest import TestCase
    from mock import patch, Mock

from yaml.scanner import ScannerError

from cfn_sphere.exceptions import TemplateErrorException, CfnSphereException, CfnSphereBotoError
from cfn_sphere.file_loader import FileLoader


class FileLoaderTests(TestCase):
    @patch("cfn_sphere.file_loader.FileLoader.get_yaml_or_json_file")
    def test_get_cloudformation_template_returns_template(self, get_yaml_or_json_file_mock):
        expected = {
            'Conditions': {},
            'Mappings': {},
            'Resources': 'Foo',
            'Parameters': {},
            'Outputs': {},
            'AWSTemplateFormatVersion': '2010-09-09',
            'Description': ''
        }

        get_yaml_or_json_file_mock.return_value = {"Resources": "Foo"}

        response = FileLoader.get_cloudformation_template("s3://my-bucket/template.yml", None)

        self.assertEqual(expected, response.get_template_body_dict())
        get_yaml_or_json_file_mock.assert_called_once_with('s3://my-bucket/template.yml', None)

    @patch("cfn_sphere.file_loader.FileLoader.get_yaml_or_json_file")
    def test_get_cloudformation_template_raises_exception_on_any_error(self, get_yaml_or_json_file_mock):
        get_yaml_or_json_file_mock.side_effect = Exception

        with self.assertRaises(TemplateErrorException):
            FileLoader.get_cloudformation_template("s3://my-bucket/template.yml", None)

    @patch("cfn_sphere.file_loader.json")
    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_parses_json_on_json_suffix(self, get_file_mock, json_mock):
        get_file_return_value = Mock()
        get_file_mock.return_value = get_file_return_value

        FileLoader.get_yaml_or_json_file('foo.json', 'baa')
        json_mock.loads.assert_called_once_with(get_file_return_value)

    @patch("cfn_sphere.file_loader.yaml")
    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_parses_yaml_on_yaml_suffix(self, get_file_mock, yaml_mock):
        get_file_return_value = Mock()
        get_file_mock.return_value = get_file_return_value

        FileLoader.get_yaml_or_json_file('foo.yaml', 'baa')
        yaml_mock.load.assert_called_once_with(get_file_return_value)

    @patch("cfn_sphere.file_loader.yaml")
    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_parses_yaml_on_yml_suffix(self, get_file_mock, yaml_mock):
        get_file_return_value = Mock()
        get_file_mock.return_value = get_file_return_value

        FileLoader.get_yaml_or_json_file('foo.yml', 'baa')
        yaml_mock.load.assert_called_once_with(get_file_return_value)

    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_raises_exception_invalid_file_extension(self, _):
        with self.assertRaises(CfnSphereException):
            FileLoader.get_yaml_or_json_file('foo.foo', 'baa')

    @patch("cfn_sphere.file_loader.yaml")
    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_raises_exception_on_yaml_error(self, _, yaml_mock):
        yaml_mock.load.side_effect = ScannerError()

        with self.assertRaises(CfnSphereException):
            FileLoader.get_yaml_or_json_file('foo.yml', 'baa')

    @patch("cfn_sphere.file_loader.json")
    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_raises_exception_on_json_error(self, _, json_mock):
        json_mock.loads.side_effect = ValueError()

        with self.assertRaises(CfnSphereException):
            FileLoader.get_yaml_or_json_file('foo.json', 'baa')

    @patch("cfn_sphere.file_loader.FileLoader._s3_get_file")
    def test_get_file_calls_correct_handler_for_s3_prefix(self, s3_get_file_mock):
        FileLoader.get_file("s3://foo/foo.yml", None)
        s3_get_file_mock.assert_called_with("s3://foo/foo.yml")

    @patch("cfn_sphere.file_loader.FileLoader._s3_get_file")
    def test_get_file_calls_correct_handler_for_S3_prefix(self, s3_get_file_mock):
        FileLoader.get_file("S3://foo/foo.yml", None)
        s3_get_file_mock.assert_called_with("S3://foo/foo.yml")

    @patch("cfn_sphere.file_loader.FileLoader._fs_get_file")
    def test_get_file_calls_correct_handler_for_fs_path(self, fs_get_file_mock):
        FileLoader.get_file("foo/foo.yml", "/home/user")
        fs_get_file_mock.assert_called_with("foo/foo.yml", "/home/user")

    @patch("cfn_sphere.file_loader.codecs.open")
    def test_fs_get_file_constructs_absolute_path_if_url_is_relative_and_workingdir_is_set(self, open_mock):
        FileLoader._fs_get_file("foo/foo.yml", "/home/user")
        open_mock.assert_called_once_with("/home/user/foo/foo.yml", 'r', encoding='utf-8')

    @patch("cfn_sphere.file_loader.codecs.open")
    def test_fs_get_file_absolute_url_without_modification(self, open_mock):
        FileLoader._fs_get_file("/foo/foo.yml", "/home/user")
        open_mock.assert_called_once_with("/foo/foo.yml", 'r', encoding='utf-8')

    @patch("cfn_sphere.file_loader.codecs.open")
    def test_fs_get_file_raises_exception_on_any_error(self, open_mock):
        open_mock.side_effect = IOError
        with self.assertRaises(CfnSphereException):
            FileLoader._fs_get_file("/foo/foo.yml", None)

    @patch("cfn_sphere.file_loader.S3")
    def test_s3_get_file_raises_exception_on_error(self, s3_mock):
        s3_mock.return_value.get_contents_from_url.side_effect = CfnSphereBotoError

        with self.assertRaises(CfnSphereException):
            FileLoader._s3_get_file("s3://foo/foo.yml")