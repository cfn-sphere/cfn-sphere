import os
import json
import yaml
from boto import connect_s3
from cfn_sphere.util import get_logger
from cfn_sphere.aws.s3 import S3
from cfn_sphere.exceptions import TemplateErrorException


class CloudFormationTemplateLoader(object):

    @classmethod
    def get_template_dict_from_url(cls, url):
        if url.lower().startswith("s3://"):
            return CloudFormationTemplate(cls._s3_get_template(url), os.path.basename(url))
        else:
            return CloudFormationTemplate(cls._fs_get_template(url), os.path.basename(url))

    @staticmethod
    def _fs_get_template(url):
        """
        Load cfn template from filesyste

        :param url: str template path
        :return: dict repr of cfn template
        """

        try:
            with open(url, 'r') as template_file:
                if url.lower().endswith(".json"):
                    return json.loads(template_file.read())
                if url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                    return yaml.load(template_file.read())
        except ValueError as e:
            raise TemplateErrorException("Could not load template from {0}: {1}".format(url, e))
        except IOError as e:
            raise TemplateErrorException("Could not load template from {0}: {1}".format(url, e))

    @staticmethod
    def _s3_get_template(url):
        s3 = S3()
        try:
            if url.lower().endswith(".json"):
                return json.loads(s3.get_contents_from_url(url))
            if url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                return yaml.load(s3.get_contents_from_url(url))
        except Exception as e:
            raise TemplateErrorException(e)


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

        self.transform_template_body()

    def get_template_body_dict(self):
        return {
            'AWSTemplateFormatVersion': self.template_format_version,
            'Description': self.description,
            'Parameters': self.parameters,
            'Resources': self.resources,
            'Outputs': self.outputs
        }

    def get_template_json(self):
        return json.dumps(self.get_template_body_dict())

    def transform_template_body(self):
        # Could be a nice dynamic import solution if anybody wants custom handlers
        self.transform_dict(self.body_dict, {'@TaupageUserData': self.render_taupage_user_data})

    @classmethod
    def render_taupage_user_data(cls, taupage_user_data_dict):
        assert isinstance(taupage_user_data_dict, dict), "Value of 'TaupageUserData' must be of type dict"

        lines = ['#taupage-ami-config']
        lines.extend(cls.transform_userdata_dict(taupage_user_data_dict))

        return "UserData", {
            'Fn::Base64': {
                'Fn::Join': ['\n', lines]
            }
        }

    @classmethod
    def transform_userdata_dict(cls, userdata_dict, level=0):
        parameters = []

        for key, value in userdata_dict.items():
            # key indentation
            if level > 0:
                key = '  ' * level + str(key)

            # recursion for dict values
            if isinstance(value, dict):
                parameters.extend(cls.transform_userdata_dict(value, level + 1))
                parameters.append(key + ':')

            elif isinstance(value, str):
                if value.lower().startswith('@ref::'):
                    value = cls.transform_reference_string(value)
                elif value.lower().startswith('@getattr::'):
                    value = cls.transform_getattr_string(value)

                parameters.append(cls.transform_kv_to_cfn_join(key, value))

            else:
                parameters.append(cls.transform_kv_to_cfn_join(key, value))

        parameters.reverse()
        return parameters

    @staticmethod
    def transform_reference_string(value):
        return {'Ref': value[6:]}

    @staticmethod
    def transform_getattr_string(value):
        elements = value.split('@', 3)
        resource = elements[2]
        attribute = elements[3]

        return {'Fn::GetAtt': [resource, attribute]}

    @staticmethod
    def transform_kv_to_cfn_join(key, value):
        return {'Fn::Join:': [': ', [key, value]]}

    @classmethod
    def transform_dict(cls, dictionary, key_handlers):
        for key in dictionary:
            value = dictionary[key]
            if isinstance(value, dict):
                cls.transform_dict(value, key_handlers)
            if key.startswith('@'):
                if key in key_handlers.keys():
                    key_handler = key_handlers[key]

                    new_key, new_value = key_handler(value)
                    dictionary[new_key] = new_value
                    dictionary.pop(key)
                else:
                    raise TemplateErrorException("No handler defined for key {0}".format(key))

if __name__ == "__main__":
    s3_conn = connect_s3()
    bucket = s3_conn.get_bucket('is24-cfn-templates')
    print bucket.get_all_keys()
