# Go + Python LangChain RAG Backend Example

This project demonstrates a Go backend service that connects to a Python agent with Retrieval-Augmented Generation (RAG) capabilities using LangChain. The Go service forwards user queries to the Python RAG agent, which answers using compensation data.

## Project Structure

- `main.go`: Go HTTP server exposing `/query` endpoint. Forwards queries to the Python RAG agent.
- `rag_agent.py`: Python FastAPI server with LangChain RAG logic, exposing `/query` endpoint.
- `dummy_compensation_data.json`: Sample compensation data used by the RAG agent.
- `test_queries.sh`: Bash script to test the agent with multiple queries and save results.
- `qa_results.txt`: Output file with question-answer pairs from test queries.
- `.vscode/tasks.json`: VS Code tasks to run both services easily.
- `leetcode_scraper.py`: (Optional) Script to scrape compensation data from LeetCode Discuss.

## Prerequisites

- Go (1.18+ recommended)
- Python 3.8+
- pip (Python package manager)

## Setup

### 1. Install Python dependencies

Create and activate a virtual environment (recommended):

```sh
python3 -m venv venv
source venv/bin/activate
```

Install required packages:

```sh
pip install fastapi uvicorn pydantic langchain-openai langchain-community openai
```

### 2. Set your OpenAI API key

Edit `rag_agent.py` or set the environment variable:

```sh
export OPENAI_API_KEY=sk-...your-key-here...
```

## Running the Services

### 1. Start the Python RAG Agent

```sh
python3 rag_agent.py
```

Or use the VS Code task: **Run Python RAG Agent**

### 2. Start the Go Backend

```sh
go run main.go
```

Or use the VS Code task: **Run Go Backend**

### 3. Query the API

Send a POST request to `http://localhost:8080/query` with JSON body:

```json
{
  "query": "What is the compensation for SDE II at Google in Bangalore?"
}
```

Or use the provided test script:

```sh
bash test_queries.sh
cat qa_results.txt
```

## Notes

- The Go service expects the Python agent to be running on `localhost:8000`.
- The Python agent only answers questions about compensation, job roles, or companies.
- You can extend the data or scraping logic as needed (see `leetcode_scraper.py`).

## Example Advanced Queries

See `test_queries.sh` for multi-point and time-specific queries to test the agent.

---

**Happy job hunting!**
