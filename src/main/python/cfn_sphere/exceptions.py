__author__ = 'mhoyer'


class CfnSphereException(Exception):
    pass


class CfnStackActionFailedException(CfnSphereException):
    pass


class TemplateErrorException(CfnSphereException):
    pass


class NoConfigException(CfnSphereException):
    pass