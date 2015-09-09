from cfn_sphere.resolver.dependency_resolver import DependencyResolver
from cfn_sphere.resolver.parameter_resolver import ParameterResolver
from cfn_sphere.aws.cloudformation.cfn_api import CloudFormation
from cfn_sphere.aws.cloudformation.template_loader import CloudFormationTemplateLoader
from cfn_sphere.aws.cloudformation.template_transformer import CloudFormationTemplateTransformer
from cfn_sphere.aws.cloudformation.stack import CloudFormationStack
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
            self.logger.info("Will process stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            stack_config = self.config.stacks.get(stack_name)

            template_url = stack_config.template_url
            working_dir = stack_config.working_dir

            template = CloudFormationTemplateLoader.get_template_from_url(template_url, working_dir)
            template = CloudFormationTemplateTransformer.transform_template(template)

            parameters = self.parameter_resolver.resolve_parameter_values(stack_config.parameters, stack_name)

            stack = CloudFormationStack(template, parameters, stack_name, self.region, stack_config.timeout)

            if stack_name in existing_stacks:

                self.cfn.validate_stack_is_ready_for_updates(stack_name)
                self.cfn.update_stack(stack)
            else:
                self.cfn.create_stack(stack)

            CustomResourceHandler.process_post_resources(stack)
