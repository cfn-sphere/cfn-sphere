from botocore.exceptions import ClientError


class CfnSphereException(Exception):
    def __init__(self, message="", boto_exception=None):
        self.pretty_string = str(message)
        self.str = self.pretty_string
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


class InvalidConfigException(CfnSphereException):
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
        self.pretty_string = str(e)
        self.is_throttling_exception = False

        if isinstance(e, ClientError):
            self.parse_boto_client_error(e)

    def parse_boto_client_error(self, e):
        response = e.response
        error = response["Error"]
        code = error["Code"]
        message = error["Message"]

        self.pretty_string = "{0}: {1}".format(code, message)

        if code == "Throttling":
            self.is_throttling_exception = True

    def __str__(self):
        return self.pretty_string
