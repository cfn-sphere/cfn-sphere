from unittest import TestCase

from mock import patch

from cfn_sphere import TemplateHandler
from cfn_sphere.template import CloudFormationTemplate


class TemplateHandlerTests(TestCase):
    @patch("cfn_sphere.template.template_handler.FileLoader")
    @patch("cfn_sphere.template.template_handler.CloudFormationTemplateTransformer")
    @patch("cfn_sphere.template.template_handler.get_git_repository_remote_url")
    def test_get_template_calls_file_handler(self, get_git_repository_remote_url_mock, template_transformer_mock,
                                             file_loader_mock):
        template = CloudFormationTemplate({}, "my-template")
        file_loader_mock.get_cloudformation_template.return_value = template
        get_git_repository_remote_url_mock.return_value = "my-repository-url"

        TemplateHandler.get_template("my-template-url", "my-working-directory")

        file_loader_mock.get_cloudformation_template.assert_called_once_with("my-template-url", "my-working-directory")
        get_git_repository_remote_url_mock.assert_called_once_with("my-working-directory")
        template_transformer_mock.transform_template.assert_called_once_with(template,
                                                                             "Config repo url: my-repository-url")
