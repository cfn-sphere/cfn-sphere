import pprint

from boto import ec2
from boto.exception import BotoServerError
from cfn_sphere.exceptions import CfnSphereException, CfnSphereBotoErrorException
from cfn_sphere.util import get_logger, with_boto_retry


class Ec2Api(object):
    def __init__(self, region="eu-west-1"):
        self.conn = ec2.connect_to_region(region)
        self.logger = get_logger()

    @with_boto_retry()
    def get_taupage_images(self):
        filters = {'name': ['Taupage-AMI-*'],
                   'is-public': ['false'],
                   'state': ['available'],
                   'root-device-type': ['ebs']
                   }
        try:
            response = self.conn.get_all_images(executable_by=["self"], filters=filters)
        except BotoServerError as e:
            raise CfnSphereBotoErrorException(e)

        if not response:
            raise CfnSphereException("Could not find any private and available Taupage AMI")

        self.logger.debug("Found Taupage-AMI-* images:\n{0}".format(pprint.pformat([vars(x) for x in response])))
        return response

    def get_latest_taupage_image_id(self):
        images = {image.creationDate: image.id for image in self.get_taupage_images()}

        creation_dates = list(images.keys())
        creation_dates.sort(reverse=True)
        return images[creation_dates[0]]
