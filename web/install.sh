#!/bin/bash

echo "Installing dependencies for Jai's Personal Web Agent..."

# Install dependencies
npm install

# Copy environment file if it doesn't exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✓ Created .env file from .env.example"
    echo "  Please update VITE_API_BASE if needed"
fi

echo ""
echo "🎉 Setup complete!"
echo ""
echo "To start development:"
echo "  npm run dev"
echo ""
echo "To build for production:"
echo "  npm run build"
echo ""