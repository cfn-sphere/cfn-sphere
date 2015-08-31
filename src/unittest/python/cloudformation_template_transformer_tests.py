import unittest2
from cfn_sphere.aws.cloudformation.template_transformer import CloudFormationTemplateTransformer
from cfn_sphere.exceptions import TemplateErrorException
from mock import Mock, mock


class CloudFormationTemplateTransformerTests(unittest2.TestCase):

    def test_transform_dict_values_executes_value_handler_for_all_matching_prefixes(self):
        dictionary = {'a': 'foo123', 'b': {'c': 'foo234'}}
        handler = Mock()
        handler.return_value = "foo"

        result = CloudFormationTemplateTransformer.transform_dict_values(dictionary, handler)
        expected_calls = [mock.call('foo123'), mock.call('foo234')]

        self.assertListEqual(expected_calls, handler.mock_calls)
        self.assertEqual(result, {'a': 'foo', 'b': {'c': 'foo'}})

    def test_transform_reference_string_creates_valid_cfn_reference(self):
        result = CloudFormationTemplateTransformer.transform_reference_string('|ref|my-value')
        self.assertEqual({'Ref': 'my-value'}, result)

    def test_transform_reference_string_ignores_value_without_reference(self):
        result = CloudFormationTemplateTransformer.transform_reference_string('my-value')
        self.assertEqual('my-value', result)

    def test_transform_reference_string_raises_exception_on_empty_reference(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_reference_string('|ref|')

    def test_transform_reference_string_ignores_none_values(self):
        result = CloudFormationTemplateTransformer.transform_reference_string(None)
        self.assertEqual(None, result)

    def test_transform_reference_string_ignores_empty_strings(self):
        result = CloudFormationTemplateTransformer.transform_reference_string('')
        self.assertEqual('', result)

    def test_transform_getattr_string_creates_valid_cfn_getattr(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string('|getatt|resource|attribute')
        self.assertEqual({'Fn::GetAtt': ['resource','attribute' ]}, result)

    def test_transform_getattr_string_raises_exception_on_missing_resource(self):
        with self.assertRaises(TemplateErrorException):
            CloudFormationTemplateTransformer.transform_getattr_string('|getatt|attribute')

    def test_transform_getattr_string_ignores_none_values(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string(None)
        self.assertEqual(None, result)

    def test_transform_getattr_string_ignores_empty_strings(self):
        result = CloudFormationTemplateTransformer.transform_getattr_string('')
        self.assertEqual('', result)