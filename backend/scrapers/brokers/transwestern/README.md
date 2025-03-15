# Transwestern Scraper

This scraper extracts property listings from the Transwestern website and saves them to the database.

## Overview

The Transwestern scraper is designed to extract commercial and multifamily property listings from the Transwestern website. It navigates to the properties page, extracts property data, and saves it to both local files and the database.

## Features

- Extracts property listings from the Transwestern website
- Saves HTML content and screenshots for debugging
- Extracts property details including title, description, location, property type, etc.
- Saves extracted properties to Supabase database
- Handles JavaScript-rendered content through multiple extraction methods

## Files

- `scraper.py`: Main scraper implementation
- `test_db_storage.py`: Test script for database storage functionality
- `README.md`: Documentation

## How to Run

### Main Scraper (Production Run)

To run the main scraper and save properties to the database:

```bash
python3 -m backend.scrapers.brokers.transwestern.scraper
```

This will:
1. Navigate to the Transwestern properties page
2. Extract property listings
3. Save the HTML content and screenshots
4. Save the extracted properties to JSON files in `data/extracted/transwestern/`
5. Save all properties to the Supabase database

## Implementation Details

The scraper uses a multi-layered approach to extract property data:

1. **Page Interaction**: Attempts to interact with the page by clicking on search buttons or filters to load property data
2. **JavaScript Extraction**: Tries to extract property data directly from the page's JavaScript data
3. **HTML Parsing**: Falls back to parsing the HTML content if JavaScript extraction fails
4. **Link Analysis**: As a final fallback, extracts property data from links on the page

## Results

The scraper successfully extracts over 1900 properties from the Transwestern website and saves them to the Supabase database. Each property includes:

- Title
- Description (when available)
- Link to the property page
- Location (when available)
- Property type
- Price (when available)
- Square footage (when available)
- Status
- Image URL (when available)

## Dependencies

- `asyncio`: For asynchronous operations
- `logging`: For logging information and errors
- `datetime`: For timestamping
- `BeautifulSoup`: For HTML parsing
- `MCPClient`: For browser automation
- `ScraperDataStorage`: For data storage operations
