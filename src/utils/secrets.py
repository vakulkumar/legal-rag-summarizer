import boto3
import logging
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

def get_secret(secret_name: str, region_name: str = "us-east-1") -> str:
    """
    Retrieves a secret from AWS Secrets Manager.
    """
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        logger.error(f"Failed to retrieve secret {secret_name}: {e}")
        raise e

    # Decrypts secret using the associated KMS key.
    if 'SecretString' in get_secret_value_response:
        return get_secret_value_response['SecretString']
    else:
        # If binary
        return get_secret_value_response['SecretBinary']
