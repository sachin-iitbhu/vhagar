#!/bin/bash

# Development runner for Go backend with auto-reload
# This script watches for changes and restarts the Go server

echo "🚀 Starting Go Backend in development mode with auto-reload..."
echo "📁 Working directory: $(pwd)"
echo "🔄 Auto-reload enabled - Go files will be monitored for changes"
echo "🌐 Server will be available at: http://localhost:8081"
echo ""
echo "============================================================"
echo ""

# Function to kill the Go process
kill_go_process() {
    if [ ! -z "$GO_PID" ]; then
        echo "🛑 Stopping Go server (PID: $GO_PID)..."
        kill $GO_PID 2>/dev/null
        wait $GO_PID 2>/dev/null
    fi
}

# Function to start the Go server
start_go_server() {
    kill_go_process
    echo "🔄 Starting Go server..."
    go run main.go &
    GO_PID=$!
    echo "✅ Go server started (PID: $GO_PID)"
}

# Cleanup function
cleanup() {
    echo ""
    echo "🧹 Cleaning up..."
    kill_go_process
    exit 0
}

# Set up signal handlers
trap cleanup SIGINT SIGTERM

# Initial start
start_go_server

# Check if fswatch is available (macOS)
if command -v fswatch &> /dev/null; then
    echo "👀 Using fswatch to monitor Go files..."
    fswatch -o -e ".*" -i "\.go$" . | while read f; do
        echo "📝 File change detected, restarting server..."
        start_go_server
    done
else
    echo "� Using polling to monitor Go files (fswatch not available)..."
    # Fallback: simple polling mechanism
    last_change=0
    while true; do
        # Get the latest modification time of any .go file
        current_change=$(find . -name "*.go" -type f -exec stat -f "%m" {} \; 2>/dev/null | sort -n | tail -1)
        
        if [ "$current_change" != "$last_change" ] && [ "$last_change" != "0" ]; then
            echo "� Go file change detected, restarting server..."
            start_go_server
        fi
        
        last_change=$current_change
        sleep 2
    done
fi
