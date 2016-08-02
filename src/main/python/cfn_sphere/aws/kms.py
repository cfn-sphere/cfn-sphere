import base64

import boto3
from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError

from cfn_sphere.exceptions import CfnSphereBotoError


class KMS(object):
    def __init__(self, region="eu-west-1"):
        self.client = boto3.client('kms', region_name=region)

    def decrypt(self, encrypted_value):
        try:
            ciphertext_blob = base64.b64decode(encrypted_value.encode())
            response = self.client.decrypt(CiphertextBlob=ciphertext_blob)
            return response['Plaintext'].decode('utf-8')
        except Boto3Error as e:
            raise CfnSphereBotoError(e)

    def encrypt(self, key_id, cleartext_string):
        try:
            response = self.client.encrypt(KeyId=key_id, Plaintext=cleartext_string)
            return base64.b64encode(response['CiphertextBlob']).decode('utf-8')
        except (Boto3Error, ClientError) as e:
            raise CfnSphereBotoError(e)


if __name__ == "__main__":
    kms_client = KMS()
    ciphertext = kms_client.encrypt("my-key-id", "foo")
    print(kms_client.decrypt(ciphertext))
