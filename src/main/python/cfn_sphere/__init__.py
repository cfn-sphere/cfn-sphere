from cfn_sphere.template.template_handler import TemplateHandler
from cfn_sphere.template.transformer import CloudFormationTemplateTransformer
from cfn_sphere.stack_configuration.dependency_resolver import DependencyResolver
from cfn_sphere.stack_configuration.parameter_resolver import ParameterResolver
from cfn_sphere.aws.cfn import CloudFormation
from cfn_sphere.file_loader import FileLoader
from cfn_sphere.aws.cfn import CloudFormationStack
from cfn_sphere.util import get_logger

__version__ = '${version}'


class StackActionHandler(object):
    def __init__(self, config):
        self.logger = get_logger(root=True)
        self.config = config
        self.cfn = CloudFormation(region=self.config.region)
        self.parameter_resolver = ParameterResolver(region=self.config.region)
        self.cli_parameters = config.cli_params
    
    def create_change_set(self):
        existing_stacks = self.cfn.get_stack_names()
        desired_stacks = self.config.stacks
        stack_processing_order = DependencyResolver().get_stack_order(desired_stacks)

        if len(stack_processing_order) > 1:
            self.logger.info(
                "Will process stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            stack_config = self.config.stacks.get(stack_name)

            if stack_config.stack_policy_url:
                self.logger.info("Using stack policy from {0}".format(stack_config.stack_policy_url))
                stack_policy = FileLoader.get_yaml_or_json_file(stack_config.stack_policy_url, stack_config.working_dir)
            else:
                stack_policy = None

            template = TemplateHandler.get_template(stack_config.template_url, stack_config.working_dir)
            parameters = self.parameter_resolver.resolve_parameter_values(stack_name, stack_config, self.cli_parameters)

            stack = CloudFormationStack(template=template,
                                        parameters=parameters,
                                        tags=stack_config.tags,
                                        name=stack_name,
                                        region=self.config.region,
                                        timeout=stack_config.timeout,
                                        service_role=stack_config.service_role,
                                        stack_policy=stack_policy,
                                        failure_action=stack_config.failure_action)

            if stack_name in existing_stacks:
                self.cfn.create_change_set(stack)
            else:
                print('Stack will be created.')
                        

    def create_or_update_stacks(self):
        existing_stacks = self.cfn.get_stack_names()
        desired_stacks = self.config.stacks
        stack_processing_order = DependencyResolver().get_stack_order(desired_stacks)

        if len(stack_processing_order) > 1:
            self.logger.info(
                "Will process stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            stack_config = self.config.stacks.get(stack_name)

            if stack_config.stack_policy_url:
                self.logger.info("Using stack policy from {0}".format(stack_config.stack_policy_url))
                stack_policy = FileLoader.get_yaml_or_json_file(stack_config.stack_policy_url, stack_config.working_dir)
            else:
                stack_policy = None

            template = TemplateHandler.get_template(stack_config.template_url, stack_config.working_dir)
            parameters = self.parameter_resolver.resolve_parameter_values(stack_name, stack_config, self.cli_parameters)

            stack = CloudFormationStack(template=template,
                                        parameters=parameters,
                                        tags=stack_config.tags,
                                        name=stack_name,
                                        region=self.config.region,
                                        timeout=stack_config.timeout,
                                        service_role=stack_config.service_role,
                                        stack_policy=stack_policy,
                                        failure_action=stack_config.failure_action)

            if stack_name in existing_stacks:

                self.cfn.validate_stack_is_ready_for_action(stack)
                self.cfn.update_stack(stack)
            else:
                self.cfn.create_stack(stack)

    def delete_stacks(self):
        existing_stacks = self.cfn.get_stack_names()
        stacks = self.config.stacks

        stack_processing_order = DependencyResolver().get_stack_order(stacks)
        stack_processing_order.reverse()

        self.logger.info("Will delete stacks in the following order: {0}".format(", ".join(stack_processing_order)))

        for stack_name in stack_processing_order:
            stack_config = self.config.stacks.get(stack_name)

            if stack_name in existing_stacks:
                stack = CloudFormationStack(None, None, stack_name, None, None, service_role=stack_config.service_role)
                self.cfn.validate_stack_is_ready_for_action(stack)
                self.cfn.delete_stack(stack)
            else:
                self.logger.info("Stack {0} is already deleted".format(stack_name))
