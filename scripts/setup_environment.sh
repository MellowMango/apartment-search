#!/bin/bash

# Setup script for Acquire Apartments development environment
echo "Setting up Acquire Apartments development environment..."

# Check if Python is installed
if command -v python3 &>/dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo "✅ $PYTHON_VERSION is installed"
else
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.9 or higher from https://www.python.org/downloads/"
    exit 1
fi

# Check if Node.js is installed
if command -v node &>/dev/null; then
    NODE_VERSION=$(node --version)
    echo "✅ Node.js $NODE_VERSION is installed"
else
    echo "❌ Node.js is not installed"
    echo "Please install Node.js 16 or higher from https://nodejs.org/"
    exit 1
fi

# Check if npm is installed
if command -v npm &>/dev/null; then
    NPM_VERSION=$(npm --version)
    echo "✅ npm $NPM_VERSION is installed"
else
    echo "❌ npm is not installed"
    echo "Please install npm from https://www.npmjs.com/get-npm"
    exit 1
fi

# Check if virtual environment exists for backend
if [ ! -d "backend/venv" ]; then
    echo "Creating Python virtual environment for backend..."
    cd backend
    python3 -m venv venv
    cd ..
    echo "✅ Python virtual environment created"
else
    echo "✅ Python virtual environment already exists"
fi

# Activate virtual environment and install backend dependencies
echo "Installing backend dependencies..."
cd backend
source venv/bin/activate
pip install -r requirements.txt
deactivate
cd ..
echo "✅ Backend dependencies installed"

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..
echo "✅ Frontend dependencies installed"

# Check if .env files exist
if [ ! -f "backend/.env" ]; then
    echo "❌ Backend .env file not found"
    echo "Please create a .env file in the backend directory based on .env.example"
else
    echo "✅ Backend .env file exists"
fi

if [ ! -f "frontend/.env" ]; then
    echo "❌ Frontend .env file not found"
    echo "Please create a .env file in the frontend directory based on .env.example"
else
    echo "✅ Frontend .env file exists"
fi

# Check for Neo4j credentials
if grep -q "NEO4J_URI" backend/.env; then
    echo "✅ Neo4j credentials found in backend/.env"
else
    echo "❌ Neo4j credentials not found in backend/.env"
    echo "Please add NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD to backend/.env"
    echo "You can create a free Neo4j Aura instance at https://neo4j.com/cloud/aura/"
fi

# Check for Supabase credentials
if grep -q "SUPABASE_URL" backend/.env; then
    echo "✅ Supabase credentials found in backend/.env"
else
    echo "❌ Supabase credentials not found in backend/.env"
    echo "Please add SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY to backend/.env"
    echo "You can create a free Supabase project at https://supabase.com/"
fi

if grep -q "NEXT_PUBLIC_SUPABASE_URL" frontend/.env; then
    echo "✅ Supabase credentials found in frontend/.env"
else
    echo "❌ Supabase credentials not found in frontend/.env"
    echo "Please add NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY to frontend/.env"
    echo "You can create a free Supabase project at https://supabase.com/"
fi

echo ""
echo "Environment setup completed!"
echo ""
echo "To start the backend server:"
echo "  cd backend"
echo "  source venv/bin/activate"
echo "  uvicorn app.main:app --reload"
echo ""
echo "To start the frontend server:"
echo "  cd frontend"
echo "  npm run dev"
echo ""
echo "Visit http://localhost:3000 in your browser to view the application." 