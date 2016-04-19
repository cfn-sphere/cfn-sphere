import codecs

from cfn_sphere.exceptions import CfnSphereException


class FileResolver(object):
    @staticmethod
    def read(path):
        try:
            with codecs.open(path, 'r', encoding='utf-8') as f:
                return str(f.read())
        except IOError as e:
            raise CfnSphereException("Cannot read file " + path, e)
