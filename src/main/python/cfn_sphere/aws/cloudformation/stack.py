

class CloudFormationStack(object):
    def __init__(self, template, parameters, name, region, timeout=600):
        self.template = template
        self.parameters = parameters
        self.name = name
        self.region = region
        self.timeout = timeout

    def get_parameters_list(self):
        return [(key, value) for key, value in self.parameters.items()]
