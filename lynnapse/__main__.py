"""
Main entry point for the Lynnapse package.
Allows running with: python -m lynnapse
"""

import sys
import os

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lynnapse.cli import app

if __name__ == "__main__":
    app()