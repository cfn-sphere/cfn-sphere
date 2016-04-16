from cfn_sphere.exceptions import CfnSphereException


class CustomResourceHandler(object):
    @classmethod
    def process_post_resources(cls, stack):
        custom_resources_dict = stack.template.post_custom_resources
        if not custom_resources_dict:
            return

        for _, resource_description in custom_resources_dict.items():
            if resource_description['Type'] == "Custom::SNS::Subscription":
                cls.handle_sns_subscription(resource_description, stack)

    @classmethod
    def handle_sns_subscription(cls, resource_description, stack):
        raise CfnSphereException("The Cfn-Sphere PostCustomResource feature has been removed")
