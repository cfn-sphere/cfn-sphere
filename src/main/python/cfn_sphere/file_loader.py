import codecs
import json
import os

import yaml

from cfn_sphere.aws.s3 import S3
from cfn_sphere.exceptions import TemplateErrorException, CfnSphereException
from cfn_sphere.template import CloudFormationTemplate


class FileLoader(object):
    @classmethod
    def get_cloudformation_template(cls, url, working_dir):
        """
        Load file content from url and return cfn-sphere CloudFormationTemplate
        :param url: str
        :param working_dir: str
        :return: CloudFormationTemplate
        """
        try:
            template_body_dict = cls.get_yaml_or_json_file(url, working_dir)
            return CloudFormationTemplate(body_dict=template_body_dict, name=os.path.basename(url))
        except Exception as e:
            raise TemplateErrorException("Could not load file from {0}: {1}".format(url, e))

    @classmethod
    def get_yaml_or_json_file(cls, url, working_dir):
        """
        Load yaml or json from filesystem or s3
        :param url: str
        :param working_dir: str
        :return: dict
        """
        file_content = cls.get_file(url, working_dir)

        try:
            if url.lower().endswith(".json"):
                return json.loads(file_content.read())
            elif url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                return yaml.load(file_content.read())
            else:
                raise CfnSphereException("{0} has an invalid suffix, use [json|yml|yaml]")
        except Exception as e:
            raise CfnSphereException(e)

    @classmethod
    def get_file(cls, url, working_dir):
        """
        Load file from filesystem or s3
        :param url: str
        :param working_dir: str
        :return: str(utf-8)
        """
        if url.lower().startswith("s3://"):
            return cls._s3_get_file(url)
        else:
            return cls._fs_get_file(url, working_dir)

    @staticmethod
    def _fs_get_file(url, working_dir):
        """
        Load file from filesystem

        :param url: str template path
        :return: str(utf-8)
        """
        if not os.path.isabs(url) and working_dir:
            url = os.path.join(working_dir, url)

        try:
            with codecs.open(url, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            raise CfnSphereException("Could not load file from {0}: {1}".format(url, e))

        raise TemplateErrorException("Template file must have either .yml, .yaml or .json extension")

    @staticmethod
    def _s3_get_file(url):
        """
        Load file from s3
        :param url: str
        :return: str(utf-8)
        """
        try:
            return S3().get_contents_from_url(url)
        except Exception as e:
            raise CfnSphereException("Could not load file from {0}: {1}".format(url, e))
