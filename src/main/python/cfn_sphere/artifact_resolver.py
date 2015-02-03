__author__ = 'mhoyer'

from cfn_sphere.connector.cloudformation import CloudFormation
import logging


class CloudFormation(object):

    def __init__(self, region="eu-west-1", stacks= None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

