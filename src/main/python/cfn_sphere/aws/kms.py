import binascii

from builtins import bytes
from boto import kms
from boto.exception import BotoServerError
from boto.kms.exceptions import InvalidCiphertextException
from cfn_sphere.exceptions import CfnSphereBotoErrorException, InvalidEncryptedValueException
from cfn_sphere.util import with_boto_retry
import base64


class KMS(object):
    def __init__(self, region="eu-west-1"):
        self.conn = kms.connect_to_region(region)

    @with_boto_retry()
    def decrypt(self, encrypted_value):
        try:
            response = self.conn.decrypt(base64.b64decode(encrypted_value.encode()))
        except TypeError as e:
            raise InvalidEncryptedValueException("Could not decode encrypted value: {0}".format(e), e)
        except binascii.Error as e:
            raise InvalidEncryptedValueException("Could not decode encrypted value: {0}".format(e))
        except InvalidCiphertextException as e:
            raise InvalidEncryptedValueException("Could not decrypted value: {0}".format(e))
        except BotoServerError as e:
            raise CfnSphereBotoErrorException(e)

        return response['Plaintext'].decode('utf-8')

    @with_boto_retry()
    def encrypt(self, key_id, cleartext_string):
        response = self.conn.encrypt(key_id, bytes(cleartext_string, 'utf-8'))
        return base64.b64encode(response['CiphertextBlob']).decode('utf-8')


if __name__ == "__main__":
    kms_client = KMS()
    ciphertext = kms_client.encrypt("a-key-id", "foo")
    print(kms_client.decrypt(ciphertext))

