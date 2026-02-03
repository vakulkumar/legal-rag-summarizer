import json
import logging
import os
import boto3
import redis
from botocore.exceptions import ClientError
from redis.exceptions import RedisError
from src.core.ingestion import load_and_split_pdf
from src.core.rag import summarize_documents
from src.utils.config import settings

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Redis
try:
    r = redis.from_url(settings.REDIS_URL, decode_responses=True)
except Exception as e:
    logger.error(f"Failed to connect to Redis: {e}")
    r = None

# Initialize S3 Client
s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

def handler(event, context):
    """
    SQS Worker Handler.
    """
    if not r:
        logger.error("Redis client not available. Cannot process jobs.")
        return # Or raise, but we can't report status.

    logger.info("Received event: %s", json.dumps(event))

    for record in event.get('Records', []):
        try:
            # Parse S3 event from SQS message body
            body = json.loads(record['body'])

            # S3 event structure inside body
            if 'Records' in body and len(body['Records']) > 0:
                s3_record = body['Records'][0]
                bucket_name = s3_record['s3']['bucket']['name']
                object_key = s3_record['s3']['object']['key']

                logger.info(f"Processing file: {object_key} from bucket: {bucket_name}")

                job_id = os.path.basename(object_key).replace('.pdf', '')

                # Update status
                try:
                    r.hset(f"job:{job_id}", mapping={"status": "processing"})
                except RedisError as re:
                    logger.error(f"Redis error update status: {re}")

                download_path = f"/tmp/{os.path.basename(object_key)}"

                try:
                    s3_client.download_file(bucket_name, object_key, download_path)
                    logger.info(f"Downloaded file to {download_path}")

                    docs = load_and_split_pdf(download_path)
                    summary = summarize_documents(docs)

                    r.hset(f"job:{job_id}", mapping={
                        "status": "completed",
                        "summary": summary
                    })
                    logger.info(f"Job {job_id} completed successfully")

                except ClientError as ce:
                    logger.error(f"S3 ClientError for job {job_id}: {ce}")
                    try:
                         r.hset(f"job:{job_id}", mapping={"status": "failed", "error": f"S3 Error: {ce}"})
                    except: pass
                except RedisError as re:
                    logger.error(f"Redis error for job {job_id}: {re}")
                    # If redis failed, we can't update status.
                except Exception as e:
                    logger.error(f"General error processing job {job_id}: {str(e)}")
                    try:
                        r.hset(f"job:{job_id}", mapping={"status": "failed", "error": str(e)})
                    except:
                        pass
                finally:
                    if os.path.exists(download_path):
                        os.remove(download_path)
            else:
                logger.warning("No S3 records found in message body")

        except Exception as e:
            logger.error(f"Error processing record: {str(e)}")
