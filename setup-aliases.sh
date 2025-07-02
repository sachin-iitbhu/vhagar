#!/bin/bash

# Vhagar Development Setup Script
# This script sets up convenient aliases for development

echo "🚀 Setting up Vhagar development aliases..."

# Add to zshrc if not already present
if ! grep -q "Vhagar Development Aliases" ~/.zshrc; then
    echo "" >> ~/.zshrc
    echo "# Vhagar Development Aliases" >> ~/.zshrc
    echo "source /Users/sachinmittal/vhagar/dev-aliases.sh" >> ~/.zshrc
    echo "✅ Added aliases to ~/.zshrc"
else
    echo "ℹ️  Aliases already present in ~/.zshrc"
fi

# Add Go bin to PATH if not present
if ! grep -q "export PATH=\$PATH:/Users/sachinmittal/go/bin" ~/.zshrc; then
    echo "export PATH=\$PATH:/Users/sachinmittal/go/bin" >> ~/.zshrc
    echo "✅ Added Go bin to PATH"
else
    echo "ℹ️  Go bin already in PATH"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To use the aliases, either:"
echo "1. Restart your terminal, or"
echo "2. Run: source ~/.zshrc"
echo ""
echo "Then you can use:"
echo "  rag         - Start Python RAG Agent"
echo "  go-backend  - Start Go Backend"
echo "  frontend    - Start Frontend"
echo "  vhagar      - Show all available commands"
echo ""
