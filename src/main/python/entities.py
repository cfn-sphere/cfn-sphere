

class Artifact(object):

    def __init__(self, stack_name, key, value):
        self.resource_name = stack_name + '.' + key
        self.key = key
        self.value = value

class Stack(object):

    def __init__(self):
        pass
