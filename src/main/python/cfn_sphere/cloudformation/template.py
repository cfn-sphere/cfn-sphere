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
        self.body = template_body

        if not self.body:
            self.body = self._load_template(self.url)

    def get_template_body(self):
        return self.body

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
