import logging
import uuid
import boto3
import redis
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from mangum import Mangum
from src.utils.config import settings
import uvicorn
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI(title="Legal RAG Summarizer")

# Initialize Redis
r = redis.from_url(settings.REDIS_URL, decode_responses=True)

# Initialize S3 Client
s3_client = boto3.client('s3', region_name=settings.AWS_REGION)

@app.get("/")
def health_check() -> Dict[str, str]:
    logger.info("Health check endpoint called")
    return {"status": "ok", "service": "legal-rag-summarizer"}

@app.post("/summarize")
async def summarize_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    logger.info(f"Received summarization request for file: {file.filename}")
    if file.content_type != "application/pdf":
        logger.warning(f"Invalid content type: {file.content_type}")
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        # Generate Job ID
        job_id = str(uuid.uuid4())
        
        # S3 Key
        key = f"uploads/{job_id}.pdf"
        
        # Upload to S3
        # Use file.file (spooled temp file) to upload directly
        logger.info(f"Uploading file to S3 bucket {settings.S3_BUCKET_NAME} with key {key}")
        file.file.seek(0)
        s3_client.upload_fileobj(file.file, settings.S3_BUCKET_NAME, key)
        
        # Initialize status in Redis
        r.hset(f"job:{job_id}", mapping={"status": "uploaded", "filename": file.filename})
        
        logger.info(f"Job {job_id} created and file uploaded")
        
        return {
            "job_id": job_id,
            "status": "uploaded",
            "message": "File uploaded successfully. Processing started."
        }
        
    except Exception as e:
        logger.error(f"Error initiating job: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}")
def get_job_status(job_id: str) -> Dict[str, Any]:
    logger.info(f"Checking status for job: {job_id}")
    try:
        job = r.hgetall(f"job:{job_id}")
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")

        return job
    except redis.RedisError as e:
        logger.error(f"Redis error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")

# Lambda handler
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
