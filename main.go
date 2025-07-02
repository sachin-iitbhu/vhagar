package main

import (
	"bytes"         // Used to create a buffer for the JSON request body
	"encoding/json" // For encoding (marshaling) and decoding (unmarshaling) JSON data
	"io"            // For reading the response body from HTTP requests
	"log"           // For logging server status and errors
	"net/http"      // For building HTTP servers and making HTTP requests
)

// QueryRequest represents the expected JSON request body from the client
// Example: {"query": "What is the compensation for SDE II at Google in Bangalore?"}
type QueryRequest struct {
	Query string `json:"query"`
}

// AgentResponse represents the JSON response from the Python RAG agent
// Example: {"response": "The total compensation for SDE II at Google in Bangalore is ..."}
type AgentResponse struct {
	Response string `json:"response"`
}

// handler processes POST requests to /query, forwards them to the Python RAG agent, and returns the agent's response
func handler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode the incoming JSON request
	var req QueryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	// Marshal the request to JSON to send to the Python agent
	// json.Marshal converts the Go struct (QueryRequest) into a JSON-formatted byte slice.
	// This is necessary because the Python RAG agent expects the request body in JSON format.
	agentReq, err := json.Marshal(req)
	if err != nil {
		http.Error(w, "Failed to encode request", http.StatusInternalServerError)
		return
	}

	// Make a POST request to the Python RAG agent's /query endpoint
	rsp, err := http.Post("http://localhost:8000/query", "application/json", bytes.NewBuffer(agentReq))
	if err != nil {
		http.Error(w, "Failed to contact agent", http.StatusInternalServerError)
		return
	}
	defer rsp.Body.Close()

	// Read the response from the agent
	// io.ReadAll reads all the data from the response body and returns it as a byte slice.
	// This is used to capture the full JSON response from the Python agent before sending it back to the client.
	body, err := io.ReadAll(rsp.Body)
	if err != nil {
		http.Error(w, "Failed to read agent response", http.StatusInternalServerError)
		return
	}

	// Set response headers and write the agent's response back to the client
	w.Header().Set("Content-Type", "application/json")
	w.Write(body)
}

func main() {
	// Register the /query endpoint with the handler
	http.HandleFunc("/query", handler)
	log.Println("Go backend running on :8080")
	// Start the HTTP server on port 8080
	log.Fatal(http.ListenAndServe(":8080", nil))
}
