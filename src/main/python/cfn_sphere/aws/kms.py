import binascii

import six
from boto import kms
from boto.exception import BotoServerError
from boto.kms.exceptions import InvalidCiphertextException
from cfn_sphere.exceptions import CfnSphereBotoError, InvalidEncryptedValueException
from cfn_sphere.util import with_boto_retry
if six.PY3:
    from base64 import decodebytes as base64decode
else:
    from base64 import decodestring as base64decode


class KMS(object):
    def __init__(self, region="eu-west-1"):
        self.conn = kms.connect_to_region(region)

    @with_boto_retry()
    def decrypt(self, encrypted_value):
        try:
            response = self.conn.decrypt(base64decode(encrypted_value))
        except TypeError as e:
            raise InvalidEncryptedValueException("Could not decode encrypted value: {0}".format(e), e)
        except binascii.Error as e:
            raise InvalidEncryptedValueException("Could not decode encrypted value: {0}".format(e), e)
        except InvalidCiphertextException as e:
            raise InvalidEncryptedValueException("Could not decrypted value: {0}".format(e), e)
        except BotoServerError as e:
            raise CfnSphereBotoError(e)

        return response['Plaintext']
