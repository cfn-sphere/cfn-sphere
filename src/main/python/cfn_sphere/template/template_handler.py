from cfn_sphere.file_loader import FileLoader
from cfn_sphere.template.transformer import CloudFormationTemplateTransformer
from cfn_sphere.util import get_git_repository_remote_url


class TemplateHandler(object):
    @staticmethod
    def get_template(template_url, working_dir):
        template = FileLoader.get_cloudformation_template(template_url, working_dir)
        additional_stack_description = "Config repo url: {0}".format(get_git_repository_remote_url(working_dir))
        return CloudFormationTemplateTransformer.transform_template(template, additional_stack_description)
