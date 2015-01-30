__author__ = 'mhoyer'

from boto import cloudformation
from boto.resultset import ResultSet

import logging


class CloudFormation(object):

    def __init__(self, region="eu-west-1", stacks= None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.conn = cloudformation.connect_to_region(region)
        self.logger.info("Connected to cloudformation API at {0} with access key id: {1}".format(
            region, self.conn.aws_access_key_id))

        self.stacks = stacks
        if not self.stacks:
            self._load_stacks()

        assert isinstance(self.stacks, ResultSet)

    def _load_stacks(self):
        self.stacks = self.conn.describe_stacks()
        assert isinstance(self.stacks, ResultSet)

    def get_stacks_dict(self):
        stacks = {}
        for element in self.stacks:
            stack = {}
            stack["outputs"] = self.convert_kv_object_list_to_dict(element.outputs)
            stack["parameters"] = self.convert_kv_object_list_to_dict(element.parameters)
            stacks[element.stack_name] = stack

        return stacks

    def get_outputs_dict(self):
        outputs = {}
        for element in self.stacks:
            outputs[element.stack_name] = self.convert_kv_object_list_to_dict(element.outputs)

        return outputs

    def get_inputs_dict(self):
        inputs = {}
        for element in self.stacks:
            inputs[element.stack_name] = self.convert_kv_object_list_to_dict(element.parameters)

        return inputs

    def convert_kv_object_list_to_dict(self, list):
        kv_dict = {}
        for item in list:
            kv_dict[item.key] = item.value
        return kv_dict

    def get_app_from_stack_name(self, stack_name):
        return stack_name.split('-')[0]

    def get_env_from_stack_name(self, stack_name):
        return stack_name.split('-')[1]

    def get_available_artifacts(self):
        artifacts = {}
        for stack in self.stacks:
            for output in stack.outputs:
                key = stack.stack_name + '.' + output.key
                value = output.value

                artifacts[key] = value
        return artifacts

    def get_artifact_value(self, key):
        artifacts = self.get_available_artifacts()
        try:
            return artifacts[key]
        except KeyError:
            return None

    def create(self, template):
        self.conn.create_stack("bla", template_body={}, parameters=[])

class StackHandler(object):
    pass



if __name__ == "__main__":
    cfn = CloudFormation()
    outputs = cfn.get_inputs_dict()
    # print outputs["betasearch-live"]
    # print outputs
    #
    # inputs = cfn.get_outputs_dict()
    # print inputs["betasearch-live"]
    # print inputs

    print cfn.get_available_artifacts()
    print cfn.get_artifact_value("betasearch-test.S3LogBucket")
    print cfn.get_artifact_value("betasearch-live.S3LogBucket")
    print cfn.get_artifact_value("blalbufg")