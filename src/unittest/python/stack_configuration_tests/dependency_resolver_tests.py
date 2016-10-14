try:
    from unittest2 import TestCase
except ImportError:
    from unittest import TestCase

from cfn_sphere.exceptions import CfnSphereException, CyclicDependencyException
from cfn_sphere.stack_configuration import StackConfig
from cfn_sphere.stack_configuration.dependency_resolver import DependencyResolver

VPC_SG_APP1_APP2 = {'default-sg': StackConfig({'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id'}}),
                   'app1': StackConfig(
                       {'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id'}}),
                   'app2': StackConfig({'template-url': 'horst.yml',
                                        'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id',
                                                       'c': '|Ref|app1.id'}}), 'vpc': StackConfig(
                            {'template-url': 'horst.yml'})}

INDEPENDENT_APPS_INDEPENDENT_VPC_AND_SG = {'default-sg': StackConfig({'template-url': 'horst.yml'}),
                    'app1': StackConfig(
                        {'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id'}}),
                    'app2': StackConfig(
                        {'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id'}}),
                    'vpc': StackConfig({'template-url': 'horst.yml'})}

INDEPENDENT_APPS = {'default-sg': StackConfig({'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id'}}),
                   'app1': StackConfig(
                       {'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id'}}),
                   'app2': StackConfig({'template-url': 'horst.yml',
                                        'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id'}}),
                    'vpc': StackConfig({'template-url': 'horst.yml'})}

THIRD_APP = {'default-sg': StackConfig({'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id'}}),
                   'app1': StackConfig(
                       {'template-url': 'horst.yml', 'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id'}}),
                   'app2': StackConfig({'template-url': 'horst.yml',
                                        'parameters': {'a': '|Ref|vpc.id', 'b': '|Ref|default-sg.id'}}),
                   'vpc': StackConfig({'template-url': 'horst.yml'}),
                   'app3': StackConfig({'template-url': 'horst.yml',
                                        'parameters': {'a': '|Ref|app1.url', 'b': '|Ref|app2.url'}})}


class DependencyResolverTests(TestCase):
    def test_is_parameter_reference_returns_true_for_uppercase_ref(self):
        self.assertTrue(DependencyResolver.is_parameter_reference("|Ref|vpc.id"))

    def test_is_parameter_reference_returns_true_for_all_uppercase_ref(self):
        self.assertTrue(DependencyResolver.is_parameter_reference("|REF|vpc.id"))

    def test_is_parameter_reference_returns_true_for_lowercase_ref(self):
        self.assertTrue(DependencyResolver.is_parameter_reference("|ref|vpc.id"))

    def test_is_parameter_reference_returns_false_for_single_separator(self):
        self.assertFalse(DependencyResolver.is_parameter_reference("Ref|vpc.id"))

    def test_is_parameter_reference_returns_false_for_simple_string(self):
        self.assertFalse(DependencyResolver.is_parameter_reference("vpc.id"))

    def test_is_parameter_reference_returns_false_for_boolean_values(self):
        self.assertFalse(DependencyResolver.is_parameter_reference(True))

    def test_is_parameter_reference_returns_true_on_empty_reference(self):
        self.assertTrue(DependencyResolver.is_parameter_reference('|ref|'))

    def test_get_stack_order_returns_a_valid_order(self):
        expected = ['vpc', 'default-sg', 'app1', 'app2']

        self.assertEqual(expected, DependencyResolver.get_stack_order(VPC_SG_APP1_APP2))

    def test_get_stack_order_includes_independent_stacks(self):
        self.assertEqual(4, len(DependencyResolver.get_stack_order(INDEPENDENT_APPS_INDEPENDENT_VPC_AND_SG)))

    def test_get_stack_order_accepts_stacks_without_parameters_key(self):
        stacks = {'default-sg': {},
                  'app1': None,
                  'app2': {},
                  'vpc': {},
                  }

        result = 4

        self.assertEqual(result, len(DependencyResolver.get_stack_order(stacks)))

    def test_get_stack_order_raises_exception_on_cyclic_dependency(self):
        stacks = {
            'app1': StackConfig({'template-url': 'horst.yml', 'parameters': {'a': '|Ref|app2.id'}}),
            'app2': StackConfig({'template-url': 'horst.yml', 'parameters': {'a': '|Ref|app3.id'}}),
            'app3': StackConfig({'template-url': 'horst.yml', 'parameters': {'a': '|Ref|app1.id'}})
        }

        with self.assertRaises(CyclicDependencyException):
            DependencyResolver.get_stack_order(stacks)

    def test_parallel_execution_order(self):
        executions = DependencyResolver.get_parallel_execution_list(INDEPENDENT_APPS_INDEPENDENT_VPC_AND_SG)

        self.assertIn('default-sg', executions[0].stacks)
        self.assertIn('vpc', executions[0].stacks)
        self.assertEqual(2, len(executions[0].stacks))

        self.assertIn('app1', executions[1].stacks)
        self.assertIn('app2', executions[1].stacks)
        self.assertEqual(2, len(executions[1].stacks))

    def test_parallel_execution_order_without_parallel_execution(self):
        executions = DependencyResolver.get_parallel_execution_list(VPC_SG_APP1_APP2)

        self.assertIn('vpc', executions[0].stacks)
        self.assertEqual(1, len(executions[0].stacks))

        self.assertIn('default-sg', executions[1].stacks)
        self.assertEqual(1, len(executions[1].stacks))

        self.assertIn('app1', executions[2].stacks)
        self.assertEqual(1, len(executions[2].stacks))

        self.assertIn('app2', executions[3].stacks)
        self.assertEqual(1, len(executions[3].stacks))

    def test_parallel_execution_order_with_independent_apps(self):
        executions = DependencyResolver.get_parallel_execution_list(INDEPENDENT_APPS)

        self.assertIn('vpc', executions[0].stacks)
        self.assertEqual(1, len(executions[0].stacks))

        self.assertIn('default-sg', executions[1].stacks)
        self.assertEqual(1, len(executions[1].stacks))

        self.assertIn('app1', executions[2].stacks)
        self.assertIn('app2', executions[2].stacks)
        self.assertEqual(2, len(executions[2].stacks))

    def test_parallel_execution_order_with_third_app_depending_on_two(self):
        executions = DependencyResolver.get_parallel_execution_list(THIRD_APP)

        self.assertIn('vpc', executions[0].stacks)
        self.assertEqual(1, len(executions[0].stacks))

        self.assertIn('default-sg', executions[1].stacks)
        self.assertEqual(1, len(executions[1].stacks))

        self.assertIn('app1', executions[2].stacks)
        self.assertIn('app2', executions[2].stacks)
        self.assertEqual(2, len(executions[2].stacks))

        self.assertIn('app3', executions[3].stacks)
        self.assertEqual(1, len(executions[3].stacks))

    def test_filter_unmanaged_stacks(self):
        stacks = ['a', 'b', 'c']
        managed_stacks = ['a', 'c']

        self.assertListEqual(managed_stacks, DependencyResolver.filter_unmanaged_stacks(managed_stacks, stacks))

    def test_filter_unmanaged_stacks_filters_all_items(self):
        stacks = ['a', 'b', 'c']
        managed_stacks = []
        self.assertListEqual(managed_stacks, DependencyResolver.filter_unmanaged_stacks(managed_stacks, stacks))

    def test_filter_unmanaged_stacks_filters_all_occurences(self):
        stacks = ['a', 'b', 'c', 'c']
        managed_stacks = ['a']
        self.assertListEqual(managed_stacks, DependencyResolver.filter_unmanaged_stacks(managed_stacks, stacks))

    def test_parse_stack_reference_value_returns_none_for_non_reference(self):
        self.assertEqual((None, None), DependencyResolver.parse_stack_reference_value('foo'))

    def test_parse_stack_reference_value_returns_stack_and_output_name_tuple(self):
        self.assertEqual(('stack', 'output'), DependencyResolver.parse_stack_reference_value('|ref|stack.output'))

    def test_parse_stack_reference_raises_exception_on_missing_dot(self):
        with self.assertRaises(CfnSphereException):
            DependencyResolver.parse_stack_reference_value('|ref|foo')

    def test_parse_stack_reference_raises_exception_on_empty_reference(self):
        with self.assertRaises(CfnSphereException):
            DependencyResolver.parse_stack_reference_value('|ref|')
