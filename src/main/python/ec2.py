__author__ = 'mhoyer'

from boto import ec2
from boto.ec2 import autoscale
from boto.ec2.autoscale.limits import AccountLimits

import logging


class Ec2ResourceLimits(object):

    def __init__(self, region="eu-west-1", stacks= None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.conn = ec2.connect_to_region(region)
        self.logger.info("Connected to ec2 API at {0} with access key id: {1}".format(
            region, self.conn.aws_access_key_id))

    def get_account_limits(self):
        limits = {}
        for attribute in self.conn.describe_account_attributes():
            limits[attribute.attribute_name] = attribute.attribute_values
        return limits

    def get_instances_count(self):
        self.conn.get

class AutoscaleResourceLimits(object):

    def __init__(self, region="eu-west-1", stacks= None):
        logging.basicConfig(format='%(asctime)s %(levelname)s %(module)s: %(message)s',
                            datefmt='%d.%m.%Y %H:%M:%S',
                            level=logging.INFO)
        self.logger = logging.getLogger(__name__)

        self.conn = autoscale.connect_to_region(region)
        self.logger.info("Connected to autoscale API at {0} with access key id: {1}".format(
            region, self.conn.aws_access_key_id))

    def _describe_account_attributes(self):
        return self.conn.get_account_limits()

if __name__ == "__main__":
    ecc = Ec2ResourceLimits()
    for limit in ecc.get_account_limits():
        print limit

    print ""

    # autoscaling = AutoscaleResourceLimits()
    # limits = autoscaling.describe_account_attributes()
    # print limits.max_autoscaling_groups
    # print limits.max_launch_configurations