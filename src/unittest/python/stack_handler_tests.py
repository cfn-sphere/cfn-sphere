__author__ = 'mhoyer'

import unittest2
from cfn_sphere.stack_handler import StackHandler


class StackHandlerTests(unittest2.TestCase):
    def test_convert_list_to_string_returns_string(self):
        self.assertEqual("a,b,c", StackHandler.convert_list_to_string(["a", "b", "c"]))

    def test_convert_list_to_string_returns_empty_string_on_empty_list(self):
        self.assertEqual("", StackHandler.convert_list_to_string([]))

    def test_convert_list_to_string_returns_empty_string_on_none_value(self):
        self.assertEqual("", StackHandler.convert_list_to_string(None))

    def test_convert_list_to_string_returns_single_item(self):
        self.assertEqual("a", StackHandler.convert_list_to_string(["a"]))

    def test_convert_list_to_string_returns_two_items(self):
        self.assertEqual("a,b", StackHandler.convert_list_to_string(["a", "b"]))