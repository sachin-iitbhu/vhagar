# 🚀 Vhagar Development Aliases - Quick Reference

## Installation
```bash
# Run once to set up aliases
cd /Users/sachinmittal/vhagar
./setup-aliases.sh
source ~/.zshrc
```

## Available Commands

### Core Services
| Command | Description | Port | Auto-Reload |
|---------|-------------|------|-------------|
| `rag` | Start Python RAG Agent | 8000 | ✅ |
| `go-backend` | Start Go Backend | 8081 | ✅ |
| `frontend` | Start Vite Frontend | 8080 | ✅ |

### Utility Commands
| Command | Description |
|---------|-------------|
| `vhagar` | Show all available commands |
| `vhagar-all` | Instructions to run all services |
| `vhagar-status` | Check which ports are running |

## Quick Start
```bash
# Terminal 1
rag

# Terminal 2  
go-backend

# Terminal 3
frontend
```

## URLs After Starting
- 🐍 **Python RAG**: http://localhost:8000
- 🔗 **Go Backend**: http://localhost:8081  
- 🎨 **Frontend**: http://localhost:8080

## What Auto-Reloads
- **`rag`**: Python files (.py) → Server restarts
- **`go-backend`**: Go files (.go) → Server restarts
- **`frontend`**: React/TS files → Hot module replacement

## Troubleshooting
```bash
# Check service status
vhagar-status

# Kill processes on specific ports
lsof -ti:8000 | xargs kill  # Kill Python RAG
lsof -ti:8081 | xargs kill  # Kill Go Backend  
lsof -ti:8080 | xargs kill  # Kill Frontend
```
