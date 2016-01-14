import json


class CloudFormationTemplate(object):
    def __init__(self, body_dict, name):
        self.name = name
        self.template_format_version = body_dict.get('AWSTemplateFormatVersion', '2010-09-09')
        self.description = body_dict.get('Description', '')
        self.metadata = body_dict.get('Metadata', {})
        self.parameters = body_dict.get('Parameters', {})
        self.mappings = body_dict.get('Mappings', {})
        self.conditions = body_dict.get('Conditions', {})
        self.resources = body_dict.get('Resources', {})
        self.outputs = body_dict.get('Outputs', {})
        self.post_custom_resources = body_dict.get('PostCustomResources', {})

    def get_no_echo_parameter_keys(self):
        if self.parameters:
            return [key for key, value in self.parameters.items() if str(value.get('NoEcho')).lower() == 'true']
        else:
            return []

    def get_template_body_dict(self):
        return {
            'AWSTemplateFormatVersion': self.template_format_version,
            'Description': self.description,
            'Parameters': self.parameters,
            'Mappings': self.mappings,
            'Conditions': self.conditions,
            'Resources': self.resources,
            'Outputs': self.outputs
        }

    def get_template_json(self):
        return json.dumps(self.get_template_body_dict(), indent=2)
