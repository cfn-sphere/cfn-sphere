from boto.ec2 import connect_to_region


class Ec2(object):
    def __init__(self, region="eu-west-1"):
        self.conn = connect_to_region(region)

    def get_latest_taupage_image(self):
        filters = [{'Name': 'name', 'Values': ['*Taupage-AMI-*']},
                   {'Name': 'is-public', 'Values': ['false']},
                   {'Name': 'state', 'Values': ['available']},
                   {'Name': 'root-device-type', 'Values': ['ebs']}]
        print self.conn.get_all_images(executable_by="self", filters=filters)



foo = Ec2().get_latest_taupage_image()