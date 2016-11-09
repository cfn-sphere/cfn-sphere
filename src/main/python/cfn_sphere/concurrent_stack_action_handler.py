from cfn_sphere import get_logger, CloudFormation, DependencyResolver, CloudFormationStack
from cfn_sphere.create_or_update import CreateOrUpdate


class ConcurrentStackActionHandler(object):

    def __init__(self, config):
        self.logger = get_logger(root=True)
        self.config = config
        self.cfn = CloudFormation(region=self.config.region)

    def create_or_update_stacks(self):
        executions = DependencyResolver().get_parallel_execution_list(self.config.stacks)

        self.logger.info(
            "Will process stacks in the following order: {0}".format(", ".join(str(exc) for exc in executions)))

        for execution in executions:
            threads = []
            for stack_name in execution.stacks:
                thread = CreateOrUpdate(stack_name, self.config)
                thread.start()
                threads.append(thread)

            [thread.join() for thread in threads]

    def delete_stacks(self):
        existing_stacks = self.cfn.get_stack_names()
        stacks = self.config.stacks

        stack_processing_order = DependencyResolver().get_stack_order(stacks)
        stack_processing_order.reverse()

        self.logger.info("Will delete stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            if stack_name in existing_stacks:
                stack = CloudFormationStack(None, None, stack_name, None, None)
                self.cfn.validate_stack_is_ready_for_action(stack)
                self.cfn.delete_stack(stack)
            else:
                self.logger.info("Stack {0} is already deleted".format(stack_name))


