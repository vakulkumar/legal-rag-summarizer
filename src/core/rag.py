import logging
from typing import List, Any
from langchain_openai import ChatOpenAI
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from src.utils.config import settings
from src.core.prompts import get_map_prompt, get_combine_prompt

# Handle import changes in langchain
try:
    from langchain.chains.summarize import load_summarize_chain
except ImportError:
    try:
        from langchain_classic.chains.summarize import load_summarize_chain
    except ImportError:
         raise ImportError("Could not import load_summarize_chain")

logger = logging.getLogger(__name__)

def get_summarization_chain(model_name: str = "gpt-3.5-turbo") -> Any:
    """
    Creates a Map-Reduce summarization chain customized for legal documents.
    """
    logger.info(f"Initializing summarization chain with model: {model_name}")
    llm = ChatOpenAI(temperature=0, model_name=model_name, api_key=settings.OPENAI_API_KEY)
    
    map_prompt = get_map_prompt()
    combine_prompt = get_combine_prompt()
    
    # Load the chain
    chain = load_summarize_chain(
        llm=llm,
        chain_type="map_reduce",
        map_prompt=map_prompt,
        combine_prompt=combine_prompt,
        verbose=False 
    )
    
    return chain

def summarize_documents(docs: List[Document]) -> str:
    """
    Runs the summarization chain on the provided documents.
    """
    logger.info(f"Starting summarization for {len(docs)} documents/chunks")
    try:
        chain = get_summarization_chain()
        # The chain call expects a key depending on internal structure, usually 'input_documents' for this chain
        result = chain.invoke({"input_documents": docs})
        summary = result["output_text"]
        logger.info("Summarization completed successfully")
        return summary
    except Exception as e:
        logger.error(f"Error during summarization: {str(e)}")
        raise
