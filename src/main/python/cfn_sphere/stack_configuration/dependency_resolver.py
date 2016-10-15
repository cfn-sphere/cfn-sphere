import networkx
from networkx.exception import NetworkXUnfeasible, NetworkXNoCycle

from cfn_sphere.exceptions import CfnSphereException, InvalidDependencyGraphException, CyclicDependencyException


class Execution(object):
    def __init__(self):
        self.stacks = set()

    def __repr__(self):
        return "ConcurrentExecution[%s]" % ", ".join(self.stacks)


class Executions(list):
    def get(self, index):
        while index >= len(self):
            self.append(Execution())
        return self[index]


class DependencyResolver(object):
    @staticmethod
    def parse_stack_reference_value(value):
        if not value:
            return None, None

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
            return None, None

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
                for _, value in data.parameters.items():
                    if isinstance(value, list):
                        for item in value:
                            if cls.is_parameter_reference(item):
                                dependant_stack, _ = cls.parse_stack_reference_value(item)
                                graph.add_edge(dependant_stack, name)
                    elif cls.is_parameter_reference(value):
                        dependant_stack, _ = cls.parse_stack_reference_value(value)
                        graph.add_edge(dependant_stack, name)

        return graph

    @staticmethod
    def filter_unmanaged_stacks(managed_stacks, stacks):
        return [stack for stack in stacks if stack in managed_stacks]

    @staticmethod
    def analyse_cyclic_dependencies(graph):
        try:
            cycle = networkx.find_cycle(graph)
            dependency_string = ' => '.join("[%s is referenced by %s]" % tup for tup in cycle)
            raise CyclicDependencyException("Found cyclic dependency between stacks: {0}".format(dependency_string))
        except NetworkXNoCycle:
            pass

    @classmethod
    def get_stack_order(cls, desired_stacks):
        (order, _) = cls.get_stack_order_with_graph(desired_stacks)
        return order

    @classmethod
    def get_stack_order_with_graph(cls, desired_stacks):
        graph = cls.create_stacks_directed_graph(desired_stacks)
        try:
            order = networkx.topological_sort_recursive(graph)
        except NetworkXUnfeasible as e:
            cls.analyse_cyclic_dependencies(graph)
            raise InvalidDependencyGraphException("Could not define an order of stacks: {0}".format(e))

        return cls.filter_unmanaged_stacks(desired_stacks, order), graph

    @classmethod
    def get_parallel_execution_list(cls, stacks):
        (order, graph) = cls.get_stack_order_with_graph(stacks)

        executions = Executions()

        for stack in order:
            if graph.in_degree(stack) == 0:
                executions.get(0).stacks.add(stack)
            else:
                last_predecessor = 0
                for pre in graph.predecessors(stack):
                    for i in range(0, len(executions)):
                        if pre in executions[i].stacks and i > last_predecessor:
                            last_predecessor = i

                executions.get(last_predecessor + 1).stacks.add(stack)

        return executions


if __name__ == "__main__":
    stacks = ['a', 'b', 'c']
    managed_stacks = []
    print(DependencyResolver.filter_unmanaged_stacks(managed_stacks, stacks))
