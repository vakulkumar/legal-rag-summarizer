import pytest
import json
import os
import fakeredis
from unittest.mock import MagicMock, patch
from src.core.ingestion import load_and_split_pdf
from src.core.rag import summarize_documents
from fastapi.testclient import TestClient
from src.app import app
from src.worker import handler
from botocore.exceptions import ClientError

client = TestClient(app)

MOCK_PDF_CONTENT = b"%PDF-1.4 mock pdf content"

@pytest.fixture
def mock_s3():
    with patch("src.app.s3_client") as mock:
        yield mock

@pytest.fixture
def fake_redis():
    server = fakeredis.FakeServer()
    r = fakeredis.FakeStrictRedis(server=server, decode_responses=True)
    # Patch app redis
    with patch("src.app.r", r):
        # Patch worker redis
        with patch("src.worker.r", r):
             yield r

@pytest.fixture
def mock_worker_s3():
    with patch("src.worker.s3_client") as mock:
        yield mock

@pytest.fixture
def mock_chain():
    with patch("src.core.rag.get_summarization_chain") as mock:
        chain_instance = MagicMock()
        chain_instance.invoke.return_value = {"output_text": "Mocked Summary"}
        mock.return_value = chain_instance
        yield mock

@pytest.fixture
def mock_loader():
    with patch("src.core.ingestion.PyPDFLoader") as mock:
        loader_instance = MagicMock()
        doc = MagicMock()
        doc.page_content = "Mock page content"
        doc.metadata = {}
        loader_instance.load.return_value = [doc]
        mock.return_value = loader_instance
        yield mock

def test_health_check():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "legal-rag-summarizer"}

def test_summarize_endpoint_integration(mock_s3, fake_redis):
    # This tests the full API -> Redis flow
    response = client.post(
        "/summarize",
        files={"file": ("test.pdf", MOCK_PDF_CONTENT, "application/pdf")}
    )

    assert response.status_code == 200
    data = response.json()
    job_id = data["job_id"]

    # Verify Redis state
    status = fake_redis.hgetall(f"job:{job_id}")
    assert status["status"] == "uploaded"
    assert status["filename"] == "test.pdf"

def test_get_status_integration(fake_redis):
    job_id = "test-job-id"
    fake_redis.hset(f"job:{job_id}", mapping={"status": "completed", "summary": "Test Summary"})

    response = client.get(f"/status/{job_id}")

    assert response.status_code == 200
    assert response.json() == {"status": "completed", "summary": "Test Summary"}

def test_worker_handler_success(mock_worker_s3, fake_redis, mock_chain, mock_loader):
    job_id = "test-job-id"
    key = f"uploads/{job_id}.pdf"

    # Setup initial state
    fake_redis.hset(f"job:{job_id}", mapping={"status": "uploaded"})

    # Simulate SQS event
    event = {
        "Records": [
            {
                "body": json.dumps({
                    "Records": [
                        {
                            "s3": {
                                "bucket": {"name": "test-bucket"},
                                "object": {"key": key}
                            }
                        }
                    ]
                })
            }
        ]
    }

    # Run handler
    handler(event, None)

    # Verify Redis final state
    status = fake_redis.hgetall(f"job:{job_id}")
    assert status["status"] == "completed"
    assert status["summary"] == "Mocked Summary"

def test_worker_handler_s3_error(mock_worker_s3, fake_redis):
    job_id = "error-job-id"
    key = f"uploads/{job_id}.pdf"

    fake_redis.hset(f"job:{job_id}", mapping={"status": "uploaded"})

    # Mock S3 Error
    mock_worker_s3.download_file.side_effect = ClientError(
        {"Error": {"Code": "404", "Message": "Not Found"}},
        "GetObject"
    )

    event = {
        "Records": [
            {
                "body": json.dumps({
                    "Records": [
                        {
                            "s3": {
                                "bucket": {"name": "test-bucket"},
                                "object": {"key": key}
                            }
                        }
                    ]
                })
            }
        ]
    }

    handler(event, None)

    status = fake_redis.hgetall(f"job:{job_id}")
    assert status["status"] == "failed"
    assert "S3 Error" in status["error"]

def test_worker_handler_processing_error(mock_worker_s3, fake_redis, mock_loader):
    # Mock chain to fail or loader to fail
    with patch("src.worker.summarize_documents", side_effect=Exception("Summarization Failed")):
        job_id = "process-fail-job"
        key = f"uploads/{job_id}.pdf"
        
        fake_redis.hset(f"job:{job_id}", mapping={"status": "uploaded"})
        
        event = {
            "Records": [
                {
                    "body": json.dumps({
                        "Records": [
                            {
                                "s3": {
                                "bucket": {"name": "test-bucket"},
                                "object": {"key": key}
                            }
                        }
                    ]
                })
            }
        ]
    }
        
        handler(event, None)
        
        status = fake_redis.hgetall(f"job:{job_id}")
        assert status["status"] == "failed"
        assert "Summarization Failed" in status["error"]
