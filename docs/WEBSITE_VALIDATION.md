# Website Validation System

The Lynnapse Website Validation System is a comprehensive tool for checking, categorizing, and validating faculty website links to ensure data quality and proper link classification.

## Overview

The system addresses common issues with faculty link extraction:
- **Incorrect Links**: Social media links instead of personal websites
- **Broken Links**: Dead or inaccessible URLs  
- **Mixed Categories**: Academic profiles mixed with personal sites
- **Low Quality**: Random links that aren't faculty-related

## Features

### 🔍 Link Categorization
Automatically categorizes links into specific types:

| Category | Description | Examples |
|----------|-------------|----------|
| **Google Scholar** | Google Scholar profiles | `scholar.google.com/citations?user=...` |
| **University Profile** | Official faculty pages | `university.edu/faculty/name.html` |
| **Personal Website** | Personal academic sites | Academic personal domains |
| **Academic Profile** | Research platforms | ResearchGate, Academia.edu, ORCID |
| **Lab Website** | Research lab sites | Lab/group websites |
| **Social Media** | Social platforms | Facebook, Twitter, LinkedIn |
| **Publication** | Journal articles | DOI links, PubMed, arXiv |
| **Unknown** | Unclassified links | Links that don't fit categories |
| **Invalid** | Broken/invalid URLs | Non-functional links |

### ✅ Link Validation
- **Accessibility Check**: Tests if links are reachable
- **Content Analysis**: Extracts page titles and metadata
- **Redirect Handling**: Follows redirects and updates URLs
- **Confidence Scoring**: Provides confidence levels (0-1) for categorization

### 📊 Quality Assessment
- **Link Quality Score**: Overall quality metric per faculty member
- **Validation Reports**: Comprehensive statistics and recommendations
- **Broken Link Detection**: Identifies inaccessible links
- **Quality Distribution**: High/medium/low quality classification

## Usage

### CLI Command

```bash
# Validate a results file
python3 -m lynnapse.cli validate-websites results.json -v --output enhanced.json --report report.json

# Options
--output, -o        Save enhanced data with validation info
--report, -r        Save detailed validation report
--verbose, -v       Show detailed progress
--concurrent, -c    Max concurrent requests (default: 5)
--min-confidence    Filter by minimum confidence threshold
```

### Python API

```python
from lynnapse.core.website_validator import validate_faculty_websites

# Validate faculty data
enhanced_data, report = await validate_faculty_websites(faculty_data)

# Filter high-quality links
from lynnapse.core.website_validator import filter_valid_links
high_quality = filter_valid_links(enhanced_data, min_confidence=0.8)
```

### Web Interface

1. **Load Results**: View faculty results in the web interface
2. **Validate Button**: Click "Validate Websites" in the results modal
3. **Enhanced Display**: Links show categories, confidence, and status
4. **Validation Report**: Detailed statistics and recommendations

## Output Structure

### Enhanced Faculty Data
Each faculty member gets additional validation fields:

```json
{
  "name": "John Doe",
  "personal_website": "https://scholar.google.com/citations?user=...",
  "personal_website_validation": {
    "type": "google_scholar",
    "is_valid": true,
    "is_accessible": true,
    "confidence": 0.95,
    "title": "John Doe - Google Scholar",
    "error": null
  },
  "link_quality_score": 0.87
}
```

### Validation Report
```json
{
  "total_faculty": 43,
  "link_categories": {
    "google_scholar": 15,
    "university_profile": 43,
    "social_media": 8,
    "personal_website": 12
  },
  "validation_stats": {
    "valid_links": 78,
    "accessible_links": 74,
    "broken_links": 4,
    "redirected_links": 6
  },
  "quality_distribution": {
    "high_quality": 28,
    "medium_quality": 12,
    "low_quality": 3
  },
  "recommendations": [
    "Found 8 social media links. Consider filtering these out.",
    "High broken link rate detected. Consider re-scraping or manual verification."
  ]
}
```

## Link Categorization Logic

### Domain-Based Classification
- **Academic Domains**: `.edu`, `.ac.uk`, `.ac.jp`, etc.
- **Social Media**: `facebook.com`, `twitter.com`, `linkedin.com`
- **Academic Profiles**: `scholar.google.com`, `researchgate.net`, `orcid.org`
- **Publications**: `pubmed.ncbi.nlm.nih.gov`, `arxiv.org`, `doi.org`

### Path-Based Heuristics
- **Faculty Patterns**: `/faculty/`, `/people/`, `/directory/`, `/profile/`
- **Lab Patterns**: `/lab/`, `/group/`, `/center/`, `/institute/`
- **Personal Patterns**: `/~username/`, `/personal/`, `/home/`

### Confidence Scoring
Confidence levels indicate categorization certainty:
- **0.9-1.0**: Very high confidence (e.g., Google Scholar profiles)
- **0.8-0.9**: High confidence (e.g., university faculty pages)
- **0.7-0.8**: Medium-high confidence (e.g., academic domains)
- **0.5-0.7**: Medium confidence (e.g., personal sites)
- **0.3-0.5**: Low confidence (e.g., unknown domains)
- **0.0-0.3**: Very low confidence (e.g., invalid URLs)

## Integration Points

### Scraping Pipeline
The validator can be integrated into scraping workflows:

```python
# In adaptive scraping
from lynnapse.core.website_validator import validate_faculty_websites

async def enhanced_scraping_flow():
    # 1. Extract faculty data
    faculty_data = await scrape_faculty()
    
    # 2. Validate and enhance links
    enhanced_data, report = await validate_faculty_websites(faculty_data)
    
    # 3. Filter high-quality results
    quality_data = filter_valid_links(enhanced_data, min_confidence=0.7)
    
    return quality_data, report
```

### Quality Assurance
Use validation reports to improve scraping logic:

```python
def analyze_extraction_quality(report):
    """Analyze validation report to identify extraction issues."""
    
    social_media_rate = report['link_categories'].get('social_media', 0) / report['total_faculty']
    broken_link_rate = report['validation_stats']['broken_links'] / report['validation_stats']['valid_links']
    
    if social_media_rate > 0.2:
        print("Warning: High social media link rate - improve extraction selectors")
    
    if broken_link_rate > 0.1:
        print("Warning: High broken link rate - check URL extraction logic")
```

### 🔄 Secondary Link Finding (Social Media Replacement)

**Purpose**: Replace social media links with appropriate academic sources of truth.

**Scope**: The secondary link finder should **ONLY** target social media links for replacement, as these are not appropriate sources of truth for academic research.

#### Replacement Logic

```python
def identify_secondary_scraping_candidates(faculty_data):
    """
    Identify faculty with social media links that need academic replacements.
    
    IMPORTANT: Only social media links should be targeted for replacement.
    Other link types (university profiles, Google Scholar, etc.) are valuable and should be preserved.
    """
    candidates = []
    good_links = []
    
    # ONLY target social media links for replacement
    needs_replacement = {'social_media'}
    
    # Preserve these valuable link types
    good_types = {
        'google_scholar',      # High value academic profiles
        'personal_website',    # Personal academic sites
        'lab_website',         # Research lab sites
        'academic_profile',    # ResearchGate, Academia.edu
        'university_profile'   # Official faculty pages
    }
    
    for faculty in faculty_data:
        has_social_media_only = False
        has_good_academic_links = False
        
        # Check all link fields for social media vs academic content
        for field in ['profile_url', 'personal_website', 'lab_website']:
            validation = faculty.get(f"{field}_validation")
            if validation:
                link_type = validation['type']
                
                if link_type in needs_replacement:
                    has_social_media_only = True
                
                if link_type in good_types:
                    has_good_academic_links = True
        
        # Only replace if faculty ONLY has social media links
        if has_social_media_only and not has_good_academic_links:
            faculty_copy = faculty.copy()
            faculty_copy['needs_secondary_scraping'] = True
            faculty_copy['replacement_reason'] = 'social_media_only'
            candidates.append(faculty_copy)
        else:
            good_links.append(faculty)
    
    return candidates, good_links
```

#### Search Strategy for Academic Links

When replacing social media links, prioritize finding:

1. **Google Scholar Profiles**: `site:scholar.google.com "Faculty Name"`
2. **University Faculty Pages**: `"Faculty Name" site:university.edu`
3. **Personal Academic Sites**: `"Faculty Name" research academic`
4. **Lab/Group Websites**: `"Faculty Name" laboratory research group`

#### Quality Criteria for Replacements

New links must meet these criteria to replace social media links:
- **Domain Authority**: Prefer `.edu`, `.org`, academic domains
- **Content Relevance**: Must contain academic/research content
- **Accessibility**: Link must be accessible and functional
- **Confidence Score**: Minimum 0.7 confidence in categorization

## 🐛 Known Issues & Debugging

### Issue 1: API Endpoint 404 Error (RESOLVED)
**Problem**: `/api/find-better-links` endpoint returning 404 Not Found  
**Cause**: Web server running old code without endpoint  
**Solution**: Restart web server with `python3 -m lynnapse.web.run`

### Issue 2: Google Search Rate Limiting (ACTIVE)
**Problem**: 429 Too Many Requests errors during secondary link finding  
**Impact**: 0% success rate in finding replacement links  
**Mitigation**: 
- Add rate limiting (1 request per 2 seconds)
- Implement exponential backoff
- Cache search results
- Consider alternative search APIs

### Issue 3: Secondary Link Finder Scope
**Problem**: System was targeting all low-quality links, not just social media  
**Clarification**: Only social media links should be replaced  
**Status**: Requirements documented, implementation pending

### Debugging Commands

```bash
# Test endpoint directly
curl -X POST http://localhost:8000/api/find-better-links \
  -H "Content-Type: application/json" \
  -d '{"faculty_data": [...]}'

# Check available routes
python3 -c "from lynnapse.web.app import create_app; app = create_app(); print([route.path for route in app.routes if hasattr(route, 'path')])"

# Validate specific faculty data
python3 -m lynnapse.cli validate-websites test_data.json -v

# Test secondary scraping
python3 -m lynnapse.cli find-better-links test_data.json --dry-run
```

## Performance Considerations

### Concurrent Requests
- **Default**: 5 concurrent requests to avoid overwhelming servers
- **Adjustable**: Use `--concurrent` flag or `max_concurrent` parameter
- **Rate Limiting**: Built-in delays between requests

### Timeout Handling
- **Default Timeout**: 10 seconds per request
- **Graceful Degradation**: Continues with other links if some timeout
- **Error Handling**: Captures and reports specific error types

### Resource Usage
- **Memory**: Processes faculty in batches to manage memory
- **Network**: Respects robots.txt and rate limits
- **Caching**: Future versions may cache validation results

## Best Practices

### 1. Validation Workflow
```bash
# Step 1: Run initial scraping
python3 -m lynnapse.cli adaptive-scrape "Carnegie Mellon University" -d psychology -o raw_results.json

# Step 2: Validate websites
python3 -m lynnapse.cli validate-websites raw_results.json -o validated_results.json -r validation_report.json -v

# Step 3: Review recommendations
cat validation_report.json | jq '.recommendations'

# Step 4: Filter high-quality results
python3 -c "
import json
with open('validated_results.json') as f:
    data = json.load(f)
high_quality = [f for f in data['faculty'] if f.get('link_quality_score', 0) >= 0.8]
print(f'High quality faculty: {len(high_quality)}/{len(data[\"faculty\"])}')
"
```

### 2. Quality Thresholds
- **High Quality**: `link_quality_score >= 0.8` - Use for final datasets
- **Medium Quality**: `link_quality_score >= 0.6` - Review manually
- **Low Quality**: `link_quality_score < 0.6` - Needs re-scraping

### 3. Link Filtering
```python
def filter_faculty_by_link_types(faculty_data, desired_types):
    """Filter faculty by desired link types."""
    filtered = []
    
    for faculty in faculty_data:
        has_desired_link = False
        
        for field in ['profile_url', 'personal_website', 'lab_website']:
            validation = faculty.get(f'{field}_validation')
            if validation and validation['type'] in desired_types:
                has_desired_link = True
                break
        
        if has_desired_link:
            filtered.append(faculty)
    
    return filtered

# Example: Get faculty with Google Scholar or personal websites
quality_faculty = filter_faculty_by_link_types(
    enhanced_data, 
    ['google_scholar', 'personal_website']
)
```

## Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   # Ensure all dependencies are installed
   pip install aiohttp>=3.8.0
   ```

2. **Network Timeouts**
   ```bash
   # Reduce concurrent requests
   python3 -m lynnapse.cli validate-websites data.json --concurrent 2
   ```

3. **Memory Issues**
   ```bash
   # Process smaller batches
   python3 -c "
   import json
   with open('large_data.json') as f:
       data = json.load(f)
   
   # Split into smaller files
   batch_size = 50
   for i in range(0, len(data['faculty']), batch_size):
       batch = data['faculty'][i:i+batch_size]
       with open(f'batch_{i//batch_size}.json', 'w') as f:
           json.dump({'faculty': batch}, f)
   "
   ```

### Debug Mode
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# This will show detailed validation progress
enhanced_data, report = await validate_faculty_websites(faculty_data)
```

## Future Enhancements

### Planned Features
- **Personal Website Scraping**: Extract additional data from validated personal sites
- **Link Caching**: Cache validation results to avoid re-checking
- **Machine Learning**: Improve categorization with ML models
- **Batch Processing**: Handle very large datasets efficiently
- **Custom Categories**: Allow users to define custom link categories

### API Extensions
- **Real-time Validation**: WebSocket API for live validation updates
- **Bulk Operations**: Validate multiple result files simultaneously
- **Export Formats**: CSV, Excel exports with validation data
- **Integration Webhooks**: Notify external systems of validation completion 