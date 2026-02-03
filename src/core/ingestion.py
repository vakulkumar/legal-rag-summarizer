import os
import logging
from typing import List, Optional
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

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
    logger.info(f"Loading and splitting PDF from {file_path}")
    try:
        loader = PyPDFLoader(file_path)
        # PyPDFLoader loads pages. We might want to split them further if pages are dense.
        documents = loader.load()
        logger.debug(f"Loaded {len(documents)} pages from PDF")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        split_docs = text_splitter.split_documents(documents)
        logger.info(f"Split document into {len(split_docs)} chunks")
        return split_docs
    except Exception as e:
        logger.error(f"Error loading/splitting PDF: {str(e)}")
        raise
