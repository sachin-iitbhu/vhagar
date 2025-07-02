#!/usr/bin/env python3
"""
Development runner for the RAG agent with auto-reload enabled.
This script starts the FastAPI server with uvicorn in development mode.
"""

import uvicorn
import os
import sys

def main():
    # Ensure we're in the right directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    
    print("🚀 Starting RAG Agent in development mode with auto-reload...")
    print("📁 Working directory:", script_dir)
    print("🔄 Auto-reload enabled - changes will be detected automatically")
    print("🌐 Server will be available at: http://localhost:8000")
    print("📖 API docs available at: http://localhost:8000/docs")
    print("\n" + "="*60 + "\n")
    
    try:
        uvicorn.run(
            "rag_agent:app",
            host="0.0.0.0",
            port=8000,
            reload=True,
            reload_dirs=["."],
            log_level="info"
        )
    except KeyboardInterrupt:
        print("\n🛑 RAG Agent stopped by user")
    except Exception as e:
        print(f"\n❌ Error starting RAG Agent: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
