from cfn_sphere.exceptions import CfnSphereException


class FileResolver(object):
    @staticmethod
    def read(path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except IOError as e:
            raise CfnSphereException("Cannot read file " + path, e)
