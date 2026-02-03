from langchain_core.prompts import PromptTemplate

# Prompt for summarizing each chunk (Map step)
MAP_PROMPT_TEMPLATE = """
Write a concise summary of the following legal text section:

"{text}"

CONCISE SUMMARY:
"""

# Prompt for combining summaries (Reduce step)
COMBINE_PROMPT_TEMPLATE = """
You are a legal expert. You have been given a series of summaries of sections from a legal document.
Your goal is to create a coherent, comprehensive summary of the entire document, highlighting obligations, liabilities, dates, and key terms.
Use professional legal tone but make it easy to understand for a business stakeholder.

Summaries:
"{text}"

COMPREHENSIVE LEGAL SUMMARY:
"""

def get_map_prompt() -> PromptTemplate:
    return PromptTemplate(template=MAP_PROMPT_TEMPLATE, input_variables=["text"])

def get_combine_prompt() -> PromptTemplate:
    return PromptTemplate(template=COMBINE_PROMPT_TEMPLATE, input_variables=["text"])
