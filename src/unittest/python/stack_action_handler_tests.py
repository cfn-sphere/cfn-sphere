try:
    from unittest2 import TestCase
    from mock import patch, Mock, call
except ImportError:
    from unittest import TestCase
    from mock import patch, Mock, call

import six

from cfn_sphere.sequential_stack_action_handler import SequentialStackActionHandler
from cfn_sphere.aws.cfn import CloudFormationStack


class StackActionHandlerTests(TestCase):
    @patch('cfn_sphere.stack_configuration.Config')
    @patch('cfn_sphere.sequential_stack_action_handler.CloudFormation')
    @patch('cfn_sphere.sequential_stack_action_handler.DependencyResolver')
    @patch('cfn_sphere.sequential_stack_action_handler.CreateOrUpdate')
    def test_create_or_update_tests(self,
                                    create_or_update_mock,
                                    dependency_resolver_mock,
                                    cfn_mock,
                                    config_mock):

        dependency_resolver_mock.return_value.get_stack_order.return_value = ['a', 'c']

        handler = SequentialStackActionHandler(config_mock)
        handler.create_or_update_stacks()

        self.assertEqual([call('a', config_mock), call('c', config_mock)], create_or_update_mock.call_args_list)

    @patch('cfn_sphere.sequential_stack_action_handler.CloudFormation')
    @patch('cfn_sphere.sequential_stack_action_handler.DependencyResolver')
    @patch('cfn_sphere.sequential_stack_action_handler.CloudFormationStack')
    def test_delete_stacks(self,
                           stack_mock,
                           dependency_resolver_mock,
                           cfn_mock):

        dependency_resolver_mock.return_value.get_stack_order.return_value = ['a', 'c']
        cfn_mock.return_value.get_stack_names.return_value = ['a', 'd']

        stack_a = CloudFormationStack('', [], 'a', '')
        stack_c = CloudFormationStack('', [], 'c', '')

        def stack_side_effect(*args):
            if args[2] == 'a':
                return stack_a
            if args[2] == 'c':
                return stack_c
            return None

        stack_mock.side_effect = stack_side_effect

        handler = SequentialStackActionHandler(Mock())
        handler.delete_stacks()

        cfn_mock.return_value.delete_stack.assert_called_once_with(stack_a)

    @patch('cfn_sphere.sequential_stack_action_handler.CloudFormation')
    @patch('cfn_sphere.sequential_stack_action_handler.DependencyResolver')
    @patch('cfn_sphere.sequential_stack_action_handler.CloudFormationStack')
    def test_delete_stacks_uses_the_correct_order(self,
                                                  stack_mock,
                                                  dependency_resolver_mock,
                                                  cfn_mock):

        dependency_resolver_mock.return_value.get_stack_order.return_value = ['a', 'c']
        cfn_mock.return_value.get_stack_names.return_value = ['a', 'c']

        stack_a = CloudFormationStack('', [], 'a', '')
        stack_c = CloudFormationStack('', [], 'c', '')

        def stack_side_effect(*args):
            if args[2] == 'a':
                return stack_a
            if args[2] == 'c':
                return stack_c
            return None

        stack_mock.side_effect = stack_side_effect

        handler = SequentialStackActionHandler(Mock())
        handler.delete_stacks()

        expected_calls = [call(stack_c), call(stack_a)]
        six.assertCountEqual(self, expected_calls, cfn_mock.return_value.delete_stack.mock_calls)
