from fastapi import FastAPI, UploadFile, File, HTTPException
from mangum import Mangum
from src.core.ingestion import process_uploaded_file
from src.core.rag import summarize_documents
from src.core.cache import get_content_hash, get_cached_summary, cache_summary
import uvicorn
import os

app = FastAPI(title="Legal RAG Summarizer")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "legal-rag-summarizer"}

@app.post("/summarize")
async def summarize_pdf(file: UploadFile = File(...)):
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        content = await file.read()
        
        # 1. Check Cache
        file_hash = get_content_hash(content)
        cached_summary = get_cached_summary(file_hash)
        
        if cached_summary:
            return {"source": "cache", "summary": cached_summary}
        
        # 2. Process PDF
        # We need to pass the content to a helper that saves it temporarily
        # because PyPDFLoader works with file paths.
        try:
             # Re-write the content to a temp file inside the processing function
             # (Note: In a real async app we might want to avoid blocking calls, 
             # but splitting/summarizing is CPU bound anyway)
             docs = process_uploaded_file(content, file.filename)
        except Exception as e:
             raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

        # 3. Generate Summary
        summary = summarize_documents(docs)
        
        # 4. Cache Result
        cache_summary(file_hash, summary)
        
        return {"source": "generated", "summary": summary}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Lambda handler
handler = Mangum(app)

if __name__ == "__main__":
    uvicorn.run("src.app:app", host="0.0.0.0", port=8000, reload=True)
