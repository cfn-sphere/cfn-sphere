try:
    from unittest2 import TestCase
    from mock import patch
except ImportError:
    from unittest import TestCase
    from mock import patch

from yaml.scanner import ScannerError

from cfn_sphere.exceptions import TemplateErrorException, CfnSphereException
from cfn_sphere.file_loader import FileLoader


class FileLoaderTests(TestCase):
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
