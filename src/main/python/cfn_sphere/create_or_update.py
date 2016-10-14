from threading import Thread

from cfn_sphere import CloudFormation, ParameterResolver, get_logger, FileLoader, CloudFormationTemplateTransformer, \
    CloudFormationStack, CustomResourceHandler


class CreateOrUpdate(Thread):
    def __init__(self, stack_name, config):
        self.stack_name = stack_name
        self.config = config
        self.cfn = CloudFormation(region=self.config.region)
        self.parameter_resolver = ParameterResolver(region=self.config.region)
        self.logger = get_logger(root=True)
        self.exception = None
        super(CreateOrUpdate, self).__init__(name=stack_name)

    # def run(self):
    #     try:
    #         self.run_synchronously()
    #     except Exception as e:
    #         self.exception = e

    def run(self):
        stack_config = self.config.stacks.get(self.stack_name)
        template = FileLoader.get_cloudformation_template(stack_config.template_url,
                                                          stack_config.working_dir)
        transformed_template = CloudFormationTemplateTransformer.transform_template(template)

        parameters = self.parameter_resolver.resolve_parameter_values(self.stack_name, stack_config)
        merged_parameters = self.parameter_resolver.update_parameters_with_cli_parameters(
            parameters=parameters,
            cli_parameters=self.config.cli_params,
            stack_name=self.stack_name)
        self.logger.debug("Parameters after merging with cli options: {0}".format(merged_parameters))

        stack = CloudFormationStack(template=transformed_template,
                                    parameters=merged_parameters,
                                    tags=self.config.tags,
                                    name=self.stack_name,
                                    region=self.config.region,
                                    timeout=stack_config.timeout)

        if self.stack_name in self.cfn.get_stack_names():
            self.cfn.validate_stack_is_ready_for_action(stack)
            self.cfn.update_stack(stack)
        else:
            self.cfn.create_stack(stack)

        CustomResourceHandler.process_post_resources(stack)