class CfnSphereException(Exception):
    pass


class CfnStackActionFailedException(CfnSphereException):
    pass


class TemplateErrorException(CfnSphereException):
    pass


class NoConfigException(CfnSphereException):
    pass


class CfnSphereBotoError(CfnSphereException):
    def __init__(self, e):
        self.boto_exception = e

    def __str__(self):
        return "{0}: {1}".format(self.boto_exception.error_code, self.boto_exception.message)
