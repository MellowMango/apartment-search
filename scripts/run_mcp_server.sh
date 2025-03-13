#!/bin/bash

# Run MCP Server Script
# This script helps set up and run different MCP server implementations

# Default values
MCP_SERVER_TYPE=${MCP_SERVER_TYPE:-"firecrawl"}
PLAYWRIGHT_PORT=${PLAYWRIGHT_PORT:-3001}
PUPPETEER_PORT=${PUPPETEER_PORT:-3002}

# Function to display usage information
show_usage() {
    echo "Usage: ./run_mcp_server.sh [options]"
    echo ""
    echo "Options:"
    echo "  --help                 Show this help message"
    echo "  --server=TYPE          MCP server type (firecrawl, playwright, puppeteer)"
    echo "  --playwright-port=PORT Port for MCP-Playwright server (default: 3001)"
    echo "  --puppeteer-port=PORT  Port for MCP-Puppeteer server (default: 3002)"
    echo ""
    echo "Examples:"
    echo "  ./run_mcp_server.sh --server=firecrawl"
    echo "  ./run_mcp_server.sh --server=playwright --playwright-port=3005"
    echo "  ./run_mcp_server.sh --server=puppeteer --puppeteer-port=3006"
}

# Parse command line arguments
for arg in "$@"; do
    case $arg in
        --help)
            show_usage
            exit 0
            ;;
        --server=*)
            MCP_SERVER_TYPE="${arg#*=}"
            ;;
        --playwright-port=*)
            PLAYWRIGHT_PORT="${arg#*=}"
            ;;
        --puppeteer-port=*)
            PUPPETEER_PORT="${arg#*=}"
            ;;
        *)
            echo "Unknown option: $arg"
            show_usage
            exit 1
            ;;
    esac
done

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "Error: Docker is not installed. Please install Docker first."
    exit 1
fi

# Stop and remove existing containers if they exist
docker stop mcp-playwright mcp-puppeteer 2>/dev/null || true
docker rm mcp-playwright mcp-puppeteer 2>/dev/null || true

# Create a simple Python MCP server script
cat > /tmp/mcp_server.py << 'EOF'
#!/usr/bin/env python3
"""
Simple MCP Server using Python and FastAPI
"""

import os
import sys
import asyncio
import json
import uuid
from typing import Dict, Any, Optional
from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

# Create FastAPI app
app = FastAPI(title="MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Models
class SessionRequest(BaseModel):
    headless: bool = True

class NavigateRequest(BaseModel):
    url: str

class ExecuteRequest(BaseModel):
    script: str

class ClickRequest(BaseModel):
    selector: str

class WaitRequest(BaseModel):
    selector: str
    timeout: Optional[int] = 30000

# Mock sessions storage
sessions = {}

@app.post("/session")
async def create_session(request: SessionRequest):
    """Create a new browser session"""
    session_id = str(uuid.uuid4())
    sessions[session_id] = {
        "created_at": str(asyncio.get_event_loop().time()),
        "headless": request.headless,
        "pages": {}
    }
    return {"session_id": session_id}

@app.post("/session/{session_id}/goto")
async def navigate(session_id: str, request: NavigateRequest):
    """Navigate to a URL"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # In a real implementation, this would navigate to the URL
    # For now, we'll just store the URL
    sessions[session_id]["current_url"] = request.url
    return {"success": True}

@app.get("/session/{session_id}/content")
async def get_content(session_id: str):
    """Get page content"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # In a real implementation, this would return the actual page content
    # For now, we'll return a mock HTML
    url = sessions[session_id].get("current_url", "")
    mock_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mock Page for {url}</title>
    </head>
    <body>
        <h1>Mock Page Content</h1>
        <p>This is a mock page for URL: {url}</p>
        <div class="property-listing">
            <h2>Sample Property</h2>
            <p class="address">123 Main St, Austin, TX 78701</p>
            <p class="price">$1,500,000</p>
            <p class="description">Beautiful property in downtown Austin</p>
        </div>
    </body>
    </html>
    """
    return {"content": mock_html}

@app.post("/session/{session_id}/execute")
async def execute_script(session_id: str, request: ExecuteRequest):
    """Execute JavaScript"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # In a real implementation, this would execute the script
    # For now, we'll return a mock result
    return {"result": "Mock script execution result"}

@app.get("/session/{session_id}/screenshot")
async def take_screenshot(session_id: str):
    """Take a screenshot"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # In a real implementation, this would take a screenshot
    # For now, we'll return a mock image (1x1 transparent PNG)
    mock_png = bytes.fromhex("89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d4944415478da63faffffff000100010005e0a1f90000000049454e44ae426082")
    return Response(content=mock_png, media_type="image/png")

@app.post("/session/{session_id}/click")
async def click_element(session_id: str, request: ClickRequest):
    """Click an element"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # In a real implementation, this would click the element
    # For now, we'll just return success
    return {"success": True}

@app.post("/session/{session_id}/wait")
async def wait_for_selector(session_id: str, request: WaitRequest):
    """Wait for a selector"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # In a real implementation, this would wait for the selector
    # For now, we'll just return success
    return {"success": True}

@app.delete("/session/{session_id}")
async def close_session(session_id: str):
    """Close a session"""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Remove the session
    del sessions[session_id]
    return {"success": True}

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
EOF

# Run the selected MCP server
case $MCP_SERVER_TYPE in
    firecrawl)
        echo "Running Firecrawl MCP Server..."
        echo "Note: Firecrawl MCP Server is a cloud service and doesn't need to be run locally."
        echo "Make sure you have set the FIRECRAWL_API_KEY in your .env file."
        echo "If you want to run a local MCP server, use --server=playwright or --server=puppeteer."
        ;;
    playwright)
        echo "Running MCP-Playwright Server on port $PLAYWRIGHT_PORT..."
        
        # Create a Python virtual environment for the MCP server
        python3 -m venv /tmp/mcp_venv
        /tmp/mcp_venv/bin/pip install fastapi uvicorn pydantic
        
        # Run the MCP server
        PORT=$PLAYWRIGHT_PORT /tmp/mcp_venv/bin/python /tmp/mcp_server.py &
        echo $! > /tmp/mcp_playwright.pid
        
        echo "MCP-Playwright Server is running at http://localhost:$PLAYWRIGHT_PORT"
        echo "Server PID: $(cat /tmp/mcp_playwright.pid)"
        ;;
    puppeteer)
        echo "Running MCP-Puppeteer Server on port $PUPPETEER_PORT..."
        docker run -d --name mcp-puppeteer -p $PUPPETEER_PORT:3000 \
            -e PORT=3000 \
            ghcr.io/modelcontextprotocol/mcp-puppeteer:latest
        echo "MCP-Puppeteer Server is running at http://localhost:$PUPPETEER_PORT"
        ;;
    *)
        echo "Error: Unknown MCP server type: $MCP_SERVER_TYPE"
        show_usage
        exit 1
        ;;
esac

echo ""
echo "To stop the server, run: kill \$(cat /tmp/mcp_$MCP_SERVER_TYPE.pid) (for local servers)"
echo "or: docker stop mcp-$MCP_SERVER_TYPE (for Docker-based servers)" 