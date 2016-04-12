from botocore.exceptions import ClientError, BotoCoreError


class CfnSphereException(Exception):
    pass


class CfnStackActionFailedException(CfnSphereException):
    pass


class TemplateErrorException(CfnSphereException):
    pass


class NoConfigException(CfnSphereException):
    pass


class BadConfigException(CfnSphereException):
    pass


class CyclicDependencyException(CfnSphereException):
    pass


class InvalidDependencyGraphException(CfnSphereException):
    pass


class CfnSphereBotoError(CfnSphereException):
    def __init__(self, e):
        self.boto_exception = e
        self.message = str(e)

        if isinstance(e, ClientError):
            response = e.response
            error = response["Error"]
            code = error["Code"]
            message = error["Message"]

            self.message = "{0}: {1}".format(code, message)

    def __str__(self):
        return self.message
