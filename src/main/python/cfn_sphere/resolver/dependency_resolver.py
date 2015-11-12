import networkx
from networkx.exception import NetworkXUnfeasible
from cfn_sphere.exceptions import CfnSphereException


class DependencyResolver(object):

    @staticmethod
    def parse_stack_reference_value(value):
        if not value:
            return None

        if value.lower().startswith('|ref|'):
            components = value.split('|')
            if len(components) != 3:
                raise CfnSphereException("Stack output reference must be like '|ref|stack.output'")

            reference = components[2]

            reference_components = reference.split('.')
            if len(reference_components) != 2:
                raise CfnSphereException("Stack output reference must be like '|ref|stack.output'")

            stack_name = reference_components[0]
            output_name = reference_components[1]

            return stack_name, output_name
        else:
            return None

    @staticmethod
    def is_parameter_reference(value):
        if not isinstance(value, str):
            return False

        if value.lower().startswith("|ref|"):
            return True
        else:
            return False

    @classmethod
    def create_stacks_directed_graph(cls, desired_stacks):
        graph = networkx.DiGraph()
        for name in desired_stacks.keys():
            graph.add_node(name)
        for name, data in desired_stacks.items():
            if data:
                for key, value in data.parameters.items():
                    if cls.is_parameter_reference(value):
                        dependant_stack, _ = cls.parse_stack_reference_value(value)
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
