import base64

import boto3
from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError

from cfn_sphere.exceptions import CfnSphereBotoError, CfnSphereException


class KMS(object):
    def __init__(self, region="eu-west-1"):
        self.client = boto3.client('kms', region_name=region)

    def decrypt(self, encrypted_value, encryption_context=None):
        if encryption_context is None:
            encryption_context = {}

        try:
            ciphertext_blob = base64.b64decode(encrypted_value.encode())
            response = self.client.decrypt(CiphertextBlob=ciphertext_blob, EncryptionContext=encryption_context)
            return response['Plaintext'].decode('utf-8')
        except Boto3Error as e:
            raise CfnSphereBotoError(e)
        except ClientError as e:
            raise CfnSphereException(e)

    def encrypt(self, key_id, cleartext_string, encryption_context=None):
        if encryption_context is None:
            encryption_context = {}

        try:
            response = self.client.encrypt(KeyId=key_id,
                                           Plaintext=cleartext_string,
                                           EncryptionContext=encryption_context)

            return base64.b64encode(response['CiphertextBlob']).decode('utf-8')
        except (Boto3Error, ClientError) as e:
            raise CfnSphereBotoError(e)


if __name__ == "__main__":
    kms_client = KMS()
    ciphertext = kms_client.encrypt("my-key-id", "foo")
    print(kms_client.decrypt(ciphertext))
