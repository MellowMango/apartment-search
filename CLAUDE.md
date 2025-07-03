# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key Commands

### Core Development Commands
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting and linting
black .
isort .
ruff check .
```

### Faculty Scraping Commands
```bash
# Adaptive scraping (main command)
python -m lynnapse.cli.adaptive_scrape "University Name" -d department --lab-discovery -v

# Link processing with AI assistance
python -m lynnapse.cli.process_links --input faculty_data.json --mode social --ai-assistance

# Link enrichment and validation
python -m lynnapse.cli.enrich_links faculty_data.json --analysis comprehensive --verbose

# Enhanced data enrichment (for sparse data)
python -m lynnapse.cli.enhance_data faculty_data.json --verbose

# Website validation
python -m lynnapse.cli.validate_websites

# University database management
python -m lynnapse.cli.university_database
```

### Web Interface
```bash
# Start web interface
python -m lynnapse.web.run

# Access at http://localhost:8000 or http://localhost:8001
```

**Web Interface Features:**
- **Interactive Scraping**: Point-and-click university scraping
- **Results Management**: View, filter, and export scraped data
- **CLI Commands Tab**: Learn and execute CLI commands directly from the web interface
- **Real-time Progress**: Live scraping progress and detailed logs

### Docker Commands
```bash
# Start all services
docker-compose up -d

# Access web interface at http://localhost:8000
# MongoDB available at localhost:27017
```

## Architecture Overview

Lynnapse is a comprehensive academic faculty intelligence platform with adaptive scraping capabilities. The system consists of several key components:

### Core Components (`lynnapse/core/`)
- **AdaptiveFacultyCrawler**: Main orchestrator for faculty extraction with university pattern detection
- **UniversityAdapter**: Discovers and analyzes university website structures automatically
- **SmartLinkReplacer**: AI-assisted academic link discovery and social media replacement
- **DataCleaner**: Advanced text cleaning, email extraction, and research area detection
- **LinkHeuristics**: Intelligent lab website discovery and academic relevance scoring
- **LLMAssistant**: OpenAI integration for enhanced link processing

### CLI Interface (`lynnapse/cli/`)
- **adaptive_scrape.py**: Main adaptive scraping command
- **process_links.py**: Link processing and social media replacement
- **enrich_links.py**: Academic link enrichment and validation
- **validate_websites.py**: Website quality assessment
- **university_database.py**: University database management

### Data Models (`lynnapse/models/`)
- **Faculty**: Enhanced faculty profile with multi-link support and research intelligence
- **Lab**: Research lab associations and team mapping
- **Program**: Academic program structures
- **ScrapeJob**: Job tracking and metadata

### Web Interface (`lynnapse/web/`)
- **FastAPI-based** web interface with Jinja2 templates
- **Real-time progress tracking** for scraping operations
- **Interactive faculty data management** and export capabilities

## Key Features

### Adaptive Faculty Extraction
- **Multi-Link Support**: Extracts university profiles, Google Scholar, personal websites, lab sites per faculty
- **Faculty Deduplication**: Intelligent cross-department detection and merging
- **Lab Association Detection**: Research groups, centers, and collaborative initiatives
- **Research Intelligence**: Expertise areas, publication tracking, collaboration networks

### Smart Link Processing
- **Social Media Replacement**: AI-assisted replacement of social media links with academic sources
- **Link Categorization**: Comprehensive classification (university_profile, google_scholar, personal_website, lab_website, social_media)
- **Quality Scoring**: Advanced relevance and authenticity assessment
- **Academic Discovery**: Pattern-based exploration of university domains

### University Support
- **Fully Optimized**: Carnegie Mellon, Stanford, University of Arizona
- **Adaptive Discovery**: Works with any university through automatic structure detection
- **Subdomain Support**: Handles complex university architectures
- **Success Rates**: 95%+ email capture, 85%+ personal website detection

## Development Guidelines

### Adding New Universities
1. The adaptive scraper should handle most universities automatically
2. For complex cases, add university-specific logic to `lynnapse/scrapers/university/`
3. Test with: `python -m lynnapse.cli.adaptive_scrape "University Name" -d department -v`

### Working with Faculty Data
- Faculty objects support multiple links, departments, and research associations
- Use `AdaptiveFacultyCrawler` for comprehensive extraction
- All data is stored in MongoDB with rich metadata

### Link Processing
- Use `SmartLinkReplacer` for social media replacement
- Enable AI assistance with `OPENAI_API_KEY` environment variable
- Process costs ~$0.01-0.02 per faculty member with AI assistance

### Enhanced Data Enrichment
- Use `enhance_data` CLI for sparse faculty data that lacks research interests, biographies, or contact info
- Automatically scrapes individual profile pages to extract missing information
- Finds additional academic links (personal websites, Google Scholar, lab sites)
- Significantly improves data quality for universities with minimal initial extraction

### Testing
- Run `pytest` for unit tests
- Use `lynnapse test` for component-specific testing
- Test database connectivity with `lynnapse test --component mongo`

## Environment Variables
```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=lynnapse

# OpenAI Configuration (for AI-assisted link processing)
OPENAI_API_KEY=your-openai-api-key-here

# Scraping Configuration
USER_AGENT="Lynnapse Academic Scraper 1.0"
REQUEST_DELAY=1.0
CONCURRENT_REQUESTS=5
```

## Important Implementation Details

### Asynchronous Architecture
- All scrapers use async/await patterns with httpx and Playwright
- Concurrent request handling with configurable rate limiting
- Robust error recovery and retry mechanisms

### Data Cleaning and Validation
- Advanced email extraction with multiple fallback strategies
- Research interest parsing and classification
- Phone number extraction and formatting
- Comprehensive text cleaning and normalization

### Performance Characteristics
- **Throughput**: ~10 faculty/second with detailed profile extraction
- **Memory Usage**: ~100MB per scraping session
- **Success Rates**: 100% faculty discovery, 95%+ email extraction on optimized universities

### Security and Ethics
- Respects robots.txt and rate limiting
- Only scrapes publicly available information
- Clear user-agent identification
- Responsible scraping practices