# Acquire Apartments - Tech Stack

## Overview

This document outlines the technology stack and architecture for the Acquire Apartments (acquire-apartments.com) platform. It consolidates key technical decisions and serves as a reference for development.

## Core Technologies

### Frontend
- **Framework**: Next.js (React-based framework)
- **State Management**: React Context API
- **Styling**: Tailwind CSS or Material-UI
- **Map Component**: react-leaflet with Mapbox
  - Selected for long-term flexibility with custom layers (flood zones, opportunity zones, demographics)
  - Provides excellent support for vector tile overlays and data visualization
- **Routing**: Next.js built-in routing
- **API Communication**: Fetch API, Supabase Client
- **Real-time Updates**: Socket.IO client

### Backend
- **API Framework**: FastAPI (Python)
- **Authentication**: Supabase Auth (email and OAuth)
- **Background Tasks**: Celery with PostgreSQL (Supabase)
  - Using Supabase PostgreSQL as both broker and result backend
  - Eliminates need for Redis and simplifies infrastructure
- **Real-time Updates**: Socket.IO server
- **Email Notifications**: SendGrid
- **Payment Processing**: Stripe
- **Browser Automation**: Model Context Protocol (MCP) servers
  - [Firecrawl MCP Server](https://github.com/mendableai/firecrawl-mcp-server) (primary option)
  - [MCP-Playwright](https://github.com/executeautomation/mcp-playwright) (alternative)
  - [MCP-Puppeteer](https://github.com/modelcontextprotocol/servers/tree/HEAD/src/puppeteer) (alternative)
- **Error Tracking**: Sentry

### Databases
- **Primary Database**: PostgreSQL via Supabase
  - Stores property listings, user data, and core application data
  - Handles authentication and user management
  - Serves as message broker and result backend for Celery
  
- **Graph Database**: Neo4j Aura
  - Models relationships between properties, brokers, and brokerages
  - Enables complex graph-based queries and analysis
  - Syncs with Supabase via Celery tasks

### Data Aggregation
- **Web Scraping**: 
  - Organized in modular `backend/scrapers/` directory
  - Model Context Protocol (MCP) servers for browser automation
  - MCP-Playwright for JavaScript-heavy broker websites
  - LLM-guided data extraction for adaptive scraping
  - Available MCP implementations:
    - [Firecrawl MCP Server](https://github.com/mendableai/firecrawl-mcp-server): Specialized web scraping with built-in rate limiting and batch processing
    - [MCP-Playwright](https://github.com/executeautomation/mcp-playwright): General-purpose browser automation with Playwright
    - [MCP-Puppeteer](https://github.com/modelcontextprotocol/servers/tree/HEAD/src/puppeteer): General-purpose browser automation with Puppeteer
  - Structured directory organization:
    - Core utilities in `backend/scrapers/core/`
    - Broker-specific scrapers in `backend/scrapers/brokers/<broker_name>/`
    - Command-line interface in `backend/scrapers/run_scraper.py`
    - Data stored in organized `data/` directory (gitignored)

- **Data Cleaning System**:
  - Comprehensive system for cleaning property data in `backend/data_cleaning/` directory
  - Two-step approval process to ensure no write actions occur without explicit approval
  - Property deduplication using fuzzy matching on addresses, names, and other attributes
  - Data standardization for normalizing property types, statuses, and other categorical fields
  - Data validation to ensure critical fields contain valid data
  - Test property detection to identify and remove test/example properties
  - Command-line interface in `backend/data_cleaning/review_and_approve.py` for reviewing and approving actions
  
- **Email Processing**:
  - Python's imaplib and email libraries
  - pytesseract for OCR on email images
  
- **Email Notifications**:
  - SendGrid for transactional emails and notifications
  - Email templates for consistent messaging

### Deployment
- **Backend**: Heroku (web dyno + Celery worker)
- **Frontend**: Vercel or Heroku
- **Database**: 
  - Supabase (managed PostgreSQL)
  - Neo4j Aura (managed Neo4j)

## System Architecture

### Component Overview
1. **Frontend (Next.js SPA)**:
   - Interactive map showing Austin multifamily property listings
   - Property listing sidebar and detail views
   - Search and filter functionality
   - Admin interface for managing data

2. **Backend (FastAPI)**:
   - RESTful API endpoints for CRUD operations
   - Authentication and authorization
   - Background task management
   - Integration with Supabase and Neo4j
   - MCP server orchestration for web scraping

3. **Databases**:
   - Supabase (PostgreSQL): Primary data storage and Celery task queue
   - Neo4j Aura: Graph database for relationship modeling

4. **Data Aggregation**:
   - MCP-based browser automation for broker websites
   - Email scraping system for broker emails
   - OCR processing for images in emails

### Data Flow
1. Data is collected via MCP-powered browser automation (organized in `backend/scrapers/` modules) and email processing
2. Scraped data is stored in organized directories under `data/` for debugging and analysis
3. Processed data is stored in Supabase
4. Celery tasks (using PostgreSQL as broker) sync relevant data to Neo4j for relationship modeling
5. FastAPI serves data to the frontend
6. Real-time updates are pushed via Socket.IO when data changes

## MCP Server Comparison

### Firecrawl MCP Server (Primary Option)
- **Repository**: [mendableai/firecrawl-mcp-server](https://github.com/mendableai/firecrawl-mcp-server)
- **Advantages**:
  - Purpose-built for web scraping with specialized tools
  - Built-in rate limiting and batch processing
  - Efficient parallel processing for multiple URLs
  - Advanced extraction capabilities with LLM integration
  - Structured data extraction with schema validation
  - Comprehensive error handling and retry mechanisms

### MCP-Playwright (Alternative)
- **Repository**: [executeautomation/mcp-playwright](https://github.com/executeautomation/mcp-playwright)
- **Advantages**:
  - General-purpose browser automation
  - Flexible for various automation tasks
  - Uses Playwright for cross-browser compatibility

### MCP-Puppeteer (Alternative)
- **Repository**: [modelcontextprotocol/servers/puppeteer](https://github.com/modelcontextprotocol/servers/tree/HEAD/src/puppeteer)
- **Advantages**:
  - General-purpose browser automation
  - Uses Puppeteer for Chrome/Chromium automation
  - Part of the official Model Context Protocol implementation

## Key Features

1. **Interactive Map**: Display of all active multifamily property listings in Austin
2. **Property Details**: Comprehensive information about each property
3. **Automated Data Aggregation**: From broker emails and websites
4. **Real-time Updates**: For property status changes
5. **Search and Filter**: By property characteristics
6. **Admin Interface**: For managing data and handling missing information
7. **Graph-based Analysis**: Using Neo4j for relationship queries
8. **Email Notifications**: For property updates, missing information requests, and user account management
9. **Subscription Management**: Paid access via Stripe with monthly and annual plans

## Development Workflow

1. Local development using Docker Compose
2. CI/CD pipeline for automated testing and deployment GitHub connected to Heroku for deployment
3. Staging environment for testing before production
4. Monitoring and logging for production issues

## Security Considerations

1. Authentication via Supabase
2. HTTPS for all communications
3. Secure storage of credentials in environment variables
4. Role-based access control for admin functions
5. PCI compliance for payment processing via Stripe

---

This tech stack is designed to provide a scalable, maintainable solution for Acquire Apartments (acquire-apartments.com), with a focus on data accuracy, real-time updates, and user experience. 