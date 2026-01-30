import pytest
from unittest.mock import MagicMock, patch
from src.core.ingestion import load_and_split_pdf
from src.core.rag import summarize_documents
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)

# Mock data
MOCK_PDF_CONTENT = b"%PDF-1.4 mock pdf content"

@pytest.fixture
def mock_chain():
    with patch("src.core.rag.get_summarization_chain") as mock:
        chain_instance = MagicMock()
        chain_instance.invoke.return_value = {"output_text": "Mocked Summary"}
        mock.return_value = chain_instance
        yield mock

@pytest.fixture
def mock_redis():
    with patch("src.app.get_cached_summary") as mock_get, \
         patch("src.app.cache_summary") as mock_set:
        mock_get.return_value = None
        yield mock_get, mock_set

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

def test_ingestion(mock_loader):
    # We mock the loader, so file path doesn't matter much but must exist for the real loader if we didn't mock it completely.
    # Since we mocked PyPDFLoader class, we don't need a real file.
    docs = load_and_split_pdf("dummy.pdf")
    assert len(docs) > 0
    assert "Mock page" in docs[0].page_content

def test_summarize_endpoint_no_cache(mock_chain, mock_redis, mock_loader):
    # Mock process_uploaded_file to return dummy docs
    with patch("src.app.process_uploaded_file") as mock_process:
        mock_process.return_value = [MagicMock(page_content="foo")]
        
        response = client.post(
            "/summarize",
            files={"file": ("test.pdf", MOCK_PDF_CONTENT, "application/pdf")}
        )
        
        assert response.status_code == 200
        assert response.json() == {"source": "generated", "summary": "Mocked Summary"}

def test_summarize_endpoint_with_cache():
    with patch("src.app.get_cached_summary") as mock_get:
        mock_get.return_value = "Cached Summary"
        
        response = client.post(
            "/summarize",
            files={"file": ("test.pdf", MOCK_PDF_CONTENT, "application/pdf")}
        )
        
        assert response.status_code == 200
        assert response.json() == {"source": "cache", "summary": "Cached Summary"}
