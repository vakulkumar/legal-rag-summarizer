# Legal RAG Summarizer

A RAG-based application using Python and LangChain to summarize legal PDFs with high accuracy. Features an asynchronous job-based architecture for scalable processing.

## Features

- **PDF Ingestion**: Processes legal PDF documents using PyPDFLoader and RecursiveCharacterTextSplitter
- **AI Summarization**: Uses LangChain with GPT-3.5-turbo for high-quality legal summaries using Map-Reduce strategy
- **Async Processing**: Job-based architecture with S3 + SQS for scalable, non-blocking PDF processing
- **Redis Caching**: Reduces latency through intelligent caching and job status tracking
- **Serverless Deployment**: Ready for AWS Lambda deployment with FastAPI + Mangum
- **Secrets Management**: Supports AWS Secrets Manager for secure API key storage
- **CI/CD Pipeline**: Automated testing and deployment via GitHub Actions

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Client    │────▶│  API Lambda │────▶│     S3      │────▶│     SQS     │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
                           │                                       │
                           ▼                                       ▼
                    ┌─────────────┐                         ┌─────────────┐
                    │    Redis    │◀────────────────────────│   Worker    │
                    │   (Status)  │                         │   Lambda    │
                    └─────────────┘                         └─────────────┘
```

- **API Layer**: FastAPI application handling file uploads and status queries
- **Storage**: S3 for PDF storage, Redis for job status tracking
- **Processing**: SQS-triggered Lambda worker for async summarization
- **RAG Framework**: LangChain with OpenAI GPT-3.5-turbo
- **Deployment**: AWS Lambda + API Gateway (via AWS SAM)

## Setup

### Prerequisites

- Python 3.9+
- Redis server
- OpenAI API Key
- AWS Account (for deployment)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/vakulkumar/legal-rag-summarizer.git
cd legal-rag-summarizer
```

2. Create and activate virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set environment variables:
```bash
export OPENAI_API_KEY="your-openai-key"
export REDIS_URL="redis://localhost:6379"
export S3_BUCKET_NAME="your-bucket-name"
export AWS_REGION="us-east-1"
```

## Usage

### Run Locally

```bash
uvicorn src.app:app --reload
```

Access the API at `http://localhost:8000` and interactive docs at `http://localhost:8000/docs`.

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check |
| `/summarize` | POST | Upload PDF and start summarization job |
| `/status/{job_id}` | GET | Check job status and retrieve summary |

### Example Workflow

1. **Upload a PDF**:
```bash
curl -X POST "http://localhost:8000/summarize" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@contract.pdf"
```

Response:
```json
{
  "job_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "uploaded",
  "message": "File uploaded successfully. Processing started."
}
```

2. **Check job status**:
```bash
curl "http://localhost:8000/status/550e8400-e29b-41d4-a716-446655440000"
```

Response (when complete):
```json
{
  "status": "completed",
  "filename": "contract.pdf",
  "summary": "This Agreement acts as a Non-Disclosure Agreement..."
}
```

## Project Structure

```
legal-rag-summarizer/
├── .github/workflows/
│   └── deploy.yaml          # CI/CD pipeline
├── src/
│   ├── app.py               # FastAPI application (API Lambda)
│   ├── worker.py            # SQS Worker (Processing Lambda)
│   └── core/
│       ├── ingestion.py     # PDF loading & splitting
│       ├── rag.py           # LangChain summarization chain
│       ├── prompts.py       # Prompt templates for legal summarization
│       └── cache.py         # Redis caching utilities
│   └── utils/
│       ├── config.py        # Configuration management
│       └── secrets.py       # AWS Secrets Manager integration
├── tests/
│   └── test_rag.py          # Unit and integration tests
├── template.yaml            # AWS SAM template
└── requirements.txt
```

## Testing

Run the test suite:
```bash
pytest tests/
```

## Deployment

Deploy to AWS Lambda using SAM:

```bash
sam build
sam deploy --guided
```

### Required GitHub Secrets for CI/CD

| Secret | Description |
|--------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key |
| `OPENAI_API_KEY` | OpenAI API key (or use Secrets Manager ARN) |
| `REDIS_URL` | Redis connection string |

For automated deployment, push to the `main` branch and GitHub Actions will handle the rest.

## License

MIT
