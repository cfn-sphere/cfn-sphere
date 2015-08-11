import unittest2


class StackConfigTests(unittest2.TestCase):
    def test_foo(self):
        pass

    STACK_CONFIG = """
stacks:
    stack_a:
        template: foo.json
        region: foo-region
"""
