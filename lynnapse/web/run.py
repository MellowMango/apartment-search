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
    
    # Find an available port
    import socket
    
    def find_available_port(start_port=8000, max_port=8010):
        for port in range(start_port, max_port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                try:
                    s.bind(('localhost', port))
                    return port
                except OSError:
                    continue
        raise RuntimeError(f"No available ports found between {start_port} and {max_port}")
    
    try:
        port = find_available_port()
        if port != 8000:
            print(f"⚠️  Port 8000 is in use, using port {port} instead")
    except RuntimeError as e:
        print(f"❌ {e}")
        return
    
    print("🎓 Starting Lynnapse Web Interface...")
    print(f"📍 Access the interface at: http://localhost:{port}")
    print(f"📊 API docs available at: http://localhost:{port}/docs")
    print("🔧 To stop the server, press Ctrl+C")
    print()
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=port,
        reload=False,  # Set to True for development
        log_level="info"
    )

if __name__ == "__main__":
    main() 