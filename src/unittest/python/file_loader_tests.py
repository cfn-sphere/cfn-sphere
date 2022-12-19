import yaml

try:
    from unittest import TestCase
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
            'Metadata': {},
            'Resources': 'Foo',
            'Parameters': {},
            'Outputs': {},
            'AWSTemplateFormatVersion': '2010-09-09',
            'Description': ''
        }

        get_yaml_or_json_file_mock.return_value = {"Resources": "Foo"}

        result = FileLoader.get_cloudformation_template("s3://my-bucket/template.yml", None)

        self.assertEqual(expected, result.get_template_body_dict())
        get_yaml_or_json_file_mock.assert_called_once_with('s3://my-bucket/template.yml', None)

    @patch("cfn_sphere.file_loader.FileLoader.get_yaml_or_json_file")
    def test_get_cloudformation_template_returns_template_with_transform_property(self, get_yaml_or_json_file_mock):
        expected = {
            'Conditions': {},
            'Mappings': {},
            'Metadata': {},
            'Resources': 'Foo',
            'Transform': 'transform-section',
            'Parameters': {},
            'Outputs': {},
            'AWSTemplateFormatVersion': '2010-09-09',
            'Description': ''
        }

        get_yaml_or_json_file_mock.return_value = {"Resources": "Foo", "Transform": "transform-section"}

        result = FileLoader.get_cloudformation_template("s3://my-bucket/template.yml", None)

        self.assertEqual(expected, result.get_template_body_dict())
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
        if hasattr(yaml_mock, 'FullLoader'):
            loader = yaml_mock.FullLoader
        else:
            loader = yaml_mock.Loader

        yaml_mock.load.assert_called_once_with(get_file_return_value, Loader=loader)

    @patch("cfn_sphere.file_loader.yaml")
    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_parses_yaml_on_yml_suffix(self, get_file_mock, yaml_mock):
        get_file_return_value = Mock()
        get_file_mock.return_value = get_file_return_value

        FileLoader.get_yaml_or_json_file('foo.yml', 'baa')
        if hasattr(yaml_mock, 'FullLoader'):
            loader = yaml_mock.FullLoader
        else:
            loader = yaml_mock.Loader

        yaml_mock.load.assert_called_once_with(get_file_return_value, Loader=loader)

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

    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_accepts_yaml_template_with_ref_constructor_tag(self, get_file_mock):
        get_file_mock.return_value = "myKey: !Ref myResource"
        result = FileLoader.get_yaml_or_json_file("my-template.yaml", None)
        self.assertEqual({"myKey": {"Ref": "myResource"}}, result)

    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_accepts_yaml_template_with_getatt_constructor_tag(self, get_file_mock):
        get_file_mock.return_value = "myKey: !GetAtt myResource.attributeName"
        result = FileLoader.get_yaml_or_json_file("my-template.yaml", None)
        self.assertEqual({"myKey": {"Fn::GetAtt": ["myResource", "attributeName"]}}, result)

    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_accepts_yaml_with_cfn_join_constructor_tag(self, get_file_mock):
        get_file_mock.return_value = "myKey: !Join [ b, [ a, c] ]"
        result = FileLoader.get_yaml_or_json_file("my-template.yaml", None)
        self.assertEqual({"myKey": {"Fn::Join": ["b", ["a", "c"]]}}, result)

    @patch("cfn_sphere.file_loader.FileLoader.get_file")
    def test_get_yaml_or_json_file_accepts_yaml_with_nested_constructor_tags(self, get_file_mock):
        get_file_mock.return_value = "myKey: !Join [ b, [ !ref a, !ref b] ]"
        result = FileLoader.get_yaml_or_json_file("my-template.yaml", None)
        self.assertEqual({"myKey": {"Fn::Join": ["b", [{"Ref": "a"}, {"Ref": "b"}]]}}, result)

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

    def test_handle_yaml_constructors_converts_base64(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = "myString"
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!base64", node_mock)
        self.assertEqual({'Fn::Base64': 'myString'}, response)

    def test_handle_yaml_constructors_converts_and(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["myCondition", "myOtherCondition"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!and", node_mock)
        self.assertEqual({'Fn::And': ["myCondition", "myOtherCondition"]}, response)

    def test_handle_yaml_constructors_converts_equals(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["myValue", "myOtherValue"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!equals", node_mock)
        self.assertEqual({'Fn::Equals': ["myValue", "myOtherValue"]}, response)

    def test_handle_yaml_constructors_converts_if(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["myCondition", "myOtherCondition"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!if", node_mock)
        self.assertEqual({'Fn::If': ["myCondition", "myOtherCondition"]}, response)

    def test_handle_yaml_constructors_converts_not(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["myCondition"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!not", node_mock)
        self.assertEqual({'Fn::Not': ["myCondition"]}, response)

    def test_handle_yaml_constructors_converts_or(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["myCondition", "myOtherCondition"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!or", node_mock)
        self.assertEqual({'Fn::Or': ["myCondition", "myOtherCondition"]}, response)

    def test_handle_yaml_constructors_converts_find_in_map(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["MapName", "TopLevelKey", "SecondLevelKey"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!FindInMap", node_mock)
        self.assertEqual({'Fn::FindInMap': ["MapName", "TopLevelKey", "SecondLevelKey"]}, response)

    def test_handle_yaml_constructors_converts_getatt(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = "logicalNameOfResource.attributeName"
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!GetAtt", node_mock)
        self.assertEqual({'Fn::GetAtt': ["logicalNameOfResource", "attributeName"]}, response)

    def test_handle_yaml_constructors_converts_get_azs(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = "region"
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!GetAZs", node_mock)
        self.assertEqual({'Fn::GetAZs': "region"}, response)

    def test_handle_yaml_constructors_converts_import_value(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = "sharedValue"
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!ImportValue", node_mock)
        self.assertEqual({'Fn::ImportValue': "sharedValue"}, response)

    def test_handle_yaml_constructors_converts_join(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["delimiter", ["a", "b"]]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!join", node_mock)
        self.assertEqual({'Fn::Join': ["delimiter", ["a", "b"]]}, response)

    def test_handle_yaml_constructors_converts_select(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["index", "list"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!select", node_mock)
        self.assertEqual({'Fn::Select': ["index", "list"]}, response)

    def test_handle_yaml_constructors_converts_split(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["delimiter", "string"]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!split", node_mock)
        self.assertEqual({'Fn::Split': ["delimiter", "string"]}, response)

    def test_handle_yaml_constructors_converts_sub(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = ["string", {"key": "value"}]
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!sub", node_mock)
        self.assertEqual({'Fn::Sub': ["string", {"key": "value"}]}, response)

    def test_handle_yaml_constructors_converts_ref(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = "myResource"
        node_mock = Mock(spec=yaml.ScalarNode)

        response = FileLoader.handle_yaml_constructors(loader_mock, "!ref", node_mock)
        self.assertEqual({'Ref': "myResource"}, response)

    def test_handle_yaml_constructors_raises_exception_on_unknown_tag(self):
        loader_mock = Mock()
        loader_mock.construct_scalar.return_value = "myResource"
        node_mock = Mock(spec=yaml.ScalarNode)
        with self.assertRaises(CfnSphereException):
            FileLoader.handle_yaml_constructors(loader_mock, "!anyTag", node_mock)
