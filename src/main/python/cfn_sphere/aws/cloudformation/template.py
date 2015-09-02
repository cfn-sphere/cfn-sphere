import json
from cfn_sphere.util import get_logger


class CloudFormationTemplate(object):
    def __init__(self, body_dict, name):
        self.logger = get_logger()
        self.name = name
        self.body_dict = body_dict
        self.template_format_version = body_dict.get('AWSTemplateFormatVersion', "2010-09-09")
        self.description = body_dict.get('Description', "")
        self.parameters = body_dict.get('Parameters', {})
        self.resources = body_dict.get('Resources', {})
        self.outputs = body_dict.get('Outputs', {})
        self.post_custom_resources = body_dict.get('PostCustomResources', {})

    def get_template_body_dict(self):
        return {
            'AWSTemplateFormatVersion': self.template_format_version,
            'Description': self.description,
            'Parameters': self.parameters,
            'Resources': self.resources,
            'Outputs': self.outputs
        }

    def get_template_json(self):
        return json.dumps(self.get_template_body_dict(), indent=2)
