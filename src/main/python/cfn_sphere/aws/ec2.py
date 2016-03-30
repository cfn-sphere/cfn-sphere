import boto3
from boto.exception import BotoServerError

from cfn_sphere.exceptions import CfnSphereException, CfnSphereBotoError
from cfn_sphere.util import with_boto_retry


class Ec2Api(object):
    def __init__(self, region="eu-west-1"):
        self.client = boto3.client('ec2', region_name=region)

    @with_boto_retry()
    def get_taupage_images(self):
        filters = [{'Name': 'name', 'Values': ['Taupage-AMI-*']},
                   {'Name': 'is-public', 'Values': ['false']},
                   {'Name': 'state', 'Values': ['available']},
                   {'Name': 'root-device-type', 'Values': ['ebs']}
                   ]
        try:
            response = self.client.describe_images(ExecutableUsers=["self"], Filters=filters)
        except BotoServerError as e:
            raise CfnSphereBotoError(e)

        if not response:
            raise CfnSphereException("Could not find any private and available Taupage AMI")

        return response['Images']

    def get_latest_taupage_image_id(self):
        images = {image['CreationDate']: image['ImageId'] for image in self.get_taupage_images()}

        creation_dates = list(images.keys())
        creation_dates.sort(reverse=True)
        return images[creation_dates[0]]


if __name__ == "__main__":
    ec2 = Ec2Api()
    print(ec2.get_latest_taupage_image_id())
