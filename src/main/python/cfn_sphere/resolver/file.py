
class FileResolver(object):

    def read(self, path):
        try:
            with open(path, 'r') as f:
                return f.read()
        except IOError as e:
            raise CfnSphereException("Cannot read file " + path, e) 
