import boto3
from botocore.exceptions import ClientError, BotoCoreError

from cfn_sphere.exceptions import CfnSphereBotoError
from cfn_sphere.exceptions import CfnSphereException
from cfn_sphere.util import with_boto_retry


class Ec2Api(object):
    def __init__(self, region="eu-west-1"):
        self.client = boto3.client('ec2', region_name=region)

    @with_boto_retry()
    def get_images(self, name_pattern):
        """
        Return list of AMIs matching the given name_pattern

        :param name_pattern: str: AMI name pattern
        :return: list(dict)
        :raise CfnSphereException:
        """
        filters = [
            {'Name': 'name', 'Values': [name_pattern]},
            {'Name': 'is-public', 'Values': ['false']},
            {'Name': 'state', 'Values': ['available']},
            {'Name': 'root-device-type', 'Values': ['ebs']}
        ]

        try:
            response = self.client.describe_images(ExecutableUsers=["self"], Filters=filters)
        except (BotoCoreError, ClientError) as e:
            raise CfnSphereBotoError(e)

        if not response['Images']:
            raise CfnSphereException("Could not find any private and available Taupage AMI")

        return response['Images']

    @staticmethod
    def get_latest_image_id(images_list):
        """
        Filter image with most recent CreationDate
        :param images_list: list(dict)
        :return str: image id
        """
        images = {image['CreationDate']: image['ImageId'] for image in images_list}
        creation_dates = list(images.keys())
        creation_dates.sort(reverse=True)
        return images[creation_dates[0]]

    @with_boto_retry()
    def get_latest_taupage_image_id(self):
        """
        Return the image id of the most recent private AMI matching the name pattern 'Taupage-AMI-*'

        :return: str: image id
        """
        taupage_images = self.get_images(name_pattern='Taupage-AMI-*')
        return self.get_latest_image_id(taupage_images)


if __name__ == "__main__":
    ec2 = Ec2Api()
    print(ec2.get_latest_taupage_image_id())
