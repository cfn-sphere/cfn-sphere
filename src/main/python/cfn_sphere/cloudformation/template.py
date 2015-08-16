import json
import os
import yaml
from cfn_sphere.util import get_logger


class NoTemplateException(Exception):
    pass


class CloudFormationTemplate(object):
    def __init__(self, template_url, template_body=None, working_dir=None):
        self.logger = get_logger()

        self.working_dir = working_dir
        self.url = template_url
        self.body_dict = template_body

        if not self.body_dict:
            self.body_dict = self._load_template(self.url)

        self.transform_template_body()

    def get_template_body_dict(self):
        return self.body_dict

    def _load_template(self, url):
        self.logger.debug("Working in {0}".format(os.getcwd()))
        if url.lower().startswith("s3://"):
            return self._s3_get_template(url)
        else:
            return self._fs_get_template(url)

    def _fs_get_template(self, url):
        """
        Load cfn template from filesyste

        :param url: str template path
        :return: dict repr of cfn template
        """

        if not os.path.isabs(url) and self.working_dir:
            url = os.path.join(self.working_dir, url)

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

    def _s3_get_template(self, url):
        raise NotImplementedError

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
