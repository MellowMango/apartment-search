#!/usr/bin/env python3
"""
Quick demo script for the Lynnapse web interface.

This script demonstrates how easy it is to start the web interface
for university faculty scraping.
"""

import subprocess
import sys
import webbrowser
import time
from pathlib import Path

def main():
    """Start the Lynnapse web interface demo."""
    
    print("🎓 Lynnapse Web Interface Demo")
    print("=" * 50)
    print()
    
    # Check if we're in the right directory
    if not Path("lynnapse").exists():
        print("❌ Error: Please run this script from the lynnapse-scraper directory")
        print("   cd /path/to/lynnapse-scraper")
        print("   python demo_web.py")
        sys.exit(1)
    
    print("📦 Starting Lynnapse Web Interface...")
    print("   This will open a browser window at http://localhost:8000")
    print("   where you can:")
    print("   • Configure University of Arizona Psychology scraping")
    print("   • Monitor scraping progress in real-time")
    print("   • View and export captured faculty data")
    print("   • Access live statistics and success rates")
    print()
    
    try:
        print("🚀 Launching web server...")
        
        # Start the web interface
        # This will use the CLI command we added
        process = subprocess.Popen([
            sys.executable, "-m", "lynnapse.cli", "web", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
        
        # Wait a moment for the server to start
        time.sleep(3)
        
        # Open browser
        print("🌐 Opening browser...")
        webbrowser.open("http://localhost:8000")
        
        print()
        print("✅ Web interface is running!")
        print("   URL: http://localhost:8000")
        print("   Press Ctrl+C to stop the server")
        print()
        
        # Wait for the process to complete or be interrupted
        process.wait()
        
    except KeyboardInterrupt:
        print("\n👋 Stopping web interface...")
        if 'process' in locals():
            process.terminate()
            process.wait()
        print("✅ Web interface stopped")
        
    except Exception as e:
        print(f"❌ Error starting web interface: {e}")
        print()
        print("💡 Troubleshooting:")
        print("   1. Install dependencies: pip install -r requirements.txt")
        print("   2. Check if port 8000 is available")
        print("   3. Run manually: lynnapse web")
        sys.exit(1)

if __name__ == "__main__":
    main() 