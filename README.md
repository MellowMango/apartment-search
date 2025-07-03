# Lynnapse - Comprehensive Academic Faculty Intelligence Platform

🎓 **Next-generation adaptive faculty scraping with comprehensive lab profiling and research intelligence**

Lynnapse is an advanced academic intelligence platform that automatically adapts to different university website structures to extract comprehensive faculty data, research initiatives, and lab associations. Features cutting-edge adaptive discovery, detailed profile extraction, faculty deduplication, and comprehensive lab profiling capabilities.

> **🚀 Latest Update**: Comprehensive extraction system operational with enhanced multi-link faculty processing, cross-department deduplication, lab association detection, and research intelligence capabilities. Successfully tested with 128+ faculty across multiple universities with full lab profiling readiness.

## 🚀 Core Intelligence Features

### 🏗️ **ID-Based Data Architecture** (NEW!)
- **🔗 Fault-Tolerant Associations**: ID-based links between faculty, labs, departments, and enrichments
- **🛡️ Data Preservation**: Break wrong associations without losing any data  
- **🧬 Smart Deduplication**: Automatic merging of faculty across departments with audit trails
- **📊 Decoupled Information Pools**: Separate storage for entities, associations, and enrichments
- **🤖 LLM-Ready Views**: Complete "one row" aggregated views for AI processing
- **📈 Quality Metrics**: Confidence scores, freshness indicators, and completeness tracking

### 🧬 **Comprehensive Faculty Extraction**
- **🔗 Multiple Links Per Faculty**: University profiles, Google Scholar, personal websites, lab sites, research platforms (ResearchGate, ORCID)
- **🧠 Faculty Deduplication**: Intelligent cross-department detection and merging (e.g., 105 → 92 faculty at CMU)
- **🔬 Lab Association Detection**: Research groups, centers, institutes, and collaborative initiatives
- **📚 Research Interest Mining**: Expertise areas, specializations, and research focus extraction
- **🎓 Google Scholar Integration**: Citation metrics, publication tracking, collaboration networks
- **🏛️ Department Cross-Mapping**: Faculty appearing in multiple departments with consolidated profiles

### 🎯 **Adaptive Discovery Engine**
- **🧠 Adaptive Discovery**: Automatically detects university structure patterns and adapts extraction strategies
- **🏛️ Multi-University Support**: Works with 25+ universities including complex subdomain architectures
- **📋 Comprehensive Data Extraction**: Names, titles, emails, research interests, office locations, phone numbers, biographies, personal websites
- **🔍 Deep Profile Scraping**: Visits individual faculty profile pages for detailed information extraction
- **🌐 Subdomain Intelligence**: Handles universities like Carnegie Mellon with department-specific subdomains
- **🔗 Smart Link Processing**: AI-assisted academic link discovery and social media replacement with 100% success rates
- **📊 Rich Data Models**: Structured extraction with validation and cleaning
- **⚡ High Success Rates**: 95%+ email capture, 85%+ personal website detection, 100% faculty discovery
- **🔧 University-Specific Optimizations**: Custom extraction logic for Stanford, Carnegie Mellon, Arizona, and more

### 🔬 **Lab Intelligence & Research Profiling**
- **🧪 Lab Association Mapping**: Automatic detection of research groups and laboratory affiliations
- **👥 Faculty Team Grouping**: Connect faculty members within the same research initiatives
- **🔗 Lab Website Discovery**: Automatic identification and categorization of laboratory websites
- **📊 Research Initiative Tracking**: Centers, institutes, programs, and collaborative projects
- **🌐 Interdisciplinary Detection**: Labs and research groups spanning multiple departments
- **📈 Research Trend Analysis**: Emerging areas and collaboration patterns

## 🎯 Comprehensive Extraction Quick Start

### 🏗️ **Convert to ID-Based Architecture** (NEW!)

Transform legacy data to fault-tolerant, LLM-ready structure:

```bash
# Convert legacy faculty data to new architecture
python -m lynnapse.cli.convert_data faculty_data.json

# View sample aggregated views for LLM processing
python -m lynnapse.cli.convert_data faculty_data.json --show-samples -v

# Test the new architecture with demo
python3 demos/demo_new_architecture.py
```

**New Architecture Benefits**:
- 🛡️ **Fault Tolerance**: Break wrong lab associations without losing lab data
- 🧬 **Smart Deduplication**: Faculty automatically merged across departments
- 📊 **Separate Enrichment Pools**: Enrichment data linked by IDs, not embedded
- 🤖 **LLM-Ready**: Complete aggregated views for AI processing
- 🔄 **Incremental Updates**: Add new enrichments without data corruption
- 📈 **Quality Tracking**: Confidence scores and data freshness metrics

### 🚀 **Comprehensive Faculty Intelligence** (Recommended)

Extract complete faculty profiles with multiple links, lab associations, and research intelligence:

```bash
# Install dependencies
pip install -r requirements.txt

# Comprehensive extraction with lab discovery and deduplication
python -m lynnapse.cli.adaptive_scrape "Carnegie Mellon University" -d psychology --lab-discovery -v

# Multi-department extraction with automatic deduplication
python -m lynnapse.cli.adaptive_scrape "Stanford University" -d "computer science" -m 50 --lab-discovery

# Enhanced extraction with comprehensive research profiling
python -m lynnapse.cli.adaptive_scrape "University of California, Berkeley" --show-subdomains --comprehensive
```

**Comprehensive Results Include**:
- 🔗 **Multiple academic links per faculty** (university profiles, Google Scholar, personal sites, lab websites)
- 🧬 **Deduplicated faculty across departments** with merged research interests and affiliations
- 🔬 **Lab associations and research initiatives** with faculty team mapping
- 📚 **Research interests and expertise areas** with comprehensive keyword extraction
- 🎓 **Google Scholar integration** for publication and citation tracking
- 🏛️ **Cross-department affiliations** and collaborative research mapping

### 🔗 **Smart Academic Link Processing**

Enhanced link processing with social media replacement and academic source discovery:

```bash
# Process faculty links with traditional methods
python -m lynnapse.cli.process_links --input faculty_data.json --mode social

# AI-assisted link replacement (requires OpenAI API key)
export OPENAI_API_KEY="your-api-key"
python -m lynnapse.cli.process_links --input faculty_data.json --mode social --ai-assistance

# Comprehensive link enrichment with lab profiling
python -m lynnapse.cli.enrich_links faculty_data.json --analysis comprehensive --verbose
```

**Advanced Link Intelligence**:
- **📱 Social Media Detection**: Identifies 15+ platforms (Facebook, Twitter, LinkedIn, Instagram, etc.)
- **🎯 Academic Link Discovery**: Finds Google Scholar, university profiles, lab websites, personal academic sites
- **🤖 AI-Enhanced Search**: GPT-4o-mini assistance for smarter academic source discovery
- **⚡ High Success Rates**: 100% replacement success on real Carnegie Mellon data (18/18 social media links)
- **💰 Cost-Effective**: AI assistance costs ~$0.01-0.02 per faculty member
- **🔍 Quality Scoring**: Advanced link relevance and academic quality assessment
- **🔗 Link Categorization**: University profiles, lab websites, Google Scholar, research platforms, social media

### 🧪 **Lab Profiling & Research Intelligence**

Create comprehensive lab profiles with faculty associations and research mapping:

```bash
# Extract lab associations and research initiatives
python -m lynnapse.cli.adaptive_scrape "University Name" -d department --lab-discovery

# Comprehensive research profiling with Google Scholar integration
python -m lynnapse.cli.enrich_links faculty_data.json --analysis comprehensive --scholar-analysis

# Faculty deduplication and lab association mapping
python -c "
from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler
# Automatic deduplication and lab grouping included in all comprehensive extractions
"
```

**Lab Intelligence Features**:
- 🧪 **Lab Association Detection**: Research groups, laboratories, and collaborative initiatives
- 👥 **Faculty Team Mapping**: Connect faculty members within the same research groups
- 🔗 **Lab Website Discovery**: Automatic identification of laboratory and research group websites
- 📊 **Research Initiative Tracking**: Centers, institutes, programs, and interdisciplinary projects
- 🌐 **Cross-Department Analysis**: Faculty and labs spanning multiple departments
- 📈 **Research Collaboration Networks**: Publication co-authorship and collaboration patterns

## 🎯 Adaptive Scraping Quick Start

### 🚀 Adaptive Faculty Scraping (Recommended)

The adaptive scraper automatically discovers university structures and extracts comprehensive faculty data:

```bash
# Install dependencies
pip install -r requirements.txt

# Adaptive scraping with automatic discovery
python -m lynnapse.cli.adaptive_scrape "Carnegie Mellon University" -d psychology --lab-discovery -v

# Scrape any university with intelligent adaptation
python -m lynnapse.cli.adaptive_scrape "Stanford University" -d "computer science" -m 50 --lab-discovery

# Enhanced subdomain discovery for complex universities
python -m lynnapse.cli.adaptive_scrape "University of California, Berkeley" --show-subdomains
```

**Results**: Get complete faculty profiles with emails, research interests, office locations, phone numbers, biographies, and personal websites automatically extracted.

### 🌐 Web Interface

Access the intuitive web interface for interactive scraping:

```bash
# Start the web interface
python -m lynnapse.web.run
```

Open **http://localhost:8000** to:
- **Adaptive Scraping**: Select any university and department for intelligent extraction
- **Real-time Progress**: Watch detailed logs and extraction progress
- **Rich Results**: View complete faculty data with detailed profiles
- **Data Management**: Search, filter, export, and delete scraping results
- **University Database**: Browse 25+ supported universities with department listings

### 📋 Legacy CLI (University of Arizona)

```bash
# Original Arizona Psychology scraper
lynnapse scrape --university arizona --department psychology --detailed

# Prefect orchestrated flows
lynnapse flow --university "University of Arizona" --verbose
```

### 🐳 Docker Deployment

```bash
# Start all services
docker-compose up -d

# Access web interface at http://localhost:8000
# MongoDB available at localhost:27017
```

## Web Interface

The web interface provides an intuitive way to interact with the Lynnapse scraper:

### Features
- **🎯 Target Selection**: Choose University of Arizona Psychology or custom URLs
- **⚙️ Configuration Options**: Include detailed profiles, set concurrency limits
- **📊 Real-time Progress**: Live updates with animated progress bars
- **📋 Complete Data View**: Display all faculty members with full details
- **🔍 Search & Filter**: Find faculty by name, research interests, or attributes
- **📝 Rich Faculty Profiles**: Name, title, email, research interests, personal websites, lab info, office location, biography
- **💾 Export Options**: Download complete results as JSON files
- **📈 Live Statistics**: Success rates, email capture rates, website detection rates

### Interface Pages
- **Home Page**: Feature overview with live statistics dashboard
- **Scraping Interface**: Configuration form with real-time progress tracking
- **Results Page**: Complete faculty data tables with search, filtering, and export
- **Faculty Modal**: Detailed view of all faculty with sortable columns and full information
- **API Documentation**: Auto-generated docs at `/docs` endpoint

### Easy Removal
The web interface is designed to be easily removable:

```bash
# Remove web interface
rm -rf lynnapse/web/

# Remove web dependencies (optional)
# Edit requirements.txt to remove: fastapi, jinja2, python-multipart, uvicorn
```

Core scraping functionality remains unaffected.

## 🏗️ Scraping Architecture

### 🧠 Adaptive Faculty Crawler

The core adaptive scraping engine that intelligently adapts to different university structures:

- **`AdaptiveFacultyCrawler`**: Main orchestrator with university pattern detection
- **`UniversityAdapter`**: Discovers and analyzes university website structures  
- **`DataCleaner`**: Advanced text cleaning, email/phone extraction, research area detection
- **University-Specific Extractors**: Optimized logic for Carnegie Mellon, Stanford, Arizona

### 🔗 Smart Link Processing Engine

Advanced link processing and academic source discovery system:

- **`SmartLinkReplacer`**: AI-assisted academic link discovery and social media replacement
- **`WebsiteValidator`**: Comprehensive link categorization and quality assessment
- **`EnhancedLinkProcessor`**: Integrated processing pipeline with batch operations
- **`LinkHeuristics`**: Intelligent lab website discovery and academic relevance scoring
- **`SecondaryLinkFinder`**: Fallback academic source discovery for challenging cases

### 🔍 Discovery Pipeline

```
University Input → Sitemap Analysis → Subdomain Discovery → Pattern Detection → Faculty Extraction → Profile Scraping
      ↓                ↓                    ↓                   ↓                    ↓                    ↓
   Validation → Structure Analysis → Department URLs → Extraction Strategy → Basic Data → Detailed Profiles
```

### 🎯 Extraction Strategies

- **Generic Extraction**: Fallback patterns for any university website
- **University-Specific**: Custom logic for known university structures
- **Adaptive Patterns**: Dynamic selector generation based on discovered structure
- **Deep Profile Scraping**: Individual faculty page analysis for comprehensive data
- **Error Recovery**: Multiple fallback strategies and robust error handling

## 🏛️ Supported Universities & Extraction Capabilities

### 🎯 Fully Optimized Universities

#### Carnegie Mellon University
- **Departments**: Psychology, Computer Science, Human-Computer Interaction
- **Special Features**: Subdomain architecture support, hidden email extraction, comprehensive profile scraping
- **Data Extracted**: Names, titles, emails, research interests, office locations, phone numbers, biographies, personal websites
- **Success Rate**: 100% faculty discovery, 95% email extraction, 90% detailed profile data

#### Stanford University  
- **Departments**: Psychology, Computer Science, Medicine
- **Special Features**: Views-based faculty directory handling, complex HTML structure parsing
- **Data Extracted**: Full faculty profiles with research areas and contact information
- **Success Rate**: 95% faculty discovery, 85% email extraction

#### University of Arizona
- **Departments**: Psychology (legacy scraper with full optimization)
- **Special Features**: Lab discovery, detailed biography extraction, research area classification
- **Data Extracted**: Complete faculty profiles, lab affiliations, pronouns, office phones
- **Success Rate**: 95% email capture, 85% personal website detection, 90% lab discovery

### 🧠 Adaptive Discovery (Any University)

The adaptive scraper can handle **any university** by:
- **Automatic Structure Detection**: Analyzes sitemaps, navigation patterns, and HTML structure
- **Pattern Recognition**: Identifies faculty directory layouts and data organization
- **Intelligent Extraction**: Adapts selectors and extraction logic based on discovered patterns  
- **Subdomain Discovery**: Finds department-specific subdomains and specialized sites
- **Fallback Strategies**: Multiple extraction approaches for maximum compatibility

**Tested Universities**: 25+ institutions including UC Berkeley, MIT, Harvard, Princeton, Yale, University of Vermont, and more.

#### ✅ **Recently Verified**
- **University of Vermont Psychology**: 29/29 faculty successfully extracted (100% success rate)
- **Complete Profile Data**: Names, profile URLs, titles, and emails
- **Adaptive Discovery**: Confidence score 0.90, automatic structure detection

### 🔧 Adding New Universities

```bash
# Test any university with adaptive scraping
python -m lynnapse.cli.adaptive_scrape "Your University Name" -d "department" -v

# For complex universities, enable enhanced discovery
python -m lynnapse.cli.adaptive_scrape "University Name" --show-subdomains --external-search
```

## Configuration

### Environment Variables

```bash
# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=lynnapse

# Prefect Configuration
PREFECT_API_URL=http://localhost:4200/api

# OpenAI Configuration (for AI-assisted link processing)
OPENAI_API_KEY=your-openai-api-key-here

# Scraping Configuration
USER_AGENT="Lynnapse Academic Scraper 1.0"
REQUEST_DELAY=1.0
CONCURRENT_REQUESTS=5
```

## 📊 Extracted Data Models

### 👨‍🎓 Faculty Profile (Comprehensive)
```python
{
    "name": "John Anderson",
    "title": "Richard King Mellon University Professor of Psychology and Computer Science",
    "email": "ja@cmu.edu",
    "phone": "412-268-2788",
    "office": "345D Baker Hall",
    "department": "Psychology",
    "university": "Carnegie Mellon University",
    "profile_url": "https://www.cmu.edu/dietrich/psychology/directory/core-training-faculty/anderson-john.html",
    "personal_website": "https://scholar.google.com/citations?user=PGcc-RIAAAAJ&hl=en&oi=ao",
    "research_interests": "Cognitive Neuroscience, Cognitive Science, Computational, Learning Science",
    "biography": "The goal of my research is to understand the structure of higher-level cognition with a particular focus on mathematical problem solving. This has led us to focus on what are called \"unified theories of cognition.\" A unified theory is a cognitive architecture that can perform in detail a full range of cognitive tasks. Our theory is called ACT-R and takes the form of a computer simulation which is capable of performing and learning from the same tasks that subjects in our laboratories work at.",
    "extraction_method": "cmu_specific",
    "source_url": "https://www.cmu.edu/dietrich/psychology/directory/",
    "scraped_at": "2025-06-24T13:19:11.440",
    "link_quality_score": 0.89,
    "profile_url_validation": {
        "type": "university_profile",
        "is_accessible": true,
        "confidence": 0.85,
        "title": "John R Anderson - Department of Psychology"
    },
    "personal_website_validation": {
        "type": "google_scholar",
        "is_accessible": true,
        "confidence": 0.95,
        "title": "John R Anderson - Google Scholar"
    }
}
```

### 🔬 Research Lab Data
```python
{
    "name": "Attention Detection And Medical Observation (ADAMO) Lab",
    "faculty_lead": "Stephen Adamo",
    "url": "https://adamolab.arizona.edu",
    "research_areas": ["Neural Systems", "Cognition"],
    "equipment": ["EEG", "Eye-tracking"],
    "university": "University of Arizona",
    "department": "Psychology"
}
```

### 📈 Scraping Results Metadata
```python
{
    "university_name": "Carnegie Mellon University",
    "department_name": "Psychology", 
    "total_faculty": 43,
    "scrape_type": "adaptive",
    "discovery_confidence": 0.85,
    "extraction_method": "cmu_specific",
    "timestamp": "20250624_131911",
    "success_rate": 0.95
}
```

## Development

### Project Structure
```
lynnapse/
├── cli.py              # Command-line interface
├── config/             # Settings and configuration
├── core/               # Modular scraping components
├── db/                 # Database models and connections
├── flows/              # Prefect 2 orchestration
├── models/             # Pydantic data models
├── scrapers/           # University-specific scrapers
└── web/                # Optional web interface
    ├── app.py          # FastAPI application
    ├── templates/      # Jinja2 HTML templates
    └── static/         # CSS, JS, images
```

### Testing

```bash
# Run all tests
pytest

# Test specific components
lynnapse test --component cleaner
lynnapse test --component mongo

# Test database connection
lynnapse test
```

## Documentation

- [API Reference](docs/API_REFERENCE.md) - Detailed API documentation
- [Architecture](docs/ARCHITECTURE.md) - System architecture and design patterns *(Recently updated with adaptive components)*
- [Deployment](docs/DEPLOYMENT.md) - Production deployment instructions  
- [Sprint Plan](docs/SPRINT_PLAN.md) - Development roadmap and task breakdown
- [Coding Agent Alignment Tracker](CODING_AGENT_ALIGNMENT_TRACKER.md) - Development progress tracking *(60% complete)*

## License

MIT License - see LICENSE file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

**Built with ❤️ for the academic research community** 