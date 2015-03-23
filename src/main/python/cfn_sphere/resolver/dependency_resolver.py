__author__ = 'mhoyer'

import networkx
from networkx.exception import NetworkXUnfeasible


class DependencyResolver(object):

    @staticmethod
    def get_stack_name_from_ref_value(value):
        assert value, "No value given"
        assert not value.startswith('.'), "Reference value should not start with a dot"
        assert value.__contains__('.'), "Reference value must contain a dot"
        return value.split('.')[0]

    @staticmethod
    def is_parameter_reference(value):
        if not isinstance(value, basestring):
            return False

        if value.lower().startswith("ref::"):
            return True
        else:
            return False

    @staticmethod
    def get_parameter_key_from_ref_value(value):
        if not value:
            return ""

        stripped_value = value.partition('::')[2]
        return stripped_value

    @classmethod
    def create_stacks_directed_graph(cls, desired_stacks):
        graph = networkx.DiGraph()
        for name in desired_stacks:
            graph.add_node(name)
        for name, data in desired_stacks.iteritems():
            if data:
                for key, value in data.get('parameters', {}).iteritems():
                    if cls.is_parameter_reference(value):
                        dependant_stack = cls.get_stack_name_from_ref_value(cls.get_parameter_key_from_ref_value(value))
                        graph.add_edge(dependant_stack, name)

        return graph

    @classmethod
    def get_stack_order(cls, desired_stacks):
        graph = cls.create_stacks_directed_graph(desired_stacks)
        try:
            order = networkx.topological_sort_recursive(graph)
        except NetworkXUnfeasible as e:
            print "Could not define an order of stacks: {0}".format(e)
            raise

        for stack in order:
            if stack not in desired_stacks:
                raise Exception("Stack {0} found in parameter references but it is not defined".format(stack))

        return order


if __name__ == "__main__":
    dr = DependencyResolver()
    print dr.get_stack_order({"mystack1": {"parameters": {"ta": "ref::mystack2.da"}},
                              "mystack2": {"ta": "ref::mystack1.da"}})