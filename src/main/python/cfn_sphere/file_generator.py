from jinja2 import Template

from cfn_sphere import FileLoader
import os
import json
import yaml

from cfn_sphere.exceptions import CfnSphereException


class FileGenerator(object):
    def __init__(self, working_dir):
        self.working_dir = working_dir

    @staticmethod
    def _write_file(file_path, working_dir, content):
        if os.path.isabs(file_path):
            path = file_path
        else:
            path = os.path.join(working_dir, file_path)

        try:
            target_dir = os.path.dirname(path)
            if not os.path.exists(target_dir):
                os.mkdir(target_dir)

            with open(path, "w") as f:
                f.write(content)
        except Exception as e:
            raise CfnSphereException(e)

    @staticmethod
    def _is_valid_json(content):
        try:
            json.loads(content)
        except ValueError as e:
            raise CfnSphereException("Rendered file does not make valid json: {0}".format(e))

    @staticmethod
    def _is_valid_yaml(content):
        try:
            yaml.safe_load(content)
        except yaml.YAMLError as e:
            print(content)
            raise CfnSphereException("Rendered file does not make valid yaml: {0}".format(e))

    def render_file(self, source_url, destination_url, context):
        file_content = FileLoader().get_file(source_url, self.working_dir)
        rendered = self.get_rendered_file_content(file_content, context)

        if destination_url.endswith(".json"):
            self._is_valid_json(rendered)
        if destination_url.endswith(".yaml") or destination_url.endswith(".yml"):
            self._is_valid_yaml(rendered)

        self._write_file(destination_url, self.working_dir, rendered)

    @staticmethod
    def get_rendered_file_content(template, context):
        return Template(template).render(**context)


if __name__ == "__main__":
    FileGenerator(None).render_file("/tmp/input.template", "/tmp/output.json", {"name": "Somebody"})
