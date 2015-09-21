from boto.ec2 import connect_to_region


class Ec2(object):
    def __init__(self, region="eu-west-1"):
        self.conn = connect_to_region(region)

    def get_taupage_images(self):
        filters = {'name': ['Taupage-AMI-*'],
                   'is-public': ['false'],
                   'state': ['available'],
                   'root-device-type': ['ebs']
                   }

        return self.conn.get_all_images(executable_by=["self"], filters=filters)

    def get_latest_taupage_image_id(self):
        images = {image.creationDate: image.id for image in self.get_taupage_images()}

        creation_dates = images.keys()
        creation_dates.sort()
        return images[creation_dates[0]]

# creationDate, name, id, ownerId

print Ec2().get_latest_taupage_image_id()