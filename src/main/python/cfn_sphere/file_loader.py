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
            raise TemplateErrorException(
                "Could not load file from {0}: {1}".format(url, e))

    @staticmethod
    def handle_yaml_constructors(loader, suffix, node):
        """
        Constructor method for PyYaml to handle cfn intrinsic functions specified as yaml tags
        """
        function_mapping = {
            "!and": ("Fn::And", lambda x: x),
            "!base64": ("Fn::Base64", lambda x: x),
            "!condition": ("Condition", lambda x: x),
            "!equals": ("Fn::Equals", lambda x: x),
            "!findinmap": ("Fn::FindInMap", lambda x: x),
            "!getatt": ("Fn::GetAtt", lambda x: str(x).split(".", 1)),
            "!getazs": ("Fn::GetAZs", lambda x: x),
            "!if": ("Fn::If", lambda x: x),
            "!importvalue": ("Fn::ImportValue", lambda x: x),
            "!join": ("Fn::Join", lambda x: [x[0], x[1]]),
            "!not": ("Fn::Not", lambda x: x),
            "!or": ("Fn::Or", lambda x: x),
            "!ref": ("Ref", lambda x: x),
            "!select": ("Fn::Select", lambda x: x),
            "!sub": ("Fn::Sub", lambda x: x),
        }
        try:
            function, value_transformer = function_mapping[str(suffix).lower()]
        except KeyError as key:
            raise CfnSphereException(
                "Unsupported cfn intrinsic function tag found: {0}".format(key))

        if isinstance(node, yaml.ScalarNode):
            value = loader.construct_scalar(node)
        elif isinstance(node, yaml.SequenceNode):
            value = loader.construct_sequence(node)
        elif isinstance(node, yaml.MappingNode):
            value = loader.construct_mapping(node)
        else:
            raise CfnSphereException(
                "Invalid yaml node found while handling cfn intrinsic function tags")

        return {function: value_transformer(value)}

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
                return json.loads(file_content, encoding='utf-8')
            elif url.lower().endswith(".template"):
                return json.loads(file_content, encoding='utf-8')
            elif url.lower().endswith(".yml") or url.lower().endswith(".yaml"):
                yaml.add_multi_constructor(u"", cls.handle_yaml_constructors)
                return yaml.load(file_content)
            else:
                raise CfnSphereException(
                    "Invalid suffix, use [json|template|yml|yaml]")
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
            raise CfnSphereException(
                "Could not load file from {0}: {1}".format(url, e))

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
            raise CfnSphereException(
                "Could not load file from {0}: {1}".format(url, e))
