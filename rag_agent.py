# rag_agent.py
# This is a Python backend service that uses FastAPI and LangChain to answer job compensation-related queries using RAG (Retrieval-Augmented Generation).
# The service loads real LeetCode compensation data, builds a vector database, and uses an LLM (GPT-4) to answer questions via an HTTP API.

from fastapi import FastAPI  # Web framework for building APIs
from pydantic import BaseModel  # For data validation and request/response models
from langchain_openai import OpenAIEmbeddings, ChatOpenAI  # For generating embeddings and chat LLM interface
from langchain_chroma import Chroma  # Vector database for storing embeddings
from langchain.chains import RetrievalQA  # Retrieval-augmented QA chain
from langchain.text_splitter import RecursiveCharacterTextSplitter  # For splitting documents into chunks
from langchain.docstore.document import Document  # Document wrapper for LangChain
from langchain_core.prompts import ChatPromptTemplate, SystemMessagePromptTemplate, HumanMessagePromptTemplate  # For prompt engineering
import json  # For loading JSON data
import os  # For environment variables
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Set your OpenAI API key (for demo only; use environment variables in production)
os.environ["OPENAI_API_KEY"] = "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"

# Initialize FastAPI app
app = FastAPI()

logging.info("FastAPI app initialized.")

# Define request and response data models for the API
class QueryRequest(BaseModel):
    query: str  # The user's question

class CompensationCard(BaseModel):
    id: str
    company: str
    title: str
    total_compensation: str
    total_compensation_currency: str = ""
    base_salary: str
    base_salary_currency: str = ""
    equity: str
    equity_currency: str = ""
    bonus: str = ""
    bonus_currency: str = ""
    experience: str
    location: str
    url: str
    created_at: str

class AgentResponse(BaseModel):
    response: str  # The agent's answer
    compensation_data: list[CompensationCard] = []  # Structured compensation data
    source_links: list[str] = []  # LeetCode discussion links for grounding

# Ensure the OpenAI API key is set
if not os.environ.get("OPENAI_API_KEY"):
    raise RuntimeError("OPENAI_API_KEY environment variable not set. Please set it before running the agent.")

# Load scraped LeetCode compensation data from JSON file
logging.info("Loading LeetCode compensation data...")
with open("leetcode_compensation_data.json", "r", encoding='utf-8') as f:
    data = json.load(f)

logging.info(f"Loaded {len(data)} compensation posts from LeetCode")

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

logging.info(f"Created {len(raw_docs)} documents for retrieval.")

# Split documents into smaller chunks for better retrieval
# Using larger chunks since LeetCode posts contain more detailed information
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
chunks = splitter.split_documents(raw_docs)
logging.info(f"Split documents into {len(chunks)} chunks.")

# Create embeddings for each chunk using OpenAI
embedding = OpenAIEmbeddings()

# Store embeddings in a Chroma vector database (persistent)
PERSIST_DIR = "chroma_db"
if not os.path.exists(PERSIST_DIR):
    logging.info(f"Creating new vectorstore in {PERSIST_DIR}...")
    # First run: create and persist the vectorstore
    vectorstore = Chroma.from_documents(chunks, embedding, persist_directory=PERSIST_DIR)
    logging.info("Vectorstore created and persisted.")
else:
    logging.info(f"Loading persistent vectorstore from {PERSIST_DIR}...")
    # Load the persistent vectorstore
    vectorstore = Chroma(embedding_function=embedding, persist_directory=PERSIST_DIR)
    logging.info("Vectorstore loaded.")

# Create a retriever to fetch relevant chunks for a query
# Increased k to get more context from the larger dataset
retriever = vectorstore.as_retriever(search_kwargs={"k": 8})
logging.info("Retriever created.")

# System prompt to instruct the LLM to return a JSON object containing a summary and a JSON array of compensation objects.
system_instruction = (
    "You are a helpful assistant for job switchers and professionals seeking compensation information. "
    "You have access to real LeetCode compensation data from various companies and roles. "
    "Only answer questions related to compensation, salaries, job roles, companies, or career advice. "
    "If the question is unrelated to compensation or careers, politely respond with a JSON object containing an error message. "
    "\n\n"
    "Your response must be a single JSON object with two keys: 'summary' and 'compensation_cards'. "
    "The 'summary' key should contain a concise, natural-language summary of the compensation trends based on the user's query and the retrieved data. "
    "The 'compensation_cards' key must contain a JSON array of objects, where each object represents a relevant LeetCode post and follows this schema: "
    "id, company, title, total_compensation, total_compensation_currency, base_salary, base_salary_currency, equity, equity_currency, bonus, bonus_currency, experience, location, url, created_at. "
    "For all currency fields, always use a valid ISO 4217 currency code (e.g., 'INR', 'USD', 'EUR', 'GBP', etc.). Do not use non-standard codes like 'LPA INR'. "
    "If the compensation is mentioned in units like 'LPA', 'lakhs', or 'crores', convert them to the full numeric value in the appropriate currency (e.g., '35 LPA INR' should be '3500000' with currency 'INR'). "
    "If a field is not mentioned in a post, use 'Not specified' or an empty string. "
    "Example output:"
    '{{'
    '  "summary": "For a Software Engineer in London, the average total compensation is around $120,000, with base salaries ranging from $90,000 to $110,000. Tech giants like Google and Meta tend to offer higher equity components.",'
    '  "compensation_cards": [{{"id": "123", "company": "Amazon", "title": "SDE1", "total_compensation": "150000", "total_compensation_currency": "USD", "base_salary": "120000", "base_salary_currency": "USD", "equity": "20000", "equity_currency": "USD", "bonus": "10000", "bonus_currency": "USD", "experience": "2 years", "location": "Seattle", "url": "https://leetcode.com/discuss/post/123", "created_at": "2024-01-01"}}]'
    '}}'
    "\nReturn only the JSON object and nothing else. "
    "Be precise and extract each component and its currency individually from the post content. "
)

# Build a prompt template for the LLM (must include {context} and {question})
prompt = ChatPromptTemplate.from_messages([
    SystemMessagePromptTemplate.from_template(system_instruction),
    HumanMessagePromptTemplate.from_template("Context:\n{context}\n\nQuestion:\n{question}")
])

# Initialize the LLM (GPT-4) and the RetrievalQA chain
llm = ChatOpenAI(model_name="gpt-4", temperature=0)
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    return_source_documents=True,  # Changed to True to get source documents
    chain_type_kwargs={"prompt": prompt}
)

# Remove extract_compensation_data and update /query endpoint to only use LLM JSON output

@app.post("/query")
async def query_endpoint(req: QueryRequest):
    logging.info(f"Received query: {req.query}")
    try:
        logging.info("Invoking QA chain...")
        result = qa_chain.invoke({"query": req.query})
        answer = result["result"]
        source_docs = result.get("source_documents", [])
        logging.info(f"QA chain returned {len(source_docs)} source documents.")

        import json
        import re
        
        summary = "Could not retrieve a summary."
        compensation_cards = []
        source_links = []
        
        try:
            # The entire LLM response should be a JSON object.
            # First, find the JSON object in the response.
            json_match = re.search(r'\{.*\}', answer, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                logging.info(f"Attempting to parse JSON from LLM output: {json_str[:300]}...")
                
                parsed_json = json.loads(json_str)
                summary = parsed_json.get("summary", summary)
                cards_data = parsed_json.get("compensation_cards", [])
                
                for card in cards_data:
                    compensation_cards.append(CompensationCard(**card))
                
                source_links = [card.get("url", "") for card in cards_data if card.get("url")]
                logging.info(f"Successfully parsed summary and {len(compensation_cards)} compensation cards.")
            else:
                logging.warning(f"No JSON object found in LLM output: {answer}")
                summary = answer # Fallback to returning the raw answer if parsing fails
        except Exception as e:
            logging.error(f"Failed to parse LLM output as JSON: {answer}", exc_info=True)
            summary = answer # Fallback for safety
            compensation_cards = []
            source_links = []

        response = AgentResponse(
            response=summary,
            compensation_data=compensation_cards,
            source_links=source_links[:10]
        )
        logging.info(f"Returning response with {len(compensation_cards)} cards and {len(source_links)} links.")
        return response
    except Exception as e:
        logging.error(f"An unexpected error occurred in /query endpoint for query: '{req.query}'", exc_info=True)
        # Re-raise the exception to be handled by FastAPI's default error handling
        raise

# Run the FastAPI app with Uvicorn if this script is executed directly
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "rag_agent:app",  # Use module:app format for reload
        host="0.0.0.0", 
        port=8000,
        reload=True,  # Enable auto-reload
        reload_dirs=["."]  # Watch current directory for changes
    )
