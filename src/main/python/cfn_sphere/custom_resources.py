from boto import sqs, sns
from cfn_sphere.exceptions import CfnSphereException


class CustomResourceHandler(object):
    @classmethod
    def process_post_resources(cls, stack):
        custom_resources_dict = stack.template.post_custom_resources

        for resource, resource_description in custom_resources_dict.items():
            if resource_description['Type'] == "Custom::SNS::Subscription":
                cls.handle_sns_subscription(resource_description, stack)

    @classmethod
    def handle_sns_subscription(cls, resource_description, stack):
        queue_prefix = stack.name + '-' + resource_description['Properties']['QueueResourceName']
        topic_arn = cls.extract_topic_arn(resource_description, stack.parameters)

        sqs_conn = sqs.connect_to_region(stack.region)
        sns_conn = sns.connect_to_region(stack.region)

        queues = sqs_conn.get_all_queues(prefix=queue_prefix)
        if (len(queues) != 1):
            raise CfnSphereException(
                "Found {0} queues matching the prefix: {1}. Should be 1.".format(len(queues), queue_prefix))

        sns_conn.subscribe_sqs_queue(topic_arn, queues[0])

    @staticmethod
    def extract_topic_arn(resource_description, parameters):
        try:
            parameter_name = resource_description['Properties']['TopicArn']

            if isinstance(parameter_name, dict):
                parameter_name = resource_description['Properties']['TopicArn']['Ref']
                for param, value in parameters:
                    if param == parameter_name:
                        return value
                raise CfnSphereException("Could not find a parameter value for {0}".format(parameter_name))
            else:
                return parameter_name
        except KeyError:
            raise CfnSphereException("Could not find TopicArn in Custom::SNS::Subscription properties")
