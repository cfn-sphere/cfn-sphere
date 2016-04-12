from botocore.exceptions import ClientError


class CfnSphereException(Exception):
    def __init__(self, message="", boto_exception=None):
        self.message = message
        self.str = self.message
        self.boto_exception = boto_exception
        self.request_id = None
        try:
            self.request_id = boto_exception.request_id
            self.str += " (Request ID: {0})".format(self.request_id)
        except:
            pass

    def __str__(self):
        return self.str


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
