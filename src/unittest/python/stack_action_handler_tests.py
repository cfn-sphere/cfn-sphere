try:
    from unittest2 import TestCase
    from mock import patch, Mock, call
except ImportError:
    from unittest import TestCase
    from mock import patch, Mock, call

import six

from cfn_sphere import StackActionHandler
from cfn_sphere.aws.cfn import CloudFormationStack
from cfn_sphere.stack_configuration import PARAMETERS_FOR_ALL_STACKS


class StackActionHandlerTests(TestCase):
    @patch('cfn_sphere.stack_configuration.Config')
    @patch('cfn_sphere.CloudFormation')
    @patch('cfn_sphere.stack_configuration.parameter_resolver.CloudFormation')
    @patch('cfn_sphere.DependencyResolver')
    @patch('cfn_sphere.FileLoader')
    @patch('cfn_sphere.CloudFormationStack')
    @patch('cfn_sphere.CustomResourceHandler')
    def test_merge_parameters_for_all_stacks(self,
                                             custom_resource_mock,
                                             stack_mock,
                                             template_loader_mock,
                                             dependency_resolver_mock,
                                             cfn_mock,
                                             resolver_cfn_mock,
                                             config_mock):
        # Given
        dependency_resolver_mock.return_value.get_stack_order.return_value = ['a']
        cfn_mock.return_value.get_stack_names.return_value = []
        config_mock.return_value.cli_params.return_value = {PARAMETERS_FOR_ALL_STACKS: {'p1': 'v1'},
                                                            "stack2": {"p2": "v2"}
                                                            }

        # When
        handler = StackActionHandler(config_mock)
        handler.create_or_update_stacks()

        # Then
        stack_mock.assert_called_once_with(parameters={'p1': 'v1', "p2": "v23"})

    @patch('cfn_sphere.stack_configuration.Config')
    @patch('cfn_sphere.CloudFormation')
    @patch('cfn_sphere.ParameterResolver')
    @patch('cfn_sphere.DependencyResolver')
    @patch('cfn_sphere.FileLoader')
    @patch('cfn_sphere.CloudFormationStack')
    @patch('cfn_sphere.CustomResourceHandler')
    def test_create_or_update_tests_exits_gracefully_if_preexisting_stack_disappears(self,
                                                                                     custom_resource_mock,
                                                                                     stack_mock,
                                                                                     template_loader_mock,
                                                                                     dependency_resolver_mock,
                                                                                     parameter_resolver_mock,
                                                                                     cfn_mock,
                                                                                     config_mock):

        dependency_resolver_mock.return_value.get_stack_order.return_value = ['a', 'c']
        cfn_mock.return_value.get_stack_names.return_value = ['a', 'd']
        config_mock.return_value.tags.return_value = {}

        stack_a = CloudFormationStack('', [], 'a', '')
        stack_c = CloudFormationStack('', [], 'c', '')

        def stack_side_effect(*args, **kwargs):
            if kwargs['name'] == 'a':
                return stack_a
            if kwargs['name'] == 'c':
                return stack_c
            return None

        stack_mock.side_effect = stack_side_effect

        handler = StackActionHandler(config_mock)
        handler.create_or_update_stacks()

        # stack a needs update
        cfn_mock.return_value.validate_stack_is_ready_for_action.assert_called_once_with(stack_a)
        cfn_mock.return_value.update_stack.assert_called_once_with(stack_a)

        # stack c doesn't exist, must be created
        cfn_mock.return_value.create_stack.assert_called_once_with(stack_c)

    @patch('cfn_sphere.CloudFormation')
    @patch('cfn_sphere.ParameterResolver')
    @patch('cfn_sphere.DependencyResolver')
    @patch('cfn_sphere.FileLoader')
    @patch('cfn_sphere.CloudFormationStack')
    @patch('cfn_sphere.CustomResourceHandler')
    def test_delete_stacks(self,
                           custom_resource_mock,
                           stack_mock,
                           template_loader_mock,
                           dependency_resolver_mock,
                           parameter_resolver_mock,
                           cfn_mock):

        dependency_resolver_mock.return_value.get_stack_order.return_value = ['a', 'c']
        cfn_mock.return_value.get_stack_names.return_value = ['a', 'd']

        stack_a = CloudFormationStack('', [], 'a', '')
        stack_c = CloudFormationStack('', [], 'c', '')

        def stack_side_effect(*args, **kwargs):
            if args[2] == 'a':
                return stack_a
            if args[2] == 'c':
                return stack_c
            return None

        stack_mock.side_effect = stack_side_effect

        handler = StackActionHandler(Mock())
        handler.delete_stacks()

        cfn_mock.return_value.delete_stack.assert_called_once_with(stack_a)

    @patch('cfn_sphere.CloudFormation')
    @patch('cfn_sphere.ParameterResolver')
    @patch('cfn_sphere.DependencyResolver')
    @patch('cfn_sphere.FileLoader')
    @patch('cfn_sphere.CloudFormationStack')
    @patch('cfn_sphere.CustomResourceHandler')
    def test_delete_stacks_uses_the_correct_order(self,
                                                  custom_resource_mock,
                                                  stack_mock,
                                                  template_loader_mock,
                                                  dependency_resolver_mock,
                                                  parameter_resolver_mock,
                                                  cfn_mock):

        dependency_resolver_mock.return_value.get_stack_order.return_value = ['a', 'c']
        cfn_mock.return_value.get_stack_names.return_value = ['a', 'c']

        stack_a = CloudFormationStack('', [], 'a', '')
        stack_c = CloudFormationStack('', [], 'c', '')

        def stack_side_effect(*args, **kwargs):
            if args[2] == 'a':
                return stack_a
            if args[2] == 'c':
                return stack_c
            return None

        stack_mock.side_effect = stack_side_effect

        handler = StackActionHandler(Mock())
        handler.delete_stacks()

        expected_calls = [call(stack_c), call(stack_a)]
        six.assertCountEqual(self, expected_calls, cfn_mock.return_value.delete_stack.mock_calls)
