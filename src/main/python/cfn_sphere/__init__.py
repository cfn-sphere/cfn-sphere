__version__ = '${version}'

from cfn_sphere.template.transformer import CloudFormationTemplateTransformer
from cfn_sphere.stack_configuration.dependency_resolver import DependencyResolver
from cfn_sphere.stack_configuration.parameter_resolver import ParameterResolver
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.template.loader import CloudFormationTemplateLoader
from cfn_sphere.aws.cfn import CloudFormationStack
from cfn_sphere.custom_resources import CustomResourceHandler
from cfn_sphere.util import get_logger


class StackActionHandler(object):
    def __init__(self, config):
        self.logger = get_logger()
        self.config = config
        self.region = config.region
        self.cfn = CloudFormation(region=self.region)
        self.parameter_resolver = ParameterResolver(region=self.region)

    def create_or_update_stacks(self):
        existing_stacks = self.cfn.get_stack_names()
        desired_stacks = self.config.stacks
        stack_processing_order = DependencyResolver().get_stack_order(desired_stacks)

        if len(stack_processing_order) > 1:
            self.logger.info(
                "Will create/update stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            stack_config = self.config.stacks.get(stack_name)

            template_url = stack_config.template_url
            working_dir = stack_config.working_dir

            raw_template = CloudFormationTemplateLoader.get_template_from_url(template_url, working_dir)
            template = CloudFormationTemplateTransformer.transform_template(raw_template)

            parameters = self.parameter_resolver.resolve_parameter_values(stack_config.parameters, stack_name)
            stack = CloudFormationStack(template, parameters, stack_name, self.region, stack_config.timeout)

            if stack_name in existing_stacks:

                self.cfn.validate_stack_is_ready_for_action(stack)
                self.cfn.update_stack(stack)
            else:
                self.cfn.create_stack(stack)

            CustomResourceHandler.process_post_resources(stack)

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