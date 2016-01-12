import unittest2

from cfn_sphere.template import CloudFormationTemplate


class TestCloudFormationTemplateTests(unittest2.TestCase):
    def test_get_template_body_dict(self):
        template_body = {
            'Description': 'some description',
            "Metadata": {
                "meta": "value"
            },
            "Parameters": {
                "parameter": "value"
            },
            "Mappings": {
                "mapping": "value"
            },
            "Conditions": {
                "condition": "value"
            },
            "Resources": {
                "resource": "value"
            },
            "Outputs": {
                "output": "value"
            }
        }
        template = CloudFormationTemplate(template_body, "some name")

        self.assertEquals(template.template_format_version, "2010-09-09")
        self.assertEquals(template.description, "some description")
        self.assertEquals(template.metadata, {"meta": "value"})
        self.assertEquals(template.parameters, {"parameter": "value"})
        self.assertEquals(template.mappings, {"mapping": "value"})
        self.assertEquals(template.conditions, {"condition": "value"})
        self.assertEquals(template.resources, {"resource": "value"})
        self.assertEquals(template.outputs, {"output": "value"})
