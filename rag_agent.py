# rag_agent.py
# This is a Python backend service that uses FastAPI and LangChain to answer job compensation-related queries using RAG (Retrieval-Augmented Generation).
# The service loads real LeetCode compensation data, builds a vector database, and uses an LLM (GPT-4) to answer questions via an HTTP API.

from fastapi import FastAPI  # Web framework for building APIs
from pydantic import BaseModel  # For data validation and request/response models
from langchain_openai import OpenAIEmbeddings  # For generating embeddings using OpenAI
from langchain_community.vectorstores import Chroma  # Vector database for storing embeddings
from langchain_community.chat_models import ChatOpenAI  # Chat LLM interface
from langchain.chains import RetrievalQA  # Retrieval-augmented QA chain
from langchain.text_splitter import RecursiveCharacterTextSplitter  # For splitting documents into chunks
from langchain.docstore.document import Document  # Document wrapper for LangChain
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate  # For prompt engineering
from typing import List, Dict, Optional
import json  # For loading JSON data
import os  # For environment variables
import re  # For extracting structured data from content

# Set your OpenAI API key (for demo only; use environment variables in production)
os.environ["OPENAI_API_KEY"] = "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"

# Initialize FastAPI app
app = FastAPI()

# Define request and response data models for the API
class QueryRequest(BaseModel):
    query: str  # The user's question

class AgentResponse(BaseModel):
    response: str  # The agent's answer
    compensation_data: Optional[List[Dict]] = None  # Structured compensation data for the frontend

# Ensure the OpenAI API key is set
if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY environment variable not set. Please set it before running the agent.")

# Load scraped LeetCode compensation data from JSON file
with open("leetcode_compensation_data.json", "r", encoding='utf-8') as f:
    data = json.load(f)

print(f"Loaded {len(data)} compensation posts from LeetCode")

# Convert each LeetCode compensation post to a text document for retrieval
raw_docs = []
for entry in data:
    # Create a comprehensive text representation of each compensation post
    doc_text = (
        f"Title: {entry['title']}\n"
        f"Author: {entry['author']}\n"
        f"Created: {entry['created_at']}\n"
        f"Content: {entry['content']}\n"
        f"Summary: {entry['summary']}\n"
        f"Tags: {', '.join(entry['tags'])}\n"
        f"URL: {entry['url']}\n"
        f"Topic ID: {entry['topic_id']}"
    )
    raw_docs.append(Document(page_content=doc_text))

# Split documents into smaller chunks for better retrieval
# Using larger chunks since LeetCode posts contain more detailed information
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = splitter.split_documents(raw_docs)

# Create embeddings for each chunk using OpenAI
embedding = OpenAIEmbeddings()

# Store embeddings in a Chroma vector database (persistent)
PERSIST_DIR = "chroma_db"
if not os.path.exists(PERSIST_DIR):
    # First run: create and persist the vectorstore
    vectorstore = Chroma.from_documents(chunks, embedding, persist_directory=PERSIST_DIR)
else:
    # Load the persistent vectorstore
    vectorstore = Chroma(embedding_function=embedding, persist_directory=PERSIST_DIR)

# Create a retriever to fetch relevant chunks for a query
# Increased k to get more context from the larger dataset
retriever = vectorstore.as_retriever(search_kwargs={"k": 8})

# System prompt to instruct the LLM to only answer job/compensation-related queries
system_instruction = (
    "You are a helpful assistant for job switchers and professionals seeking compensation information. "
    "You have access to real LeetCode compensation data from various companies and roles. "
    "Only answer questions related to compensation, salaries, job roles, companies, or career advice. "
    "When providing compensation information, be specific about the source being LeetCode discussion posts. "
    "If the question is unrelated to compensation or careers, politely respond: "
    "'I can only help with compensation, job roles, or company-related queries based on LeetCode data.'"
)

# Build a prompt template for the LLM (must include {context} and {question})
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_instruction),
    HumanMessagePromptTemplate.from_template("Context: {context}\nQuestion: {question}")
])

# Initialize the LLM (GPT-4) and the RetrievalQA chain
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=False,
    chain_type_kwargs={"prompt": prompt}
)

# Define the API endpoint for querying the agent
@app.post("/query")
async def query_endpoint(req: QueryRequest):
    # Pass the user's query to the RetrievalQA chain and return the answer
    answer = qa_chain.run(req.query)
    
    # Check if the query is asking for compensation data that should include structured results
    query_lower = req.query.lower()
    should_include_data = any(keyword in query_lower for keyword in [
        'show', 'find', 'search', 'get', 'list', 'data', 'compensation', 'salary', 'offer'
    ])
    
    compensation_data = None
    if should_include_data:
        # Get the source documents used for this query
        # Retrieve relevant documents for structuring
        docs = retriever.get_relevant_documents(req.query)
        
        # Extract structured data from the original dataset based on the query
        relevant_entries = []
        for doc in docs:
            # Find matching entries in our original data
            for entry in data:
                if entry['title'] in doc.page_content or entry['topic_id'] in doc.page_content:
                    relevant_entries.append(entry)
        
        if relevant_entries:
            compensation_data = extract_compensation_data(answer, relevant_entries)
    
    return AgentResponse(response=answer, compensation_data=compensation_data)

def extract_compensation_data(content: str, original_data: List[Dict]) -> List[Dict]:
    """
    Extract and structure compensation data from LeetCode posts
    Returns data in format expected by Chat.tsx
    """
    structured_data = []
    
    # Try to extract structured compensation information from the content
    for entry in original_data:
        # Look for compensation-related keywords in title or content
        title = entry.get('title', '').lower()
        content_text = entry.get('content', '').lower()
        
        if not any(keyword in title + content_text for keyword in ['salary', 'compensation', 'offer', 'tc', 'total comp']):
            continue
            
        # Extract company name from title
        company = 'Unknown'
        common_companies = ['google', 'meta', 'facebook', 'amazon', 'microsoft', 'apple', 'netflix', 'uber', 'airbnb', 'salesforce']
        for comp in common_companies:
            if comp in title:
                company = comp.capitalize()
                if comp == 'facebook':
                    company = 'Meta'
                break
        
        # Try to extract numbers (salary, total comp, etc.)
        numbers = re.findall(r'\$?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)[k]?', entry.get('content', ''))
        salary_numbers = [int(n.replace(',', '')) for n in numbers if len(n.replace(',', '')) >= 4]
        
        # Extract level information
        level = 'Unknown'
        level_patterns = [r'l(\d+)', r'level\s*(\d+)', r'e(\d+)', r'sde\s*(\d+)', r'ic(\d+)']
        for pattern in level_patterns:
            match = re.search(pattern, title + content_text)
            if match:
                level_num = match.group(1)
                if 'sde' in title + content_text:
                    level = f'SDE {level_num}'
                elif company.lower() == 'google':
                    level = f'L{level_num}'
                elif company.lower() == 'meta':
                    level = f'E{level_num}'
                else:
                    level = f'L{level_num}'
                break
        
        # Estimate compensation based on extracted numbers
        total_comp = max(salary_numbers) if salary_numbers else 0
        base_salary = min(salary_numbers) if len(salary_numbers) > 1 else int(total_comp * 0.6) if total_comp else 0
        
        structured_entry = {
            'id': entry.get('topic_id', str(len(structured_data))),
            'company': company,
            'level': level,
            'totalCompensation': total_comp,
            'baseSalary': base_salary,
            'bonus': int(total_comp * 0.1) if total_comp else 0,
            'equity': total_comp - base_salary - int(total_comp * 0.1) if total_comp else 0,
            'location': 'Location not specified',
            'yearsOfExperience': 'Not specified',
            'submittedDate': entry.get('created_at', ''),
            'url': entry.get('url', ''),
            'originalTitle': entry.get('title', '')
        }
        
        # Only add if we have meaningful data
        if total_comp > 0 or company != 'Unknown':
            structured_data.append(structured_entry)
    
    return structured_data[:10]  # Limit to 10 results for UI performance

# Run the FastAPI app with Uvicorn if this script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
