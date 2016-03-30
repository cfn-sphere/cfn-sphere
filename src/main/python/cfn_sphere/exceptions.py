class CfnSphereException(Exception):
    """ The base exception for Cfn-Sphere """
    pass


class CfnStackActionFailedException(CfnSphereException):
    """ Raised if a stack modification fails """
    pass


class TemplateErrorException(CfnSphereException):
    """ Raised on invalid templates """
    pass


class NoConfigException(CfnSphereException):
    """ Raised if no stack configuration could be found """
    pass


class CyclicDependencyException(CfnSphereException):
    """ Raised if there are cyclic dependencies between referenced stacks """
    pass


class InvalidDependencyGraphException(CfnSphereException):
    """ Raised if Cfn-Sphere is not able to create a dependency graph for stacks """
    pass


class InvalidEncryptedValueException(CfnSphereException):
    """ Raised if Cfn-Sphere is unable to decrypt a KMS encrypted string """
    pass


class CfnSphereBotoError(CfnSphereException):
    def __init__(self, e):
        self.boto_exception = e

    def __str__(self):
        return "{0}: {1}".format(self.boto_exception.error_code, self.boto_exception.message)
