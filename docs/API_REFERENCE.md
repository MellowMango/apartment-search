# 📚 Lynnapse Comprehensive Academic Intelligence API Reference

## 🚀 Comprehensive CLI Commands

### ID-Based Data Architecture (NEW!)

#### `convert-data`
Convert legacy monolithic data to fault-tolerant ID-based architecture.

```bash
python -m lynnapse.cli.convert_data INPUT_FILE [OPTIONS]
```

**Arguments:**
- `INPUT_FILE`: Legacy faculty data JSON file to convert

**Options:**
- `-o, --output-dir`: Output directory for converted data [default: converted_data]
- `--show-samples`: Display sample aggregated views for LLM processing
- `-v, --verbose`: Show detailed progress and error information

**Key Features:**
- **🧬 Smart Deduplication**: Automatically merges faculty across departments
- **🔗 ID-Based Associations**: Creates fault-tolerant links between entities
- **📊 Separate Data Pools**: Entities, associations, and enrichments stored separately
- **🤖 LLM-Ready Output**: Complete aggregated views for AI processing
- **🛡️ Fault Tolerance**: Can break wrong associations without losing data

**Examples:**
```bash
# Basic conversion
python -m lynnapse.cli.convert_data faculty_data.json

# Show sample LLM views and detailed output
python -m lynnapse.cli.convert_data faculty_data.json --show-samples -v

# Custom output directory
python -m lynnapse.cli.convert_data faculty_data.json -o my_converted_data
```

**Output Structure:**
```json
{
  "faculty_aggregated_views": [
    {
      "faculty": {"id": "fac_123", "name": "Dr. Jane Smith"},
      "university": {"name": "Carnegie Mellon University"},
      "department_associations": [
        {
          "association": {"appointment_type": "primary"},
          "department": {"name": "Psychology"}
        }
      ],
      "lab_associations": [
        {
          "association": {"role": "Principal Investigator", "confidence_score": 0.95},
          "lab": {"name": "Cognitive Science Laboratory"}
        }
      ],
      "enrichments": {
        "google_scholar": [{"total_citations": 1247, "h_index": 23}],
        "profile": [{"full_biography": "Dr. Smith studies..."}]
      },
      "computed_metrics": {"completeness_score": 0.87, "confidence_score": 0.95}
    }
  ]
}
```

### Adaptive Faculty Intelligence

#### `adaptive-scrape`
Comprehensive adaptive faculty scraping with multi-link extraction, deduplication, and lab profiling.

```bash
python -m lynnapse.cli.adaptive_scrape UNIVERSITY [OPTIONS]
```

**Arguments:**
- `UNIVERSITY`: University name (e.g., 'Carnegie Mellon University', 'Stanford University')

**Options:**
- `-d, --department`: Target department (e.g., 'psychology', 'computer science')
- `-m, --max-faculty`: Maximum faculty to process [default: unlimited]
- `-o, --output`: Custom output file path (automatic saving to scrape_results/adaptive always enabled)
- `--lab-discovery / --no-lab-discovery`: Enable/disable lab discovery [default: enabled]
- `--external-search / --no-external-search`: Enable external search APIs [default: disabled]
- `--show-subdomains`: Display detailed subdomain discovery information [default: false]
- `-v, --verbose`: Enable detailed progress logging [default: false]

**Comprehensive Features:**
- **🔗 Multi-Link Extraction**: University profiles, Google Scholar, personal websites, lab sites, research platforms
- **🧬 Faculty Deduplication**: Cross-department detection and intelligent merging
- **🔬 Lab Association Detection**: Research groups, centers, institutes, collaborative initiatives
- **📚 Research Interest Mining**: Expertise extraction and classification
- **🎓 Google Scholar Integration**: Citation metrics and collaboration networks
- **🤖 AI-Powered Discovery**: OpenAI fallback for obscure universities

**Examples:**
```bash
# Comprehensive extraction with lab discovery
python -m lynnapse.cli.adaptive_scrape "Carnegie Mellon University" -d psychology --lab-discovery -v

# Multi-department extraction with deduplication
python -m lynnapse.cli.adaptive_scrape "Stanford University" -d "computer science" -m 50 --comprehensive

# Enhanced subdomain discovery
python -m lynnapse.cli.adaptive_scrape "University of California, Berkeley" --show-subdomains

# Comprehensive research profiling
python -m lynnapse.cli.adaptive_scrape "University of Vermont" -d psychology --lab-discovery --comprehensive
```

**Output Example:**
```json
{
  "university": "Carnegie Mellon University",
  "department": "Psychology",
  "faculty_count": 92,
  "original_faculty_count": 105,
  "duplicates_merged": 13,
  "comprehensive_extraction": true,
  "lab_associations_detected": 8,
  "total_academic_links": 31,
  "faculty": [
    {
      "name": "Dr. Jane Smith",
      "title": "Professor of Cognitive Psychology",
      "email": "jsmith@cmu.edu",
      "departments": ["Psychology", "Human-Computer Interaction"],
      "links": [
        {
          "url": "https://scholar.google.com/citations?user=abc123",
          "category": "google_scholar",
          "text": "Google Scholar Profile",
          "context": "Publications and citations"
        },
        {
          "url": "https://janesmith.cmu.edu",
          "category": "personal_website", 
          "text": "Personal Academic Website",
          "context": "Research homepage"
        }
      ],
      "external_profiles": {
        "google_scholar": ["https://scholar.google.com/citations?user=abc123"],
        "personal_websites": ["https://janesmith.cmu.edu"],
        "university_profiles": ["https://www.cmu.edu/dietrich/psychology/people/core-training-faculty/smith-jane.html"]
      },
      "research_interests": ["Cognitive Psychology", "Memory", "Attention", "Decision Making"],
      "lab_associations": ["Cognitive Science Lab", "Memory and Cognition Research Group"],
      "comprehensive_extraction": true,
      "dedup_key": "carnegie_mellon_university::jane::smith"
    }
  ],
  "lab_associations": {
    "Cognitive Science Lab": {
      "faculty_count": 12,
      "faculty_members": ["Dr. Jane Smith", "Dr. John Doe"],
      "research_areas": ["Cognitive Psychology", "Memory", "Perception"],
      "interdisciplinary": true,
      "departments": ["Psychology", "Computer Science"]
    }
  }
}
```

### Smart Link Processing & Academic Discovery

#### `process-links`
Enhanced link processing with social media replacement and academic source discovery.

```bash
python -m lynnapse.cli.process_links [OPTIONS]
```

**Options:**
- `--input`: Input JSON file with faculty data [required]
- `--mode`: Processing mode (social, academic, full) [default: social]
- `--ai-assistance`: Enable AI-assisted link discovery [default: false]
- `--max-concurrent`: Maximum concurrent operations [default: 5]
- `--timeout`: Network timeout in seconds [default: 30]
- `-v, --verbose`: Enable detailed progress logging [default: false]

**Processing Modes:**
- **social**: Replace social media links with academic alternatives
- **academic**: Discover and categorize academic links
- **full**: Complete processing pipeline with replacement and enrichment

**Examples:**
```bash
# Basic social media replacement
python -m lynnapse.cli.process_links --input faculty_data.json --mode social

# AI-assisted academic discovery (requires OpenAI API key)
export OPENAI_API_KEY="your-api-key"
python -m lynnapse.cli.process_links --input faculty_data.json --mode social --ai-assistance

# Full processing pipeline
python -m lynnapse.cli.process_links --input faculty_data.json --mode full --ai-assistance
```

#### `enrich-links`
Comprehensive academic link enrichment with metadata extraction and analysis.

```bash
python -m lynnapse.cli.enrich_links INPUT_FILE [OPTIONS]
```

**Arguments:**
- `INPUT_FILE`: JSON file containing faculty data with links

**Options:**
- `--output`: Output file for enriched data [default: auto-generated]
- `--analysis`: Analysis type (enrichment, analysis, comprehensive) [default: enrichment]
- `--max-concurrent`: Maximum concurrent operations [default: 5]
- `--timeout`: Network timeout in seconds [default: 45]
- `--scholar-analysis`: Enable Google Scholar profile analysis [default: false]
- `-v, --verbose`: Enable detailed progress display [default: false]

**Analysis Types:**
- **enrichment**: Basic metadata extraction from links
- **analysis**: Advanced link analysis with quality scoring
- **comprehensive**: Full enrichment + analysis + Scholar profiling

**Examples:**
```bash
# Basic link enrichment
python -m lynnapse.cli.enrich_links faculty_data.json

# Comprehensive analysis with Google Scholar
python -m lynnapse.cli.enrich_links faculty_data.json --analysis comprehensive --scholar-analysis

# Custom output with detailed logging
python -m lynnapse.cli.enrich_links faculty_data.json --output enriched_results.json --verbose
```

**Enrichment Output Example:**
```json
{
  "faculty_name": "Dr. Jane Smith",
  "link_enrichment": {
    "google_scholar": {
      "url": "https://scholar.google.com/citations?user=abc123",
      "metadata": {
        "title": "Jane Smith - Google Scholar",
        "citation_count": 1247,
        "h_index": 23,
        "research_interests": ["Cognitive Psychology", "Memory"],
        "affiliation": "Carnegie Mellon University",
        "recent_publications": ["Title 1", "Title 2"]
      },
      "analysis": {
        "impact_level": "high",
        "productivity": "active",
        "collaboration_score": 0.85
      }
    },
    "lab_website": {
      "url": "https://coglab.cmu.edu",
      "metadata": {
        "title": "Cognitive Science Laboratory",
        "team_size": 12,
        "research_areas": ["Memory", "Attention", "Decision Making"],
        "equipment": ["fMRI", "EEG", "Eye Tracking"],
        "recent_projects": ["Project A", "Project B"]
      },
      "analysis": {
        "lab_scale": "large",
        "research_diversity": "high",
        "resource_level": "well-equipped"
      }
    }
  }
}
```

### Legacy & Specialized Commands

#### `scrape-university`
Legacy university scraper for specific institutions.

```bash
lynnapse scrape-university UNIVERSITY [OPTIONS]
```

**Arguments:**
- `UNIVERSITY`: University identifier (e.g., 'arizona-psychology')

**Options:**
- `--format, -f`: Output format (json, mongodb) [default: json]
- `--output, -o`: Output file path [optional]
- `--profiles`: Include detailed faculty profiles [default: false]
- `--verbose, -v`: Enable verbose logging [default: false]

#### `validate-websites`
Validate and categorize faculty websites and links.

```bash
python -m lynnapse.cli.validate_websites INPUT_FILE [OPTIONS]
```

**Options:**
- `--output`: Output file for validation results
- `--max-concurrent`: Maximum concurrent validations [default: 10]
- `--timeout`: Request timeout in seconds [default: 30]
- `-v, --verbose`: Detailed validation logging

#### `university-database`
Manage and query the university database.

```bash
python -m lynnapse.cli.university_database [OPTIONS]
```

**Options:**
- `--list`: List all universities in database
- `--search TERM`: Search universities by name
- `--departments UNIVERSITY`: Show departments for university
- `--add-university`: Add new university to database
- `--update`: Update university information

**Examples:**
```bash
# List all universities
python -m lynnapse.cli.university_database --list

# Search for universities
python -m lynnapse.cli.university_database --search "carnegie"

# Show departments
python -m lynnapse.cli.university_database --departments "Carnegie Mellon University"
```

## 🌐 Web Interface API

### Enhanced API Endpoints

#### GET `/`
Web interface home page with comprehensive features overview and live statistics dashboard.

#### GET `/scrape`
Enhanced scraping interface with adaptive scraping configuration.

#### GET `/results`
Results page with comprehensive faculty data display, advanced search, and filtering.

#### GET `/api/comprehensive-stats`
Get comprehensive statistics about the academic intelligence system.

**Response:**
```json
{
  "total_faculty_processed": 1247,
  "universities_supported": 25,
  "comprehensive_extractions": 1089,
  "faculty_deduplicated": 47,
  "lab_associations_detected": 156,
  "academic_links_discovered": 2891,
  "success_rates": {
    "faculty_discovery": 98.7,
    "email_capture": 94.2,
    "multi_link_extraction": 87.3,
    "lab_association_detection": 76.8
  }
}
```

#### POST `/api/adaptive-scrape`
Start comprehensive adaptive faculty scraping with enhanced features.

**Request Body:**
```json
{
  "university": "Carnegie Mellon University",
  "department": "psychology",
  "max_faculty": 100,
  "lab_discovery": true,
  "comprehensive_extraction": true,
  "ai_assistance": false
}
```

**Response:**
```json
{
  "message": "Comprehensive faculty extraction completed successfully!",
  "university": "Carnegie Mellon University",
  "department": "Psychology", 
  "faculty_count": 92,
  "original_count": 105,
  "duplicates_merged": 13,
  "lab_associations": 8,
  "academic_links": 31,
  "comprehensive_extraction": true,
  "filename": "cmu_psychology_comprehensive_20250627.json"
}
```

#### GET `/api/comprehensive-results/{filename}`
Get complete comprehensive faculty data with all extracted intelligence.

**Response includes:**
- Multi-link faculty profiles with categorized academic links
- Cross-department affiliations and merged data
- Lab associations and research group mappings
- Research interests and expertise classifications
- Google Scholar integration data
- Link enrichment metadata and analysis

## Individual Faculty Data Access

### Get Faculty by ID with Full Enrichments

**Endpoint:** `GET /api/faculty/{faculty_id}`

**Description:** Retrieve a complete faculty profile with all associated enrichment data.

**Parameters:**
- `faculty_id` (string): Unique faculty identifier
- `include_html` (boolean, optional): Include full HTML content (default: false)
- `include_raw` (boolean, optional): Include raw scraped data (default: false)

**Response:**
```json
{
  "success": true,
  "faculty": {
    "id": "fac_cmu_psych_john_anderson",
    "name": "John Anderson",
    "title": "Richard King Mellon University Professor",
    "university": {
      "name": "Carnegie Mellon University",
      "domain": "cmu.edu"
    },
    "primary_department": {
      "name": "Psychology",
      "full_name": "Department of Psychology"
    },
    "enrichments": {
      "profile_url_enrichment": {
        "full_html_content": "<!DOCTYPE html>...",
        "text_content": "John Anderson is a professor...",
        "html_content_length": 87580,
        "academic_links": [
          "https://johnanderson.cmu.edu/research",
          "https://cogarch.lab.cmu.edu"
        ],
        "contact_information": {
          "emails": ["ja@cmu.edu"],
          "phones": ["+1-412-268-2788"]
        }
      },
      "google_scholar": {
        "total_citations": 15420,
        "h_index": 65,
        "scholar_interests": ["Cognitive Architecture", "ACT-R"]
      }
    },
    "lab_associations": [
      {
        "role": "Principal Investigator",
        "lab": {
          "name": "Cognitive Architecture Lab",
          "website_url": "https://cogarch.lab.cmu.edu"
        }
      }
    ]
  }
}
```

### Search Faculty

**Endpoint:** `GET /api/faculty/search`

**Parameters:**
- `q` (string): Search query (name, research interests, etc.)
- `university` (string, optional): Filter by university
- `department` (string, optional): Filter by department
- `limit` (integer, optional): Number of results (default: 10, max: 100)

**Response:**
```json
{
  "success": true,
  "total": 156,
  "faculty": [
    {
      "id": "fac_cmu_psych_john_anderson",
      "name": "John Anderson",
      "title": "Richard King Mellon University Professor",
      "university": "Carnegie Mellon University",
      "department": "Psychology",
      "research_interests": ["Cognitive Architecture", "ACT-R"],
      "citation_count": 15420
    }
  ]
}
```

### Get Faculty Lab Websites

**Endpoint:** `GET /api/faculty/{faculty_id}/labs`

**Description:** Get all lab websites and enrichment data for a specific faculty member.

**Response:**
```json
{
  "success": true,
  "labs": [
    {
      "lab_name": "Cognitive Architecture Lab",
      "lab_url": "https://cogarch.lab.cmu.edu",
      "role": "Principal Investigator",
      "enrichments": {
        "full_html_content": "<!DOCTYPE html>...",
        "lab_members": ["John Anderson", "Jane Doe", "Mike Smith"],
        "research_projects": ["ACT-R 8.0", "Cognitive Tutors"],
        "equipment": ["Eye-tracking system", "EEG equipment"]
      }
    }
  ]
}
```

## 🎯 Data Models

### Enhanced Faculty Model

```python
{
  "name": "Dr. Jane Smith",
  "title": "Professor of Cognitive Psychology",
  "email": "jsmith@cmu.edu",
  
  # Multi-Link Academic Presence
  "links": [
    {
      "url": "https://scholar.google.com/citations?user=abc123",
      "text": "Google Scholar Profile",
      "category": "google_scholar",
      "context": "Research publications and citations"
    }
  ],
  "external_profiles": {
    "google_scholar": ["https://scholar.google.com/..."],
    "personal_websites": ["https://janesmith.cmu.edu"],
    "lab_websites": ["https://coglab.cmu.edu"],
    "research_platforms": ["https://www.researchgate.net/..."],
    "university_profiles": ["https://www.cmu.edu/..."]
  },
  
  # Research Intelligence
  "research_interests": ["Cognitive Psychology", "Memory", "Attention"],
  "research_areas": ["Memory Studies", "Cognitive Neuroscience"],
  "lab_associations": ["Cognitive Science Lab", "Memory Research Group"],
  "research_initiatives": ["Center for Neural Basis of Cognition"],
  
  # Cross-Department Support
  "departments": ["Psychology", "Human-Computer Interaction"],
  
  # Enhanced Metadata
  "comprehensive_extraction": true,
  "extraction_method": "adaptive_comprehensive",
  "dedup_key": "carnegie_mellon_university::jane::smith",
  "scraped_at": "2025-06-27T10:30:00Z",
  "university": "Carnegie Mellon University",
  "department": "Psychology"
}
```

### Lab Association Model

```python
{
  "lab_name": "Cognitive Science Laboratory",
  "university": "Carnegie Mellon University",
  "faculty_count": 12,
  "faculty_members": [
    {
      "name": "Dr. Jane Smith",
      "department": "Psychology",
      "departments": ["Psychology", "Human-Computer Interaction"]
    }
  ],
  "research_areas": ["Memory", "Attention", "Decision Making"],
  "lab_websites": ["https://coglab.cmu.edu"],
  "interdisciplinary": true,
  "departments_involved": ["Psychology", "Computer Science", "Neuroscience"]
}
```

## 🏗️ Microservice Architecture

Lynnapse is architected as a clean microservice with optional frontend:

### 📦 Backend Microservice

**Core Components:**
- CLI interface for all scraping operations
- Core scraping engines and adaptive crawlers  
- Data processing and enrichment pipelines
- MongoDB integration and data management
- Independent deployment via `docker-compose.backend.yml`

**Key Features:**
- ✅ No web dependencies required
- ✅ Lightweight Docker image (~500MB)
- ✅ Scales independently
- ✅ Production-ready with health checks
- ✅ Complete CLI functionality

**Dependencies:** Only `backend-requirements.txt` (35 packages)

### 🌐 Frontend Web Interface (Optional)

**Purpose:** 
- Interactive web UI for non-technical users
- Real-time progress monitoring
- Result visualization and export
- Development and demonstration tool

**Architecture:**
- FastAPI-based REST API client
- Communicates with backend via HTTP calls
- Separate Docker container
- Can be completely removed without affecting backend

**Dependencies:** Only `frontend-requirements.txt` (15 packages)

### 🚀 Deployment Strategies

1. **Production Microservice**: Backend only with CLI interface
2. **Development Full Stack**: Backend + Frontend for interactive use
3. **Hybrid**: Backend microservice + custom frontend via API

## 🔧 Configuration & Environment

### Environment Variables

```bash
# OpenAI API Integration (for AI-assisted features)
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Configuration (optional)
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=lynnapse_academic_intelligence

# Web Interface Settings
WEB_HOST=0.0.0.0
WEB_PORT=8000

# Scraping Configuration
DEFAULT_TIMEOUT=30
MAX_CONCURRENT_REQUESTS=10
RESPECT_ROBOTS_TXT=true

# AI Processing Settings
AI_MODEL=gpt-4o-mini
AI_MAX_TOKENS=150
AI_TEMPERATURE=0.1
```

### Configuration Files

#### `env.template`
Template for environment variables with comprehensive settings.

#### `requirements.txt`
All dependencies for comprehensive academic intelligence features.

## 🚀 Production Deployment

### Backend Microservice Deployment (Recommended)

```bash
# Deploy backend microservice only (production ready)
docker-compose -f docker-compose.backend.yml up -d

# Services include:
# - Lynnapse Backend Microservice (CLI + Core functionality)
# - MongoDB Database (port 27017)
# - No web dependencies
# - Independent and scalable

# Execute scraping operations
docker exec -it lynnapse-backend python -m lynnapse.cli.adaptive_scrape "University Name" -d department
```

### Full Stack Deployment (Development)

```bash
# Start all services including web interface
docker-compose up -d

# Services include:
# - Lynnapse Backend Microservice
# - Lynnapse Frontend Web Interface (port 8000)
# - MongoDB Database (port 27017)
# - Full web UI functionality
```

### Dependency-Only Installation

```bash
# Backend core functionality only
pip install -r backend-requirements.txt

# Frontend web interface only
pip install -r frontend-requirements.txt

# All dependencies (legacy)
pip install -r requirements.txt
```

### Health Checks

#### GET `/health`
System health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "components": {
    "database": "connected",
    "ai_service": "available",
    "web_interface": "running",
    "adaptive_crawler": "ready"
  },
  "version": "2.0.0",
  "features": [
    "comprehensive_extraction",
    "faculty_deduplication", 
    "lab_association_detection",
    "ai_powered_discovery"
  ]
}
```

## 📊 Performance Metrics

### System Capabilities

- **Faculty Processing**: 100+ faculty per university
- **Deduplication Rate**: ~10-15% duplicates detected and merged
- **Link Extraction**: 5-10 academic links per faculty on average
- **Lab Association Detection**: 70-80% of research groups identified
- **AI Discovery Cost**: ~$0.001-0.002 per university URL discovery
- **Processing Speed**: ~2-3 faculty per second with comprehensive extraction

### Success Rates

- **Faculty Discovery**: 95-100% across tested universities
- **Email Extraction**: 90-95% with enhanced parsing
- **Multi-Link Extraction**: 85-90% comprehensive link coverage
- **Research Interest Mining**: 80-90% expertise extraction
- **Lab Association Detection**: 75-85% research group identification
- **Cross-Department Merging**: 100% accuracy for name-based deduplication