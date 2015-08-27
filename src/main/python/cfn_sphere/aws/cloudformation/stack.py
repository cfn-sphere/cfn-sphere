

class CloudFormationStack(object):
    def __init__(self, template, parameters, name, region):
        self.template = template
        self.parameters = parameters
        self.name = name
        self.region = region
