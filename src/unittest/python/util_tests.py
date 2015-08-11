import textwrap
import unittest2
from cfn_sphere.util import convert_yaml_to_json_string, convert_json_to_yaml_string


class StackConfigTests(unittest2.TestCase):
    def test_convert_yaml_to_json_string_returns_valid_json_string(self):
        data = textwrap.dedent("""
        foo:
          foo: baa
        """)

        self.assertEqual('{\n    "foo": {\n        "foo": "baa"\n    }\n}', convert_yaml_to_json_string(data))

    def test_convert_yaml_to_json_string_returns_valid_json_string_on_empty_string_input(self):
        data = ""
        self.assertEqual('{}', convert_yaml_to_json_string(data))

    def test_convert_json_to_yaml_string_returns_valid_yaml_string(self):
        data = textwrap.dedent("""
        {
            "foo": {
                "foo": "baa"
            }
        }
        """)

        self.assertEqual('foo:\n  foo: baa\n', convert_json_to_yaml_string(data))

    def test_convert_json_to_yaml_string_returns_empty_string_on_empty_json_input(self):
        data = {}
        self.assertEqual('', convert_json_to_yaml_string(data))