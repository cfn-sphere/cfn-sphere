import json

import yaml
from boto import connect_s3
from cfn_sphere.util import get_logger
from cfn_sphere.aws.s3 import S3


class NoTemplateException(Exception):
    pass


class CloudFormationTemplateLoader(object):

    @classmethod
    def get_template_dict_from_url(cls, url):
        if url.lower().startswith("s3://"):
            return CloudFormationTemplate(cls._s3_get_template(url), url)
        else:
            return CloudFormationTemplate(cls._fs_get_template(url), url)

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
            raise NoTemplateException("Could not load template from {0}: {1}".format(url, e))
        except IOError as e:
            raise NoTemplateException("Could not load template from {0}: {1}".format(url, e))

    @staticmethod
    def _s3_get_template(url):
        s3 = S3()
        try:
            if url.lower().endswith(".json"):
                return json.loads(s3.get_contents_from_url(url))
            if url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                return yaml.load(s3.get_contents_from_url(url))
        except Exception as e:
            raise NoTemplateException(e)


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

    @staticmethod
    def render_taupage_user_data(dict_value):
        assert isinstance(dict_value, dict), "Value of 'TaupageUserData' must be of type dict"

        kv_pairs = ['#taupage-ami-config']

        for key in sorted(dict_value.keys()):
            kv_pairs.append({'Fn::Join:': [': ', [key, dict_value[key]]]})

        return "UserData", {
            'Fn::Base64': {
                'Fn::Join': ['\n', kv_pairs]
            }
        }

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
                    raise Exception("No handler defined for key {0}".format(key))

if __name__ == "__main__":
    s3_conn = connect_s3()
    bucket = s3_conn.get_bucket('is24-cfn-templates')
    print bucket.get_all_keys()
