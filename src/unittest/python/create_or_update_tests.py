from cfn_sphere import CloudFormationStack
from cfn_sphere.create_or_update import CreateOrUpdate
from cfn_sphere.stack_configuration import StackConfig, Config
from cfn_sphere.template import CloudFormationTemplate

try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase

from mock import patch, Mock

stack_config = {'template-url': 'template.yaml'}
config_dict = {
    'region': 'eu-west-1',
    'stacks': {
        'stack1': stack_config
    }
}
config = Config(config_dict=config_dict)

template = CloudFormationTemplate({}, "name")


class CreateOrUpdateTests(TestCase):
    @patch('cfn_sphere.create_or_update.FileLoader')
    @patch('cfn_sphere.create_or_update.ParameterResolver')
    @patch('cfn_sphere.create_or_update.CloudFormation')
    def test_create(self, cloud_formation_mock, parameter_resolver_mock, file_loader_mock):
        file_loader_mock.get_transformed_cloudformation_template.return_value = template
        resolve_parameter_values_mock = Mock()
        parameter_resolver_mock.return_value = resolve_parameter_values_mock
        resolve_parameter_values_mock.resolve_parameter_values.return_value = {}

        CreateOrUpdate('stack1', config).run()

        file_loader_mock.get_transformed_cloudformation_template.assert_called_with('template.yaml', None)
        resolve_parameter_values_mock.resolve_parameter_values.assert_called_with('stack1',
                                                                                  StackConfig(
                                                                                      stack_config_dict=stack_config),
                                                                                  {})
        cloud_formation_mock.return_value.create_stack.assert_called_with(
            CloudFormationStack(template, {}, 'stack1', 'eu-west-1'))

    @patch('cfn_sphere.create_or_update.FileLoader')
    @patch('cfn_sphere.create_or_update.ParameterResolver')
    @patch('cfn_sphere.create_or_update.CloudFormation')
    def test_update(self, cloud_formation_mock, parameter_resolver_mock, file_loader_mock):
        file_loader_mock.get_transformed_cloudformation_template.return_value = template
        resolve_parameter_values_mock = Mock()
        parameter_resolver_mock.return_value = resolve_parameter_values_mock
        resolve_parameter_values_mock.resolve_parameter_values.return_value = {}
        cloud_formation_mock.return_value.get_stack_names.return_value = ['stack1']

        CreateOrUpdate('stack1', config).run()

        file_loader_mock.get_transformed_cloudformation_template.assert_called_with('template.yaml', None)
        resolve_parameter_values_mock.resolve_parameter_values.assert_called_with('stack1',
                                                                                  StackConfig(
                                                                                      stack_config_dict=stack_config),
                                                                                  {})
        stack = CloudFormationStack(template, {}, 'stack1', 'eu-west-1')
        cloud_formation_mock.return_value.validate_stack_is_ready_for_action.assert_called_with(stack)
        cloud_formation_mock.return_value.update_stack.assert_called_with(stack)
