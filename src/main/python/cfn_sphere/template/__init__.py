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
        self.transform = body_dict.get('Transform', {})
        self.resources = body_dict.get('Resources', {})
        self.outputs = body_dict.get('Outputs', {})

    def get_no_echo_parameter_keys(self):
        if self.parameters:
            return [key for key, value in self.parameters.items() if str(value.get('NoEcho')).lower() == 'true']
        else:
            return []

    def get_template_body_dict(self):
        body_dict = {
            'AWSTemplateFormatVersion': self.template_format_version,
            'Description': self.description,
            'Metadata': self.metadata,
            'Parameters': self.parameters,
            'Mappings': self.mappings,
            'Conditions': self.conditions,
            'Resources': self.resources,
            'Outputs': self.outputs
        }

        if self.transform:
            body_dict['Transform'] = self.transform

        return body_dict

    def get_pretty_template_json(self):
        return json.dumps(self.get_template_body_dict(), indent=2)

    def get_template_json(self):
        return json.dumps(self.get_template_body_dict())
