from unittest import TestCase

from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.file_generator import FileGenerator


class FileGeneratorTests(TestCase):
    def test_is_valid_json(self):
        result = FileGenerator._is_valid_json("""{"a":"b"}""")
        self.assertIsNone(result)

    def test_is_valid_json_raises_exception_on_invalid_json(self):
        with self.assertRaises(CfnSphereException):
            FileGenerator._is_valid_json("""{"a":b}""")

    def test_is_valid_yaml(self):
        result = FileGenerator._is_valid_yaml("""a: b""")
        self.assertIsNone(result)

    def test_is_valid_yaml_raises_exception_on_invalid_yaml(self):
        with self.assertRaises(CfnSphereException):
            FileGenerator._is_valid_yaml("""a: b: c""")
