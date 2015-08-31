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
        if not isinstance(value, str):
            return False

        if value.lower().startswith("|ref|"):
            return True
        else:
            return False

    @staticmethod
    def get_parameter_key_from_ref_value(value):
        if not value:
            return None
        components = value.split('|')
        if len(components) == 3:
            return components[2]
        else:
            return ""

    @classmethod
    def create_stacks_directed_graph(cls, desired_stacks):
        graph = networkx.DiGraph()
        for name in desired_stacks.keys():
            graph.add_node(name)
        for name, data in desired_stacks.items():
            if data:
                for key, value in data.parameters.items():
                    if cls.is_parameter_reference(value):
                        dependant_stack = cls.get_stack_name_from_ref_value(cls.get_parameter_key_from_ref_value(value))
                        graph.add_edge(dependant_stack, name)

        return graph

    @staticmethod
    def filter_unmanaged_stacks(managed_stacks, stacks):
        return [stack for stack in stacks if stack in managed_stacks]

    @classmethod
    def get_stack_order(cls, desired_stacks):
        graph = cls.create_stacks_directed_graph(desired_stacks)
        try:
            order = networkx.topological_sort_recursive(graph)
        except NetworkXUnfeasible as e:
            raise Exception("Could not define an order of stacks: {0}".format(e))

        return cls.filter_unmanaged_stacks(desired_stacks, order)


if __name__ == "__main__":
    stacks = ['a', 'b', 'c']
    managed_stacks = []
    print DependencyResolver.filter_unmanaged_stacks(managed_stacks, stacks)
