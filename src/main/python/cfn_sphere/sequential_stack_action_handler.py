from cfn_sphere import get_logger, CloudFormation, DependencyResolver, CloudFormationStack
from cfn_sphere.create_or_update import CreateOrUpdate


class SequentialStackActionHandler(object):
    def __init__(self, config):
        self.logger = get_logger(root=True)
        self.config = config
        self.cfn = CloudFormation(region=self.config.region)

    def create_or_update_stacks(self):
        stack_processing_order = DependencyResolver().get_stack_order(self.config.stacks)

        if len(stack_processing_order) > 1:
            self.logger.info(
                "Will process stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            CreateOrUpdate(stack_name, self.config).run()

    def delete_stacks(self):
        existing_stacks = self.cfn.get_stack_names()
        stack_processing_order = DependencyResolver().get_stack_order(self.config.stacks)
        stack_processing_order.reverse()

        self.logger.info("Will delete stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            if stack_name in existing_stacks:
                stack = CloudFormationStack(None, None, stack_name, None, None)
                self.cfn.validate_stack_is_ready_for_action(stack)
                self.cfn.delete_stack(stack)
            else:
                self.logger.info("Stack {0} is already deleted".format(stack_name))