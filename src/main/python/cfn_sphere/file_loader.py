import codecs
import json
import os

import yaml

from cfn_sphere.aws.s3 import S3
from cfn_sphere.exceptions import TemplateErrorException
from cfn_sphere.template import CloudFormationTemplate


class FileLoader(object):

    @classmethod
    def get_file_from_url(cls, url, working_dir):
        if url.lower().startswith("s3://"):
            return CloudFormationTemplate(body_dict=cls._s3_get_file(url), name=os.path.basename(url))
        else:
            return CloudFormationTemplate(body_dict=cls._fs_get_file(url, working_dir), name=os.path.basename(url))

    @staticmethod
    def _fs_get_file(url, working_dir):
        """
        Load cfn template from filesystem

        :param url: str template path
        :return: dict repr of cfn template
        """
        if not os.path.isabs(url) and working_dir:
            url = os.path.join(working_dir, url)

        try:
            with codecs.open(url, 'r', encoding='utf-8') as template_file:
                if url.lower().endswith(".json"):
                    return json.loads(template_file.read())
                if url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                    return yaml.load(template_file.read())
        except Exception as e:
            raise TemplateErrorException("Could not load file from {0}: {1}".format(url, e))

        raise TemplateErrorException("Template file must have either .yaml or .json extension")

    @staticmethod
    def _s3_get_file(url):
        s3 = S3()
        try:
            if url.lower().endswith(".json"):
                return json.loads(s3.get_contents_from_url(url))
            if url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                return yaml.load(s3.get_contents_from_url(url))
            raise TemplateErrorException(
                "{0} has an unknown file type. Please provide an url with [.json|.yml|.yaml] extension")
        except Exception as e:
            raise TemplateErrorException("Could not load file from {0}: {1}".format(url, e))
