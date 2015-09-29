import os
import json
import yaml
from cfn_sphere.aws.s3 import S3
from cfn_sphere.aws.cloudformation.template import CloudFormationTemplate
from cfn_sphere.exceptions import TemplateErrorException


class CloudFormationTemplateLoader(object):
    @classmethod
    def get_template_from_url(cls, url, working_dir):
        if url.lower().startswith("s3://"):
            return CloudFormationTemplate(body_dict=cls._s3_get_template(url), name=os.path.basename(url))
        else:
            return CloudFormationTemplate(body_dict=cls._fs_get_template(url, working_dir), name=os.path.basename(url))

    @staticmethod
    def _fs_get_template(url, working_dir):
        """
        Load cfn template from filesyste

        :param url: str template path
        :return: dict repr of cfn template
        """
        if not os.path.isabs(url) and working_dir:
            url = os.path.join(working_dir, url)

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
            raise TemplateErrorException("{0} has an unknown file type. Please provide an url with [.json|.yml|.yaml] extension")
        except Exception as e:
            raise TemplateErrorException(e)