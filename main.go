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
	log.Printf("Received %s request from %s", r.Method, r.RemoteAddr)

	// Enable CORS for frontend requests
	w.Header().Set("Access-Control-Allow-Origin", "*")
	w.Header().Set("Access-Control-Allow-Methods", "POST, OPTIONS")
	w.Header().Set("Access-Control-Allow-Headers", "Content-Type")

	// Handle preflight OPTIONS request
	if r.Method == http.MethodOptions {
		log.Println("Handling CORS preflight request")
		w.WriteHeader(http.StatusOK)
		return
	}

	if r.Method != http.MethodPost {
		log.Printf("Method not allowed: %s", r.Method)
		http.Error(w, "Only POST allowed", http.StatusMethodNotAllowed)
		return
	}

	// Decode the incoming JSON request
	var req QueryRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		log.Printf("Failed to decode request: %v", err)
		http.Error(w, "Invalid request", http.StatusBadRequest)
		return
	}

	log.Printf("Processing query: %s", req.Query)

	// Marshal the request to JSON to send to the Python agent
	// json.Marshal converts the Go struct (QueryRequest) into a JSON-formatted byte slice.
	// This is necessary because the Python RAG agent expects the request body in JSON format.
	agentReq, err := json.Marshal(req)
	if err != nil {
		log.Printf("Failed to marshal request: %v", err)
		http.Error(w, "Failed to encode request", http.StatusInternalServerError)
		return
	}

	log.Println("Forwarding request to Python RAG agent at http://localhost:8000/query")
	// Make a POST request to the Python RAG agent's /query endpoint
	rsp, err := http.Post("http://localhost:8000/query", "application/json", bytes.NewBuffer(agentReq))
	if err != nil {
		log.Printf("Failed to contact Python agent: %v", err)
		http.Error(w, "Failed to contact agent", http.StatusInternalServerError)
		return
	}
	defer rsp.Body.Close()

	log.Printf("Received response from Python agent with status: %d", rsp.StatusCode)

	// Read the response from the agent
	// io.ReadAll reads all the data from the response body and returns it as a byte slice.
	// This is used to capture the full JSON response from the Python agent before sending it back to the client.
	body, err := io.ReadAll(rsp.Body)
	if err != nil {
		log.Printf("Failed to read agent response: %v", err)
		http.Error(w, "Failed to read agent response", http.StatusInternalServerError)
		return
	}

	log.Printf("Successfully processed query, returning response (length: %d bytes)", len(body))
	// Set response headers and write the agent's response back to the client
	w.Header().Set("Content-Type", "application/json")
	w.Write(body)
}

func main() {
	// Register the /query endpoint with the handler
	http.HandleFunc("/query", handler)
	log.Println("Go backend running on :8081")
	// Start the HTTP server on port 8081
	log.Fatal(http.ListenAndServe(":8081", nil))
}
