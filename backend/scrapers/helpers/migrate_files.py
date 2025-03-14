#!/usr/bin/env python
"""
Helper script to migrate existing files into the new directory structure.
"""

import os
import sys
import shutil
import glob
import re
from datetime import datetime
from pathlib import Path

# Add the project directory to the path so we can import our modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

def migrate_files():
    """
    Migrate existing files into the new directory structure.
    """
    base_dir = Path(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))
    data_dir = base_dir / "data"

    # Create directories if they don't exist
    os.makedirs(data_dir / "screenshots" / "acrmultifamily", exist_ok=True)
    os.makedirs(data_dir / "html" / "acrmultifamily", exist_ok=True)
    os.makedirs(data_dir / "extracted" / "acrmultifamily", exist_ok=True)

    # Find all screenshot files in the root directory
    screenshot_files = glob.glob(str(base_dir / "acr-screenshot-*.txt"))
    print(f"Found {len(screenshot_files)} screenshot files")

    # Find all HTML preview files in the root directory
    html_preview_files = glob.glob(str(base_dir / "acr-html-preview-*.txt"))
    print(f"Found {len(html_preview_files)} HTML preview files")

    # Find all HTML files in the root directory
    html_files = glob.glob(str(base_dir / "acr-html-*.html"))
    print(f"Found {len(html_files)} HTML files")

    # Find all JSON files in the root directory
    json_files = glob.glob(str(base_dir / "acr-properties-*.json"))
    print(f"Found {len(json_files)} JSON files")

    # Migrate screenshot files
    for file_path in screenshot_files:
        filename = os.path.basename(file_path)
        match = re.search(r'acr-screenshot-(\d{8}-\d{6})\.txt', filename)
        if match:
            timestamp = match.group(1)
            new_filename = f"{timestamp}.txt"
            new_path = data_dir / "screenshots" / "acrmultifamily" / new_filename
            print(f"Moving {filename} to {new_path}")
            shutil.move(file_path, new_path)

    # Migrate HTML preview files
    for file_path in html_preview_files:
        filename = os.path.basename(file_path)
        match = re.search(r'acr-html-preview-(\d{8}-\d{6})\.txt', filename)
        if match:
            timestamp = match.group(1)
            new_filename = f"preview-{timestamp}.txt"
            new_path = data_dir / "html" / "acrmultifamily" / new_filename
            print(f"Moving {filename} to {new_path}")
            shutil.move(file_path, new_path)

    # Migrate HTML files
    for file_path in html_files:
        filename = os.path.basename(file_path)
        match = re.search(r'acr-html-(\d{8}-\d{6})\.html', filename)
        if match:
            timestamp = match.group(1)
            new_filename = f"{timestamp}.html"
            new_path = data_dir / "html" / "acrmultifamily" / new_filename
            print(f"Moving {filename} to {new_path}")
            shutil.move(file_path, new_path)

    # Migrate JSON files
    for file_path in json_files:
        filename = os.path.basename(file_path)
        match = re.search(r'acr-properties-(\d{8}-\d{6})\.json', filename)
        if match:
            timestamp = match.group(1)
            new_filename = f"properties-{timestamp}.json"
            new_path = data_dir / "extracted" / "acrmultifamily" / new_filename
            print(f"Moving {filename} to {new_path}")
            shutil.move(file_path, new_path)

    print("Migration completed")

if __name__ == "__main__":
    migrate_files() 