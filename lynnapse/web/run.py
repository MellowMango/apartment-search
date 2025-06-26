#!/usr/bin/env python3
"""
Simple startup script for the Lynnapse web interface.

Usage:
    python -m lynnapse.web.run
    or
    python lynnapse/web/run.py
"""

import uvicorn
from .app import create_app

def main():
    """Start the web interface server."""
    app = create_app()
    
    print("🎓 Starting Lynnapse Web Interface...")
    print("📍 Access the interface at: http://localhost:8000")
    print("📊 API docs available at: http://localhost:8000/docs")
    print("🔧 To stop the server, press Ctrl+C")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,  # Set to True for development
        log_level="info"
    )

if __name__ == "__main__":
    main() 