import unittest2

from cfn_sphere.resolver.dependency_resolver import DependencyResolver
from cfn_sphere.config import StackConfig


class DependencyResolverTests(unittest2.TestCase):
    def test_get_parameter_key_from_ref_value_returns_valid_key(self):
        self.assertEqual("vpc.id", DependencyResolver.get_parameter_key_from_ref_value("Ref::vpc.id"))

    def test_get_parameter_key_from_ref_value_returns_key_on_lowercase_ref(self):
        self.assertEqual("vpc.id", DependencyResolver.get_parameter_key_from_ref_value("ref::vpc.id"))

    def test_get_parameter_key_from_ref_value_returns_empty_string_on_single_separator(self):
        self.assertEqual("", DependencyResolver.get_parameter_key_from_ref_value("Ref:vpc.id"))

    def test_get_parameter_key_from_ref_value_returns_empty_string_on_invalid_ref_value(self):
        self.assertEqual("", DependencyResolver.get_parameter_key_from_ref_value("Ref:vpc.id"))

    def test_get_parameter_key_from_ref_value_returns_empty_string_if_none(self):
        self.assertEqual(None, DependencyResolver.get_parameter_key_from_ref_value(None))

    def test_is_ref_value_returns_true_for_uppercase_ref(self):
        self.assertTrue(DependencyResolver.is_parameter_reference("Ref::vpc.id"))

    def test_is_ref_value_returns_true_for_all_uppercase_ref(self):
        self.assertTrue(DependencyResolver.is_parameter_reference("REF::vpc.id"))

    def test_is_ref_value_returns_true_for_lowercase_ref(self):
        self.assertTrue(DependencyResolver.is_parameter_reference("ref::vpc.id"))

    def test_is_ref_value_returns_false_for_single_separator(self):
        self.assertFalse(DependencyResolver.is_parameter_reference("Ref:vpc.id"))

    def test_is_ref_value_returns_false_for_simple_string(self):
        self.assertFalse(DependencyResolver.is_parameter_reference("vpc.id"))

    def test_is_ref_value_returns_false_for_simple_string_with_separator(self):
        self.assertFalse(DependencyResolver.is_parameter_reference("test::vpc.id"))

    def test_is_ref_value_returns_true_for_empty_ref_value(self):
        self.assertTrue(DependencyResolver.is_parameter_reference("Ref::"))

    def test_is_ref_value_returns_false_for_boolean_values(self):
        self.assertFalse(DependencyResolver.is_parameter_reference(True))

    def test_get_stack_order_returns_a_valid_order(self):
        stacks = {'default-sg': StackConfig({'parameters': {'a': 'Ref::vpc.id'}}),
                  'app1': StackConfig({'parameters': {'a': 'Ref::vpc.id', 'b': 'Ref::default-sg.id'}}),
                  'app2': StackConfig(
                      {'parameters': {'a': 'Ref::vpc.id', 'b': 'Ref::default-sg.id', 'c': 'Ref::app1.id'}}),
                  'vpc': StackConfig(
                      {'parameters': {'logBucketName': 'is24-cloudtrail-logs', 'includeGlobalServices': False}})
                  }

        result = ['vpc', 'default-sg', 'app1', 'app2']

        self.assertEqual(result, DependencyResolver.get_stack_order(stacks))

    def test_get_stack_order_includes_independent_stacks(self):
        stacks = {'default-sg': StackConfig({}),
                  'app1': StackConfig({'parameters': {'a': 'Ref::vpc.id', 'b': 'Ref::default-sg.id'}}),
                  'app2': StackConfig(
                      {'parameters': {'a': 'Ref::vpc.id', 'b': 'Ref::default-sg.id', 'c': 'Ref::app1.id'}}),
                  'vpc': StackConfig(
                      {'parameters': {'logBucketName': 'is24-cloudtrail-logs', 'includeGlobalServices': False}})
                  }

        result = 4

        self.assertEqual(result, len(DependencyResolver.get_stack_order(stacks)))

    def test_get_stack_order_accepts_stacks_without_parameters_key(self):
        stacks = {'default-sg': {},
                  'app1': None,
                  'app2': {},
                  'vpc': {},
                  }

        result = 4

        self.assertEqual(result, len(DependencyResolver.get_stack_order(stacks)))

    def test_get_stack_order_raises_exception_on_cyclic_dependency(self):
        stacks = {'app1': {'parameters': {'a': 'Ref::app2.id'}},
                  'app2': {'parameters': {'a': 'Ref::app1.id'}}
                  }
        with self.assertRaises(Exception):
            DependencyResolver.get_stack_order(stacks)

    def test_get_stack_name_from_ref_value_returns_stack_name(self):
        self.assertEqual("a", DependencyResolver.get_stack_name_from_ref_value("a.b"))

    def test_get_stack_name_from_ref_value_raises_exception_if_dot_is_missing(self):
        with self.assertRaises(AssertionError):
            self.assertEqual("a", DependencyResolver.get_stack_name_from_ref_value("ab"))

    def test_get_stack_name_from_ref_value_raises_exception_if_value_starts_with_dot(self):
        with self.assertRaises(AssertionError):
            self.assertEqual("a", DependencyResolver.get_stack_name_from_ref_value(".ab"))

    def test_get_stack_name_from_ref_value_raises_exception_for_empty_value(self):
        with self.assertRaises(AssertionError):
            self.assertEqual("", DependencyResolver.get_stack_name_from_ref_value(""))

    def test_get_stack_name_from_ref_value_raises_exception_for_none_value(self):
        with self.assertRaises(AssertionError):
            self.assertEqual("", DependencyResolver.get_stack_name_from_ref_value(None))

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