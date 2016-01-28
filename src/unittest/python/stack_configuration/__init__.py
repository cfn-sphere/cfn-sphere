from cfn_sphere.stack_configuration import Config
from cfn_sphere.exceptions import BadConfigException


def test_parse_parameters_parsing_cli_params(self):
    self.assertEqual(cmp(Config._split_parameters_by_stack("stack1:p1=v1,stack1:p2=v2"),
                         {'stack1': {'p1': 'v1', 'p2': 'v2'}}), 0)


def test_parse_parameters_parsing_invalid_cli_params_throws_exception(self):
    with self.assertRaises(BadConfigException):
        Config._split_parameters_by_stack("foobar")


def test_split_parameters_by_stack(self):
    self.assertEqual(cmp(Config._split_parameters_by_stack("stack1:p1=v1,stack1:p2=v2,stack2:p1=v1"),
                         {'stack1': {'p1': 'v1', 'p2': 'v2'}, 'stack2': {'p1': 'v1'}}), 0)