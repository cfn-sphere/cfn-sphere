from unittest import TestCase
from unittest.mock import call

import six
from mock import patch, Mock

from cfn_sphere import StackActionHandler
from cfn_sphere.aws.cfn import CloudFormationStack


class StackActionHandlerTests(TestCase):
    @patch('cfn_sphere.CloudFormation')
    @patch('cfn_sphere.ParameterResolver')
    @patch('cfn_sphere.DependencyResolver')
    @patch('cfn_sphere.FileLoader')
    @patch('cfn_sphere.CloudFormationStack')
    def test_delete_stacks(self,
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
            if kwargs["name"] == 'a':
                return stack_a
            if kwargs["name"] == 'c':
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
    def test_delete_stacks_uses_the_correct_order(self,
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
            if kwargs["name"] == 'a':
                return stack_a
            if kwargs["name"] == 'c':
                return stack_c
            return None

        stack_mock.side_effect = stack_side_effect

        handler = StackActionHandler(Mock())
        handler.delete_stacks()

        expected_calls = [call(stack_c), call(stack_a)]
        six.assertCountEqual(self, expected_calls, cfn_mock.return_value.delete_stack.mock_calls)
