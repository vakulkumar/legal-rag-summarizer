import os
import tempfile
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

def load_and_split_pdf(file_path: str, chunk_size: int = 2000, chunk_overlap: int = 200) -> List[Document]:
    """
    Loads a PDF from a file path and splits it into chunks.
    
    Args:
        file_path (str): Path to the PDF file.
        chunk_size (int): Size of text chunks.
        chunk_overlap (int): Overlap between chunks.
        
    Returns:
        List[Document]: List of split documents.
    """
    loader = PyPDFLoader(file_path)
    # PyPDFLoader loads pages. We might want to split them further if pages are dense.
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )
    
    split_docs = text_splitter.split_documents(documents)
    return split_docs

def process_uploaded_file(file_content: bytes, filename: str) -> List[Document]:
    """
    Helper to save bytes to a temp file and process it.
    """
    suffix = os.path.splitext(filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(file_content)
        tmp_path = tmp.name
        
    try:
        return load_and_split_pdf(tmp_path)
    finally:
        os.remove(tmp_path)
