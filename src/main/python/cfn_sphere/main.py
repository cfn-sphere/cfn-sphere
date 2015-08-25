from cfn_sphere.resolver.dependency_resolver import DependencyResolver
from cfn_sphere.resolver.parameter_resolver import ParameterResolver
from cfn_sphere.cloudformation.api import CloudFormation, CloudFormationTemplate
from cfn_sphere.util import get_logger



class StackActionHandler(object):
    def __init__(self, config, working_dir, user_input_handler=None):
        self.working_dir = working_dir
        self.logger = get_logger()
        self.config = config
        self.region = config.region
        self.cfn = CloudFormation(region=self.region)
        self.parameter_resolver = ParameterResolver(region=self.region)
        self.user_input_handler = user_input_handler

    def create_or_update_stacks(self):
        existing_stacks = self.cfn.get_stack_names()
        desired_stacks = self.config.stacks
        stack_processing_order = DependencyResolver().get_stack_order(desired_stacks)

        self.logger.info("Will process stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            stack_config = self.config.stacks.get(stack_name)

            template_url = stack_config.template
            template = CloudFormationTemplate(template_url, working_dir=self.working_dir)

            parameters = self.parameter_resolver.resolve_parameter_values(stack_config.parameters)

            if stack_name in existing_stacks:

                self.cfn.validate_stack_is_ready_for_updates(stack_name)
                self.cfn.update_stack(stack_name=stack_name, template=template, parameters=parameters)
            else:
                self.cfn.create_stack(stack_name=stack_name, template=template, parameters=parameters)
