# 📚 Lynnapse API Reference

## Web Interface API

### API Endpoints

#### GET `/`
Web interface home page with features overview and statistics dashboard.

#### GET `/scrape`
Scraping interface page with configuration form.

#### GET `/results`
Results page displaying faculty data with search and filtering.

#### GET `/api/stats`
Get statistics about the scraping system.

**Response:**
```json
{
  "total_scraped": 40,
  "success_rate": 95.5,
  "email_capture_rate": 89.2,
  "website_detection_rate": 67.8
}
```

#### POST `/api/scrape`
Start a faculty scraping job.

**Request Body:**
```json
{
  "source": "arizona-psychology",  // or "custom"
  "custom_url": "https://example.edu/faculty",  // required if source is "custom"
  "include_profiles": true
}
```

**Response:**
```json
{
  "message": "Faculty scraping completed successfully!",
  "faculty_count": 40,
  "filename": "web_scrape_20250623_141742.json"
}
```

#### GET `/api/results`
Get preview of latest scraping results.

**Response:**
```json
{
  "files": ["web_scrape_20250623_141742.json"],
  "total_files": 1,
  "preview": [
    {
      "name": "Dr. John Smith",
      "title": "Professor of Psychology",
      "email": "jsmith@arizona.edu",
      "website": "https://psychology.arizona.edu/person/john-smith"
    }
  ],
  "total_count": 40
}
```

#### GET `/api/results/{filename}`
Get complete faculty data from a specific scraping file.

**Parameters:**
- `filename`: Name of the JSON result file

**Response:**
```json
{
  "faculty": [
    {
      "name": "Dr. John Smith",
      "title": "Professor of Psychology",
      "email": "jsmith@arizona.edu",
      "website": "https://psychology.arizona.edu/person/john-smith",
      "research_interests": ["Cognitive Psychology", "Memory"],
      "personal_website": "https://johnsmith.arizona.edu",
      "lab_website": "https://coglab.arizona.edu",
      "office_location": "Psychology Building 401",
      "biography": "Dr. Smith's research focuses on cognitive processes..."
    }
  ],
  "count": 40,
  "filename": "web_scrape_20250623_141742.json"
}
```

## CLI Commands

### Core Commands

#### `scrape-university`
Scrape faculty data from a university using specialized scrapers.

```bash
lynnapse scrape-university UNIVERSITY [OPTIONS]
```

**Arguments:**
- `UNIVERSITY`: University identifier (e.g., 'arizona-psychology')

**Options:**
- `--format, -f`: Output format (json, mongodb) [default: json]
- `--output, -o`: Output file path [optional]
- `--profiles`: Include detailed faculty profiles (slower) [default: false]
- `--verbose, -v`: Enable verbose logging [default: false]

**Examples:**
```bash
# Basic scraping
lynnapse scrape-university arizona-psychology

# Custom output file
lynnapse scrape-university arizona-psychology --output faculty_data.json

# Detailed profiles with verbose logging
lynnapse scrape-university arizona-psychology --profiles --verbose
```

#### `test-scraper`
Test university scrapers with sample data.

```bash
lynnapse test-scraper [UNIVERSITY] [OPTIONS]
```

**Arguments:**
- `UNIVERSITY`: University scraper to test [default: arizona-psychology]

**Options:**
- `--save/--no-save`: Save test results to file [default: true]

**Examples:**
```bash
# Test with output
lynnapse test-scraper arizona-psychology

# Test without saving
lynnapse test-scraper arizona-psychology --no-save
```

#### `list-universities`
List available university scrapers.

```bash
lynnapse list-universities
```

**Output:**
```
University Scrapers:
• arizona-psychology - University of Arizona Psychology Department
  Captures: Faculty profiles, personal websites, lab information
```

#### `test-db`
Test database connection.

```bash
lynnapse test-db
```

**Output:**
```
✓ Database connection successful!
Database: lynnapse
```

#### `init`
Initialize Lynnapse configuration and database.

```bash
lynnapse init
```

#### `web`
Start the web interface for visual scraping and results viewing.

```bash
lynnapse web [OPTIONS]
```

**Options:**
- `--host`: Host to bind to [default: 0.0.0.0]
- `--port`: Port to bind to [default: 8000]

**Examples:**
```bash
# Start on default port
lynnapse web

# Custom host and port
lynnapse web --host 127.0.0.1 --port 8080
```

**Features:**
- Real-time scraping progress with animated progress bars
- Complete faculty data viewing with search and filtering
- Interactive results table with sortable columns
- JSON export functionality
- Live statistics dashboard

### Legacy Commands

#### `scrape` (Legacy)
Legacy seed-based scraper (requires YAML configuration).

```bash
lynnapse scrape UNIVERSITY [OPTIONS]
```

#### `create-seed`
Create a new YAML seed configuration file.

```bash
lynnapse create-seed UNIVERSITY_NAME [OPTIONS]
```

## Python API

### University Scrapers

#### BaseUniversityScraper

Base class for all university scrapers.

```python
from lynnapse.scrapers.university.base_university import BaseUniversityScraper

class CustomUniversityScraper(BaseUniversityScraper):
    def __init__(self):
        super().__init__(
            university_name="Custom University",
            base_url="https://custom.edu",
            department="Computer Science"
        )
    
    async def scrape_faculty_list(self) -> List[Dict]:
        """Implement faculty list scraping logic."""
        pass
    
    async def scrape_faculty_profile(self, profile_url: str) -> Optional[Dict]:
        """Implement detailed profile scraping logic."""
        pass
```

**Key Methods:**

##### `async scrape_all_faculty(include_detailed_profiles: bool = True) -> List[Dict]`
Main scraping method that combines faculty list and detailed profiles.

**Parameters:**
- `include_detailed_profiles`: Whether to fetch detailed profile information

**Returns:** List of faculty dictionaries

**Example:**
```python
async with ArizonaPsychologyScraper() as scraper:
    faculty_data = await scraper.scrape_all_faculty(include_detailed_profiles=True)
    print(f"Scraped {len(faculty_data)} faculty members")
```

##### `fetch_page(url: str) -> str`
Fetch a single page with error handling.

**Parameters:**
- `url`: URL to fetch

**Returns:** HTML content as string

##### `is_personal_website(url: str, faculty_name: str = None) -> bool`
Determine if a URL is likely a personal academic website.

**Parameters:**
- `url`: URL to analyze
- `faculty_name`: Faculty member's name for context

**Returns:** Boolean indicating if URL is a personal website

#### ArizonaPsychologyScraper

Specialized scraper for University of Arizona Psychology Department.

```python
from lynnapse.scrapers.university.arizona_psychology import ArizonaPsychologyScraper

async def scrape_arizona_psychology():
    async with ArizonaPsychologyScraper() as scraper:
        # Quick scrape (no detailed profiles)
        faculty_list = await scraper.scrape_faculty_list()
        
        # Full scrape with detailed profiles
        detailed_faculty = await scraper.scrape_all_faculty(include_detailed_profiles=True)
        
        return detailed_faculty
```

### Data Models

#### Faculty Model

```python
from lynnapse.models.faculty import Faculty

# Faculty data structure
faculty_dict = {
    "name": str,                           # Required
    "title": Optional[str],                # Academic title/position
    "email": Optional[str],                # Contact email
    "phone": Optional[str],                # Primary phone
    "office_phone": Optional[str],         # Office phone
    "lab_phone": Optional[str],            # Lab phone
    "pronouns": Optional[str],             # Preferred pronouns
    "research_areas": List[str],           # Research areas/keywords
    "research_interests": List[str],       # Detailed research interests
    "lab_name": Optional[str],             # Laboratory name
    "office_location": Optional[str],      # Physical office location
    "bio": Optional[str],                  # Biography/description
    "education": List[str],                # Educational background
    "personal_website": Optional[str],     # Personal academic website ⭐
    "lab_website": Optional[str],          # Laboratory website
    "university_profile_url": Optional[str], # University profile page
    "image_url": Optional[str],            # Faculty headshot URL
    "scraped_at": str,                     # ISO timestamp
    "university": str,                     # University name
    "department": str                      # Department name
}
```

### Database Integration

#### MongoDB Client

```python
from lynnapse.db import get_client

async def database_example():
    # Get database client
    client = await get_client()
    
    # Health check
    healthy = await client.health_check()
    if healthy:
        print("Database connected!")
    
    # Access collections
    db = client.database
    faculty_collection = db.faculty
```

### Configuration

#### Settings

```python
from lynnapse.config import get_settings

# Get application settings
settings = get_settings()

print(f"MongoDB URL: {settings.mongodb_url}")
print(f"Debug mode: {settings.debug}")
```

#### Environment Variables

```python
import os

# Database configuration
MONGODB_URL = os.getenv('MONGODB_URL', 'mongodb://localhost:27017/lynnapse')
MONGODB_DATABASE = os.getenv('MONGODB_DATABASE', 'lynnapse')

# Scraping configuration
PLAYWRIGHT_HEADLESS = os.getenv('PLAYWRIGHT_HEADLESS', 'true') == 'true'
MAX_CONCURRENT_REQUESTS = int(os.getenv('MAX_CONCURRENT_REQUESTS', '3'))
REQUEST_DELAY = float(os.getenv('REQUEST_DELAY', '1.0'))

# Application settings
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
DEBUG = os.getenv('DEBUG', 'false') == 'true'
```

## Data Formats

### Faculty JSON Output

```json
{
  "name": "Dr. Jane Smith",
  "title": "Associate Professor, Computer Science",
  "email": "jsmith@university.edu",
  "office_phone": "555-123-4567",
  "pronouns": "She/Her",
  "research_areas": ["Machine Learning", "Natural Language Processing"],
  "lab_name": "AI Research Laboratory",
  "office_location": "Computer Science Building, Room 301",
  "personal_website": "https://cs.university.edu/~jsmith",
  "university_profile_url": "https://cs.university.edu/people/jane-smith",
  "image_url": "https://cs.university.edu/images/faculty/jsmith.jpg",
  "scraped_at": "2024-12-23T10:30:00.000Z",
  "university": "Sample University",
  "department": "Computer Science"
}
```

### Scraping Statistics

```json
{
  "total_faculty": 40,
  "with_email": 40,
  "with_personal_website": 40,
  "with_lab": 19,
  "with_phone": 34,
  "scraping_duration": 2.3,
  "success_rate": 100.0
}
```

## Error Handling

### Common Errors

#### `ScrapingError`
General scraping failure.

```python
try:
    faculty_data = await scraper.scrape_faculty_list()
except ScrapingError as e:
    print(f"Scraping failed: {e}")
```

#### `DatabaseConnectionError`
Database connectivity issues.

```python
try:
    client = await get_client()
    await client.health_check()
except DatabaseConnectionError as e:
    print(f"Database error: {e}")
```

#### `ValidationError`
Data validation failures.

```python
from pydantic import ValidationError

try:
    faculty = Faculty(**faculty_data)
except ValidationError as e:
    print(f"Invalid faculty data: {e}")
```

### Retry Logic

Scrapers include automatic retry with exponential backoff:

```python
# Built-in retry configuration
max_retries = 3
base_delay = 1.0
max_delay = 10.0

for attempt in range(max_retries):
    try:
        result = await fetch_page(url)
        break
    except Exception:
        delay = min(base_delay * (2 ** attempt), max_delay)
        await asyncio.sleep(delay)
```

## Performance Optimization

### Concurrent Scraping

```python
import asyncio

# Control concurrency with semaphore
semaphore = asyncio.Semaphore(3)  # Max 3 concurrent requests

async def scrape_with_semaphore(url: str):
    async with semaphore:
        return await scraper.scrape_page(url)

# Process multiple URLs concurrently
tasks = [scrape_with_semaphore(url) for url in urls]
results = await asyncio.gather(*tasks)
```

### Rate Limiting

```python
import asyncio

async def rate_limited_scraping():
    for url in urls:
        result = await scraper.scrape_page(url)
        # Built-in rate limiting
        await asyncio.sleep(1.0)  # 1 second delay
```

### Memory Management

```python
# Use async context managers for proper cleanup
async with ArizonaPsychologyScraper() as scraper:
    # HTTP sessions automatically closed
    faculty_data = await scraper.scrape_all_faculty()
    # Resources cleaned up on exit
```

## Testing

### Unit Tests

```python
import pytest
from lynnapse.scrapers.university.arizona_psychology import ArizonaPsychologyScraper

@pytest.mark.asyncio
async def test_faculty_scraping():
    async with ArizonaPsychologyScraper() as scraper:
        faculty_list = await scraper.scrape_faculty_list()
        
        assert len(faculty_list) > 0
        assert all('name' in faculty for faculty in faculty_list)
        assert all('email' in faculty for faculty in faculty_list)

@pytest.mark.asyncio
async def test_personal_website_detection():
    scraper = ArizonaPsychologyScraper()
    
    # Test positive cases
    assert scraper.is_personal_website("https://psychology.arizona.edu/~jsmith", "John Smith")
    assert scraper.is_personal_website("https://psychology.arizona.edu/people/jane-doe", "Jane Doe")
    
    # Test negative cases
    assert not scraper.is_personal_website("https://facebook.com/profile", "Anyone")
    assert not scraper.is_personal_website("mailto:test@email.com", "Anyone")
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_end_to_end_scraping():
    """Test complete scraping workflow."""
    async with ArizonaPsychologyScraper() as scraper:
        # Test faculty list scraping
        faculty_list = await scraper.scrape_faculty_list()
        assert len(faculty_list) > 30  # Expect at least 30 faculty
        
        # Test personal website detection
        websites_found = sum(1 for f in faculty_list if f.get('personal_website'))
        assert websites_found > 35  # Expect high success rate
        
        # Test data quality
        for faculty in faculty_list[:5]:  # Check first 5
            assert faculty['name']
            assert faculty['university'] == "University of Arizona"
            assert faculty['department'] == "Psychology"
```

## Docker API

### Container Management

```bash
# Build containers
docker-compose build

# Start services
docker-compose up -d

# Execute commands in container
docker-compose exec lynnapse python -m lynnapse.cli scrape-university arizona-psychology

# View logs
docker-compose logs -f lynnapse

# Stop services
docker-compose down
```

### Health Checks

```bash
# Check container health
docker-compose ps

# Manual health check
docker-compose exec lynnapse python -c "from lynnapse.cli import app; print('OK')"
```

### Volume Management

```bash
# View generated data
ls -la output/

# Access MongoDB data
docker-compose exec mongodb mongosh lynnapse --eval "db.faculty.countDocuments()"
```

## Enhanced Link Processing API

### CLI Commands

#### `process-links`
Process faculty links with enhanced categorization and academic source discovery.

```bash
python -m lynnapse.cli.process_links [OPTIONS]
```

**Options:**
- `--input, -i`: Input JSON file with faculty data (required)
- `--output, -o`: Output JSON file for processed results [optional]
- `--mode, -m`: Processing mode [choices: full, social, labs, categorize] [default: full]
- `--max-concurrent`: Maximum concurrent operations [default: 3]
- `--timeout`: Timeout for network operations [default: 30]
- `--verbose, -v`: Verbose output with detailed results
- `--ai-assistance`: Use GPT-4o-mini for AI-assisted link discovery
- `--openai-key`: OpenAI API key for AI assistance

**Processing Modes:**
- `full`: Complete processing (categorization + social replacement + lab enrichment)
- `social`: Focus on social media detection and replacement
- `labs`: Focus on lab website discovery and enrichment
- `categorize`: Link categorization only

**Examples:**
```bash
# Traditional social media replacement
python -m lynnapse.cli.process_links --input faculty_data.json --mode social

# AI-assisted processing with verbose output
python -m lynnapse.cli.process_links --input faculty_data.json --mode social --ai-assistance --verbose

# Full processing pipeline
python -m lynnapse.cli.process_links --input faculty_data.json --mode full --ai-assistance
```

### Python API

#### SmartLinkReplacer Class

**Smart academic link discovery and social media replacement.**

```python
from lynnapse.core.smart_link_replacer import SmartLinkReplacer, smart_replace_social_media_links

# Initialize with AI assistance
async with SmartLinkReplacer(openai_api_key="your-key", enable_ai_assistance=True) as replacer:
    enhanced_faculty, report = await replacer.replace_social_media_links(faculty_list)

# Convenience function
enhanced_faculty, report = await smart_replace_social_media_links(
    faculty_list, 
    openai_api_key="your-key"
)
```

**Methods:**

##### `async replace_social_media_links(faculty_list: List[Dict]) -> Tuple[List[Dict], Dict]`
Replace social media links with academic alternatives.

**Parameters:**
- `faculty_list`: List of faculty dictionaries with link validation data

**Returns:**
- `enhanced_faculty`: Faculty list with replacement links
- `report`: Processing report with success metrics

**Report Structure:**
```python
{
    'total_faculty': 43,
    'faculty_with_social_media': 18,
    'faculty_with_replacements': 18,
    'total_replacements_made': 18,
    'replacement_success_rate': 1.0,  # 100%
    'processing_time_seconds': 25.0,
    'ai_assistance_enabled': True
}
```

#### Link Processing Data Models

**Faculty Data with Link Processing:**
```python
{
    "name": "Dr. Sarah Johnson",
    "university": "Carnegie Mellon University",
    "department": "Psychology",
    "profile_url": "https://www.cmu.edu/dietrich/psychology/directory/johnson.html",
    "personal_website": "https://scholar.google.com/citations?user=ABC123",  # Replaced from Twitter
    "research_interests": "cognitive neuroscience, brain imaging",
    
    # Link validation results
    "link_quality_score": 0.89,
    "profile_url_validation": {
        "type": "university_profile",
        "is_accessible": true,
        "confidence": 0.85,
        "title": "Sarah Johnson - Department of Psychology"
    },
    "personal_website_validation": {
        "type": "google_scholar",
        "is_accessible": true,
        "confidence": 0.95,
        "title": "Sarah Johnson - Google Scholar"
    }
}
```

### Performance Characteristics

#### Success Rates
- **Social Media Detection**: 95%+ accuracy across 15+ platforms
- **Academic Link Discovery**: 180+ candidates per faculty member
- **Replacement Success**: 100% on Carnegie Mellon Psychology data (18/18)
- **Link Categorization**: 85%+ precision across all link types

#### Processing Speed
- **Traditional Method**: ~1.4 seconds per faculty member
- **AI-Assisted Method**: ~2.0 seconds per faculty member
- **Batch Processing**: Concurrent operations with configurable limits

#### Cost Analysis
- **Traditional Method**: Free (no external API calls)
- **AI-Assisted Method**: ~$0.01-0.02 per faculty member (GPT-4o-mini)
- **ROI**: Higher success rates and quality justify minimal AI costs

This API reference provides comprehensive documentation for developers working with Lynnapse. For additional examples and use cases, see the main README.md and architecture documentation. 