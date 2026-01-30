from typing import List
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain.chains.summarize import load_summarize_chain
from langchain_core.prompts import PromptTemplate
from src.utils.config import settings

def get_summarization_chain(model_name: str = "gpt-3.5-turbo"):
    """
    Creates a Map-Reduce summarization chain customized for legal documents.
    """
    llm = ChatOpenAI(temperature=0, model_name=model_name, api_key=settings.OPENAI_API_KEY)
    
    # Prompt for summarizing each chunk (Map step)
    map_prompt_template = """
    Write a concise summary of the following legal text section:
    
    "{text}"
    
    CONCISE SUMMARY:
    """
    map_prompt = PromptTemplate(template=map_prompt_template, input_variables=["text"])
    
    # Prompt for combining summaries (Reduce step)
    combine_prompt_template = """
    You are a legal expert. You have been given a series of summaries of sections from a legal document.
    Your goal is to create a coherent, comprehensive summary of the entire document, highlighting obligations, liabilities, dates, and key terms.
    Use professional legal tone but make it easy to understand for a business stakeholder.
    
    Summaries:
    "{text}"
    
    COMPREHENSIVE LEGAL SUMMARY:
    """
    combine_prompt = PromptTemplate(template=combine_prompt_template, input_variables=["text"])
    
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
    chain = get_summarization_chain()
    # The chain call expects a key depending on internal structure, usually 'input_documents' for this chain
    result = chain.invoke({"input_documents": docs})
    return result["output_text"]
