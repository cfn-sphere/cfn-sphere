try:
    from unittest import TestCase
    from mock import patch, Mock
except ImportError:
    from unittest import TestCase
    from mock import patch, Mock

from cfn_sphere.exceptions import CfnSphereException, CfnSphereBotoError
from cfn_sphere.stack_configuration.parameter_resolver import ParameterResolver


class ParameterResolverTests(TestCase):
    def setUp(self):
        self.cloudformation_patcher = patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
        self.ec2api_patcher = patch('cfn_sphere.stack_configuration.parameter_resolver.Ec2Api')
        self.kms_patcher = patch('cfn_sphere.stack_configuration.parameter_resolver.KMS')
        self.ssm_patcher = patch('cfn_sphere.stack_configuration.parameter_resolver.SSM')
        self.cfn_mock = self.cloudformation_patcher.start()
        self.ec2api_mock = self.ec2api_patcher.start()
        self.kms_mock = self.kms_patcher.start()
        self.ssm_mock = self.ssm_patcher.start()

    def tearDown(self):
        self.cloudformation_patcher.stop()
        self.ec2api_patcher.stop()
        self.kms_patcher.stop()
        self.ssm_patcher.stop()

    def test_convert_list_to_string_returns_valid_string(self):
        list = ['a', 'b', 'c']
        self.assertEqual("a,b,c", ParameterResolver.convert_list_to_string(list))

    def test_convert_list_to_string_returns_valid_string_if_list_contains_int(self):
        list = ['a', 6, 'c']
        self.assertEqual("a,6,c", ParameterResolver.convert_list_to_string(list))

    def test_convert_list_to_string_returns_empty_list_on_empty_list(self):
        self.assertEqual("", ParameterResolver.convert_list_to_string([]))

    @patch('cfn_sphere.stack_configuration.parameter_resolver.ParameterResolver.convert_list_to_string')
    def test_resolve_parameter_values_calls_convert_list_to_string_on_list_value(self, convert_list_to_string_mock):
        stack_config = Mock()
        stack_config.parameters = {'foo': ['a', 'b']}

        ParameterResolver().resolve_parameter_values('foo', stack_config)
        convert_list_to_string_mock.assert_called_once_with(['a', 'b'])

    @patch('cfn_sphere.stack_configuration.parameter_resolver.ParameterResolver.get_output_value')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    def test_resolve_parameter_values_returns_ref_value(self, cfn_mock, get_output_value_mock):
        cfn_mock.return_value.get_stacks_outputs.return_value = None
        get_output_value_mock.return_value = 'bar'

        stack_config = Mock()
        stack_config.parameters = {'foo': '|Ref|stack.output'}

        result = ParameterResolver().resolve_parameter_values('foo', stack_config)

        get_output_value_mock.assert_called_with(None, "stack", "output")
        self.assertEqual({'foo': 'bar'}, result)

    @patch('cfn_sphere.stack_configuration.parameter_resolver.ParameterResolver.get_output_value')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    def test_resolve_parameter_values_returns_ref_list_value(self, cfn_mock, get_output_value_mock):
        cfn_mock.return_value.get_stacks_outputs.return_value = None
        get_output_value_mock.return_value = 'bar'

        stack_config = Mock()
        stack_config.parameters = {'foo': ['|Ref|stack.output', '|Ref|stack.output']}

        result = ParameterResolver().resolve_parameter_values('foo', stack_config)

        get_output_value_mock.assert_called_with(None, "stack", "output")
        self.assertEqual({'foo': 'bar,bar'}, result)

    def test_resolve_parameter_values_raises_exception_on_none_value(self):
        stack_config = Mock()
        stack_config.parameters = {'foo': None}

        with self.assertRaises(CfnSphereException):
            ParameterResolver().resolve_parameter_values('foo', stack_config)

    def test_resolve_parameter_values_returns_list_with_string_value(self):
        stack_config = Mock()
        stack_config.parameters = {'foo': "baa"}

        result = ParameterResolver().resolve_parameter_values('foo', stack_config)
        self.assertEqual({'foo': 'baa'}, result)

    def test_resolve_parameter_values_returns_str_representation_of_false(self):
        stack_config = Mock()
        stack_config.parameters = {'foo': False}

        result = ParameterResolver().resolve_parameter_values('foo', stack_config)
        self.assertEqual({'foo': 'false'}, result)

    def test_resolve_parameter_values_returns_str_representation_of_int(self):
        stack_config = Mock()
        stack_config.parameters = {'foo': 5}
        result = ParameterResolver().resolve_parameter_values('foo', stack_config)
        self.assertEqual({'foo': '5'}, result)

    def test_resolve_parameter_values_returns_str_representation_of_float(self):
        stack_config = Mock()
        stack_config.parameters = {'foo': 5.555}
        result = ParameterResolver().resolve_parameter_values('foo', stack_config)
        self.assertEqual({'foo': '5.555'}, result)

    def test_get_latest_value_returns_stacks_actual_value(self):
        self.cfn_mock.return_value.get_stack_parameters_dict.return_value = {'my-key': 'my-actual-value'}

        pr = ParameterResolver()
        result = pr.get_latest_value('my-key', '|keepOrUse|default-value', 'my-stack')

        self.cfn_mock.return_value.get_stack_parameters_dict.assert_called_once_with('my-stack')
        self.assertEqual('my-actual-value', result)

    def test_get_latest_value_returns_default_value_called_once_with_stack(self):
        self.cfn_mock.return_value.get_stack_parameters_dict.return_value = {'not-my-key': 'my-actual-value'}

        pr = ParameterResolver()
        result = pr.get_latest_value('my-key', '|keepOrUse|default-value', 'my-stack')

        self.cfn_mock.return_value.get_stack_parameters_dict.assert_called_once_with('my-stack')
        self.assertEqual('default-value', result)

    def test_get_latest_value_raises_exception_on_error(self):
        self.cfn_mock.return_value.get_stack_parameters_dict.side_effect = CfnSphereBotoError(Exception("foo"))

        resolver = ParameterResolver()
        with self.assertRaises(CfnSphereException):
            resolver.get_latest_value('my-key', '|keepOrUse|default-value', 'my-stack')

    def test_is_keep_value_returns_true_for_keep_keyword(self):
        result = ParameterResolver.is_keep_value('|keeporuse|')
        self.assertTrue(result)

    def test_is_keep_value_returns_true_for_uppercase_keep_keyword(self):
        result = ParameterResolver.is_keep_value('|KEEPORUSE|')
        self.assertTrue(result)

    def test_is_keep_value_returns_true_for_mixed_case_keep_keyword(self):
        result = ParameterResolver.is_keep_value('|keepOrUse|')
        self.assertTrue(result)

    def test_is_keep_value_returns_false_for_empty_value(self):
        result = ParameterResolver.is_keep_value('')
        self.assertFalse(result)

    def test_get_default_from_keep_value_returns_proper_string(self):
        result = ParameterResolver.get_default_from_keep_value('|keepOrUse|foo')
        self.assertEqual('foo', result)

    def test_get_default_from_keep_value_returns_proper_string_if_it_contains_separator(self):
        result = ParameterResolver.get_default_from_keep_value('|keepOrUse|foo|foo.de')
        self.assertEqual('foo|foo.de', result)

    def test_get_default_from_keep_value_returns_empty_string(self):
        result = ParameterResolver.get_default_from_keep_value('|keepOrUse|')
        self.assertEqual('', result)

    def test_handle_ssm_value_raises_exception_on_invalid_value_format(self):
        with self.assertRaises(CfnSphereException):
            ParameterResolver().handle_ssm_value('|ssm|/test/|invalid')

    def test_resolve_parameter_values_returns_ssm_value(self):
        self.ssm_mock.return_value.get_parameter.return_value = "decryptedValue"

        stack_config = Mock()
        stack_config.parameters = {'foo': '|ssm|/path/to/my/key'}

        result = ParameterResolver().resolve_parameter_values('foo', stack_config)
        self.assertEqual(result, {'foo': 'decryptedValue'})

    def test_resolve_parameter_values_returns_decrypted_value(self):
        self.kms_mock.return_value.decrypt.return_value = "decryptedValue"

        stack_config = Mock()
        stack_config.parameters = {'foo': '|kms|encryptedValue'}

        result = ParameterResolver().resolve_parameter_values('foo', stack_config)
        self.assertEqual(result, {'foo': 'decryptedValue'})

    def test_handle_kms_value_handles_encryption_context_if_set(self):
        self.kms_mock.return_value.decrypt.return_value = "decryptedValue"
        result = ParameterResolver().handle_kms_value('|kms|k=v|encryptedValue')

        self.kms_mock.return_value.decrypt.assert_called_once_with('encryptedValue', encryption_context={'k': 'v'})
        self.assertEqual(result, 'decryptedValue')

    def test_handle_kms_value_ignores_encryption_context_if_not_set(self):
        self.kms_mock.return_value.decrypt.return_value = "decryptedValue"
        result = ParameterResolver().handle_kms_value('|kms|encryptedValue')

        self.kms_mock.return_value.decrypt.assert_called_once_with('encryptedValue')
        self.assertEqual(result, 'decryptedValue')

    def test_handle_kms_value_raises_exception_on_invalid_value_format(self):
        with self.assertRaises(CfnSphereException):
            ParameterResolver().handle_kms_value('|kms|k=v|encryptedValue|something')

    def test_update_parameters_with_cli_parameters_with_string_param_value(self):
        result = ParameterResolver().update_parameters_with_cli_parameters(
            parameters={'foo': "foo"}, cli_parameters={'stack1': {'foo': 'foobar'}}, stack_name='stack1')
        self.assertEqual({'foo': 'foobar'}, result)

    def test_update_parameters_with_cli_parameters_adds_new_cli_parameter(self):
        result = ParameterResolver().update_parameters_with_cli_parameters(parameters={'foo': 'foo'},
                                                                           cli_parameters={
                                                                               'stack1': {'moppel': 'foo'}},
                                                                           stack_name='stack1')
        self.assertDictEqual({'foo': 'foo', 'moppel': 'foo'}, result)

    def test_update_parameters_with_cli_parameters_with_string_param_value_for_several_stacks(self):
        result = ParameterResolver().update_parameters_with_cli_parameters(
            parameters={'foo': "foo"}, cli_parameters={'stack1': {'foo': 'foobar'}, 'stack2': {'foo': 'foofoo'}},
            stack_name='stack2')
        self.assertEqual({'foo': 'foofoo'}, result)

    def test_resolve_parameters_with_cli_parameters_(self):
        cli_parameters = {'stack1': {'foo': 'foobar'}, 'stack2': {'foo': 'foofoo'}}

        stack_config = Mock()
        stack_config.parameters = {'foo': "bar"}

        result = ParameterResolver().resolve_parameter_values("stack1", stack_config, cli_parameters)

        self.assertEqual({'foo': 'foobar'}, result)

    @patch("cfn_sphere.stack_configuration.parameter_resolver.FileLoader.get_file")
    def test_handle_file_value_loads_file_for_simple_file_reference(self, get_file_mock):
        get_file_mock.return_value = "myValue"

        result = ParameterResolver.handle_file_value("|file|s3://myBucket/myParameter.txt", None)

        get_file_mock.assert_called_once_with("s3://myBucket/myParameter.txt", None)
        self.assertEqual("myValue", result)

    @patch("cfn_sphere.stack_configuration.parameter_resolver.FileLoader.get_yaml_or_json_file")
    def test_handle_file_value_loads_file_for_reference_with_pattern(self, get_yaml_or_json_file_mock):
        get_yaml_or_json_file_mock.return_value = {"accounts": [{"id": 1}, {"id": 2}, {"id": 3}]}

        result = ParameterResolver.handle_file_value("|file|s3://myBucket/myAwsAccounts.json|accounts[*].id", None)

        get_yaml_or_json_file_mock.assert_called_once_with("s3://myBucket/myAwsAccounts.json", None)
        self.assertEqual([1, 2, 3], result)

    @patch("cfn_sphere.stack_configuration.parameter_resolver.jmespath.search")
    @patch("cfn_sphere.stack_configuration.parameter_resolver.FileLoader.get_yaml_or_json_file")
    def test_handle_file_value_loads_file_for_reference_with_pattern_containing_pipe(self, f, jmespath_search_mock):
        f.return_value = {"a": "b"}

        ParameterResolver.handle_file_value("|file|s3://myBucket/myAwsAccounts.json|a|b", None)
        jmespath_search_mock.assert_called_once_with("a|b", {'a': 'b'})

    @patch("cfn_sphere.stack_configuration.parameter_resolver.FileLoader.get_yaml_or_json_file")
    def test_handle_file_value_raises_exception_on_invalid_jmespath_pattern_syntax(self, _):
        with self.assertRaises(CfnSphereException):
            ParameterResolver.handle_file_value("|file|path|broken_pattern{}}", None)

    def test_handle_file_value_raises_exception_on_invalid_macro_syntax(self):
        with self.assertRaises(CfnSphereException):
            ParameterResolver.handle_file_value("|file", None)


def test_update_parameters_with_cli_parameters_does_not_affect_other_stacks(self):
    result = ParameterResolver().update_parameters_with_cli_parameters(
        parameters={'foo': "foo"}, cli_parameters={'stack1': {'foo': 'foobar'}}, stack_name='stack2')
    self.assertEqual({'foo': 'foo'}, result)


@patch('cfn_sphere.stack_configuration.parameter_resolver.FileLoader.get_file')
def test_resolve_value_from_file(self, get_file_mock):
    get_file_mock.return_value = "line1\nline2"

    stack_config = Mock()
    stack_config.parameters = {'foo': "|file|abc.txt"}

    result = ParameterResolver().resolve_parameter_values('foo', stack_config)
    self.assertEqual({'foo': 'line1\nline2'}, result)
