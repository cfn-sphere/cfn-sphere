import boto3
from boto3.exceptions import Boto3Error
from botocore.exceptions import ClientError
from cfn_sphere.exceptions import CfnSphereBotoError, CfnSphereException

class SSM(object):
    
    def __init__(self, region='eu-west-1'):
        self.client = boto3.client('ssm', region_name=region)

    def get_parameter(self, name, with_decryption=True):
        try:
            return self.client.get_parameter(Name=name, WithDecryption=with_decryption)['Parameter']['Value']
        except (Boto3Error, ClientError) as e:
            raise CfnSphereBotoError(e)

if __name__ == "__main__":
    ssm_client = SSM()
    a = ssm_client.get_parameter('/tuv-blk/config.edn/database/blk-tuv-db-auroradbcluster/blk_master_cdc', True)
    print(a)
