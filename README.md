# Lynnapse

A comprehensive web scraping system for university programs, faculty, and research lab websites.

## Project Overview

Lynnapse is a Python-based web scraping application designed to systematically collect and organize information about university academic programs, faculty members, and their associated research laboratories. This tool provides researchers, academic administrators, and data analysts with a comprehensive view of university research landscapes.

## Features

- **Three-layer scraping strategy** for robust data collection:
  - Playwright-based HTML scraper for dynamic content
  - Fallback requests + BeautifulSoup scraper
  - Firecrawl API integration (max 3 tries)
- **Config-driven scraping** using YAML seed files
- **MongoDB storage** with optimized schemas
- **Prefect 2 orchestration** for workflow management
- **Command-line interface** with rich progress indicators
- **Comprehensive data models** for programs, faculty, lab sites, and scrape jobs
- **Real-time job tracking** and status monitoring
- **Built-in retry logic** and error handling

## Architecture

This project follows a layered architecture with the following components:

- **Scraping Layer**: Three-tier web scraping system (Playwright → Requests → Firecrawl)
- **Data Layer**: MongoDB with async Motor driver and Pydantic models
- **Orchestration Layer**: Prefect 2 workflows for job scheduling and monitoring
- **Configuration Layer**: YAML-based university and program definitions
- **CLI Layer**: Typer-based command-line interface with Rich output

## Tech Stack

### Core Technologies
- **Python 3.9+** - Primary programming language
- **MongoDB** - Document database for storing scraped data
- **Prefect 2** - Modern workflow orchestration
- **Playwright** - Browser automation for dynamic content
- **Pydantic** - Data validation and settings management

### Web Scraping
- **Playwright** - Primary scraper for JavaScript-heavy sites
- **Requests + BeautifulSoup** - Fallback scraper for static content
- **Goose3** - Article text extraction
- **Firecrawl** - AI-powered scraping API fallback

### CLI & UI
- **Typer** - Command-line interface framework
- **Rich** - Terminal formatting and progress bars
- **YAML** - Configuration file format

## Data Models

### Program
University academic programs with metadata:
- University name, program name, department, college
- Program URLs and faculty directory links
- Degree types and specializations
- Contact information

### Faculty
Faculty member profiles:
- Basic information (name, title, department)
- Contact details and office location
- Research interests and specializations
- Academic profiles (Google Scholar, ORCID, etc.)
- Lab information and recent publications

### LabSite
Research laboratory websites:
- Lab details (name, PI, members)
- Research areas and current projects
- Equipment and facilities
- Publications and software/datasets
- Student and collaboration opportunities
- Full page content analysis

### ScrapeJob
Job tracking and monitoring:
- Job identification and configuration
- Status tracking with progress indicators
- Timing and performance metrics
- Error tracking and retry logic
- Resource usage monitoring

## Getting Started

### Prerequisites

- Python 3.9 or higher
- MongoDB (local or cloud instance)
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lynnapse-scraper.git
   cd lynnapse-scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

5. Set up environment variables:
   ```bash
   cp .env.template .env
   # Edit .env with your configuration
   ```

6. Initialize the database:
   ```bash
   python -m lynnapse.cli init-db
   ```

### Quick Start

1. **List available universities:**
   ```bash
   python -m lynnapse.cli list-universities
   ```

2. **Create a new university seed:**
   ```bash
   python -m lynnapse.cli create-seed "Your University"
   # Edit the generated seed file in seeds/
   ```

3. **Test database connection:**
   ```bash
   python -m lynnapse.cli test-db
   ```

4. **Run a scraping job:**
   ```bash
   python -m lynnapse.cli scrape "University of Arizona" --program "Psychology" --verbose
   ```

### Docker Setup

1. **Using Docker Compose:**
   ```bash
   docker-compose up -d
   ```

This will start:
- MongoDB instance
- Lynnapse application container

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Database
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=lynnapse

# Scraping
PLAYWRIGHT_HEADLESS=true
PLAYWRIGHT_TIMEOUT=30000
MAX_CONCURRENT_REQUESTS=3
REQUEST_DELAY=1.0

# Firecrawl (optional)
FIRECRAWL_API_KEY=your_api_key_here

# Prefect (optional)
PREFECT_API_URL=your_prefect_url
PREFECT_API_KEY=your_prefect_key

# Logging
LOG_LEVEL=INFO
DEBUG=false
```

### University Seed Files

Create YAML configuration files in the `seeds/` directory:

```yaml
name: University of Arizona
base_url: https://arizona.edu
programs:
  - name: Psychology
    department: Psychology
    college: College of Science
    program_url: https://psychology.arizona.edu/graduate
    faculty_directory_url: https://psychology.arizona.edu/people/faculty
    program_type: graduate
    selectors:
      faculty_links: ".faculty-list a, .people-list a"
      faculty_name: "h1, .name, .faculty-name"
      faculty_title: ".title, .position"
      faculty_email: "a[href^='mailto:']"
      research_interests: ".research-interests, .interests"

scraping_config:
  user_agent: "Mozilla/5.0 (compatible; LynnapseBot/1.0)"
  wait_for_selector: ".content, .main"
  timeout: 30

rate_limit_delay: 2.0
max_concurrent_requests: 2
max_retries: 3
retry_delay: 5.0
```

## Usage Examples

### CLI Commands

```bash
# List available universities
python -m lynnapse.cli list-universities

# Scrape a specific university
python -m lynnapse.cli scrape "University of Arizona" --verbose

# Scrape a specific program
python -m lynnapse.cli scrape "University of Arizona" --program "Psychology"

# Create new seed file
python -m lynnapse.cli create-seed "Stanford University"

# Test database connection
python -m lynnapse.cli test-db

# Initialize database indexes
python -m lynnapse.cli init-db

# Show version
python -m lynnapse.cli version
```

### Python API

```python
import asyncio
from lynnapse.scrapers import ScraperOrchestrator
from lynnapse.config import get_seed_loader

async def main():
    # Load configuration
    seed_loader = get_seed_loader()
    university_config = seed_loader.get_university_config("University of Arizona")
    
    # Run scraper
    orchestrator = ScraperOrchestrator()
    result = await orchestrator.scrape_university(university_config)
    
    print(f"Scraped {result['faculty_count']} faculty members")

asyncio.run(main())
```

## Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=lynnapse

# Run specific test category
pytest tests/scrapers/
pytest tests/models/
```

## Project Structure

```
lynnapse-scraper/
├── lynnapse/                 # Main package
│   ├── models/              # Pydantic data models
│   ├── scrapers/            # Three-layer scraping system
│   ├── db/                  # MongoDB connection and repositories
│   ├── config/              # Settings and seed loading
│   ├── flows/               # Prefect workflow definitions
│   └── cli.py               # Command-line interface
├── seeds/                   # University configuration files
├── tests/                   # Test suite
├── docker-compose.yml       # Docker setup
├── requirements.txt         # Python dependencies
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Playwright](https://playwright.dev/) for browser automation
- [Prefect](https://prefect.io/) for workflow orchestration
- [MongoDB](https://mongodb.com/) for document storage
- [Pydantic](https://pydantic-docs.helpmanual.io/) for data validation
- [Typer](https://typer.tiangolo.com/) for CLI framework