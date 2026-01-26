#!/bin/bash

# Gist AI Backend Startup Script

echo "================================"
echo "Starting Gist AI Backend API"
echo "================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found!"
    echo "Please create one with: python -m venv venv"
    exit 1
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

# Check if dependencies are installed
echo "✓ Checking dependencies..."
python -c "import fastapi" 2>/dev/null || {
    echo "⚠️  FastAPI not found. Installing dependencies..."
    pip install -r requirements.txt
}

# Start the API server
echo ""
echo "================================"
echo "Starting API Server"
echo "================================"
echo "API will be available at: http://localhost:8000"
echo "Swagger docs: http://localhost:8000/docs"
echo "Press Ctrl+C to stop"
echo ""

python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
