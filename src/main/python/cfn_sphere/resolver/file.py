
class FileResolver(object):

    def read(self, path):
        with open(path, 'r') as file:
            return file.read()
