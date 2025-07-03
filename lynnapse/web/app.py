"""
Simple web interface for Lynnapse scraper.

Provides a basic UI for inputting scraping targets and viewing results.
Designed to be easily removable without affecting core functionality.
"""

import asyncio
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from fastapi import FastAPI, Request, Form, HTTPException, Query, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from lynnapse.scrapers.university.arizona_psychology import ArizonaPsychologyScraper
from lynnapse.core import MongoWriter
# from ..flows.scrape_flow import UniversityScrapeFlow  # Commented out to avoid Prefect dependency for now
from ..config.university_database import get_university_suggestions, get_department_suggestions, university_db
import logging
import os

def json_serializer(obj):
    """JSON serializer for objects not serializable by default json code"""
    if isinstance(obj, datetime):
        return obj.isoformat()
    elif hasattr(obj, 'isoformat'):
        return obj.isoformat()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    elif hasattr(obj, '__dict__'):
        return obj.__dict__
    return str(obj)

# Configure logging to show INFO level messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Configuration
RESULTS_DIR = "scrape_results"
RESULTS_SUBDIR = os.path.join(RESULTS_DIR, "adaptive")

# Ensure results directories exist
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(RESULTS_SUBDIR, exist_ok=True)

def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    
    app = FastAPI(
        title="Lynnapse Web Interface",
        description="Simple web interface for university faculty scraping",
        version="1.0.0"
    )
    
    # Setup templates and static files
    web_dir = Path(__file__).parent
    templates = Jinja2Templates(directory=web_dir / "templates")
    
    # Create static directory if it doesn't exist
    static_dir = web_dir / "static"
    static_dir.mkdir(exist_ok=True)
    
    try:
        app.mount("/static", StaticFiles(directory=static_dir), name="static")
    except RuntimeError:
        pass  # Static files already mounted or directory doesn't exist
    
    @app.on_event("startup")
    async def startup_event():
        """Initialize the university database on startup."""
        try:
            await university_db.initialize(use_api=False)  # Start with backup data
            logger.info("University database initialized")
        except Exception as e:
            logger.error(f"Failed to initialize university database: {e}")
    
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Home page with scraping interface."""
        return templates.TemplateResponse("index.html", {
            "request": request,
            "title": "Lynnapse Scraper"
        })
    
    @app.get("/scrape", response_class=HTMLResponse)
    async def scrape_page(request: Request):
        """Scraping interface page."""
        return templates.TemplateResponse("scrape.html", {
            "request": request,
            "title": "Scrape University Data"
        })
    
    @app.post("/api/adaptive-scrape")
    async def start_adaptive_scrape(request: Request):
        """Start an adaptive scraping job."""
        try:
            data = await request.json()
            university_name = data.get('university_name')
            department_name = data.get('department_name')
            max_faculty = int(data.get('max_faculty', 100))
            
            if not university_name or not department_name:
                return JSONResponse({
                    "success": False,
                    "message": "University name and department name are required"
                })
            
            # Use the adaptive scraper directly (not via subprocess)
            from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler
            
            logger.info(f"Starting adaptive scrape for {university_name} - {department_name}")
            
            # Create and run the adaptive crawler with comprehensive extraction
            # Always enable lab discovery and detailed profile extraction for complete results
            crawler = AdaptiveFacultyCrawler(enable_lab_discovery=True)
            
            try:
                scrape_result = await crawler.scrape_university_faculty(
                    university_name=university_name,
                    department_filter=department_name,
                    max_faculty=max_faculty if max_faculty > 0 else None
                )
                
                logger.info(f"Scrape completed: success={scrape_result.get('success')}, faculty_count={len(scrape_result.get('faculty', []))}")
                
                # Case 1: Scrape was successful and found faculty
                if scrape_result.get('success') and scrape_result.get('faculty'):
                    faculty_data = scrape_result['faculty']
                    
                    # Format faculty data for web interface (preview)
                    formatted_faculty = [{
                        'name': f.get('name', 'Unknown'),
                        'title': f.get('title', ''),
                        'email': f.get('email', ''),
                        'website': f.get('profile_url', '')
                    } for f in faculty_data[:10]]
                    
                    metadata = scrape_result.get('metadata', {})
                    
                    result = {
                        'success': True,
                        'faculty': formatted_faculty,
                        'message': f"Successfully extracted {len(faculty_data)} faculty from {university_name} {department_name}",
                        'total_count': len(faculty_data),
                        'confidence': metadata.get('discovery_confidence', 0.0),
                        'departments_processed': metadata.get('departments_processed', 1),
                        'metadata': metadata
                    }
                
                # Case 2: Scrape was successful but found zero faculty
                elif scrape_result.get('success'):
                    result = {
                        'success': True,
                        'faculty': [],
                        'message': f"✅ Found the department page for {department_name}, but couldn't extract any faculty. The page layout might be unusual.",
                        'total_count': 0,
                        'metadata': scrape_result.get('metadata', {})
                    }
                    # We still save the result, as the discovery was successful
                    scrape_result['faculty'] = [] # Ensure faculty list is not None
                
                # Case 3: Scrape failed
                else:
                    error_msg = scrape_result.get('error', 'Unknown error')
                    
                    # Fix: Handle case where error_msg could be None
                    if error_msg and "Could not find base URL" in error_msg:
                        suggestion = f"❌ Could not find the official website for {university_name}. Please check the university name spelling and try again."
                    elif error_msg and "URL discovery failed" in error_msg:
                        suggestion = f"❌ Network error when discovering {university_name}'s website structure. Please try again."
                    elif error_msg and "No departments found" in error_msg:
                        suggestion = f"❌ Could not find the {department_name} department at {university_name}. Try 'Psychology', 'Computer Science', or 'Engineering'."
                    else:
                        suggestion = f"❌ Error extracting faculty data from {university_name} {department_name}: {error_msg or 'Unknown error'}"
                    
                    result = {
                        'success': False,
                        'faculty': [],
                        'message': suggestion,
                        'total_count': 0,
                        'error': error_msg
                    }
                    
            finally:
                await crawler.close()
            
            # Save results to file only if the discovery was successful (even if no faculty)
            if result.get('success'):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                safe_university = university_name.replace(' ', '_').replace('/', '_')
                safe_department = department_name.replace(' ', '_').replace('/', '_')
                output_file = f"scrape_results/adaptive/{safe_university}_{safe_department}_{timestamp}.json"
                
                # Create the full result data including all faculty (not just preview)
                full_result = {
                    'university_name': university_name,
                    'department_name': department_name,
                    'faculty': scrape_result.get('faculty', []),  # All faculty data
                    'metadata': result.get('metadata', {}),
                    'timestamp': timestamp,
                    'scrape_type': 'adaptive',
                    'total_count': result.get('total_count', 0)
                }
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(full_result, f, indent=2, ensure_ascii=False)
                
                return JSONResponse({
                    "success": True,
                    "message": f"Successfully scraped {result.get('total_count', 0)} faculty members from {university_name} {department_name}",
                    "data": result.get('faculty', [])[:10],  # Return first 10 for preview
                    "total_count": result.get('total_count', 0),
                    "output_file": output_file,
                    "timestamp": timestamp,
                    "university": university_name,
                    "department": department_name
                })
            else:
                return JSONResponse({
                    "success": False,
                    "message": result.get('message', 'Scraping failed for unknown reason')
                })
                
        except Exception as e:
            logger.error(f"Adaptive scraping failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return JSONResponse({
                "success": False,
                "message": f"Scraping failed: {str(e)}",
                "error": str(e)
            })

    @app.post("/api/scrape")
    async def start_scrape(
        university_type: str = Form(...),
        custom_url: Optional[str] = Form(None),
        include_profiles: bool = Form(False)
    ):
        """Start a scraping job."""
        try:
            if university_type == "arizona-psychology":
                # Use the existing Arizona Psychology scraper
                async with ArizonaPsychologyScraper() as scraper:
                    faculty_data = await scraper.scrape_all_faculty(
                        include_detailed_profiles=include_profiles
                    )
                    
                    # Save to organized folder structure
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    output_file = f"scrape_results/legacy/arizona_psychology_{timestamp}.json"
                    
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump({
                            'university_name': 'University of Arizona',
                            'department_name': 'Psychology',
                            'faculty': faculty_data,
                            'timestamp': timestamp,
                            'scrape_type': 'legacy',
                            'total_count': len(faculty_data)
                        }, f, indent=2, ensure_ascii=False)
                    
                    return JSONResponse({
                        "success": True,
                        "message": f"Scraped {len(faculty_data)} faculty members",
                        "data": faculty_data[:10],  # Return first 10 for preview
                        "total_count": len(faculty_data),
                        "output_file": output_file,
                        "timestamp": timestamp
                    })
            
            elif university_type == "custom" and custom_url:
                # For custom URLs, we'll use a generic approach
                return JSONResponse({
                    "success": False,
                    "message": "Custom URL scraping not yet implemented. Use arizona-psychology for now."
                })
            
            else:
                return JSONResponse({
                    "success": False,
                    "message": "Invalid university type or missing URL"
                })
                
        except Exception as e:
            return JSONResponse({
                "success": False,
                "message": f"Scraping failed: {str(e)}"
            })
    
    @app.get("/api/results")
    async def get_results():
        """Get recent scraping results from organized folders."""
        try:
            results = []
            
            # Look for files in both adaptive and legacy folders
            for folder in ['scrape_results/adaptive', 'scrape_results/legacy']:
                folder_path = Path(folder)
                if folder_path.exists():
                    json_files = list(folder_path.glob("*.json"))
                    
                    for json_file in json_files:
                        try:
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                            
                            # Handle both new structured format and old format
                            if isinstance(data, dict) and 'faculty' in data:
                                # New structured format
                                university = data.get('university_name', 'Unknown')
                                department = data.get('department_name', 'Unknown')
                                scrape_type = data.get('scrape_type', 'unknown')
                                faculty = data.get('faculty', [])
                                total_count = data.get('total_count', len(faculty))
                            elif isinstance(data, list):
                                # Old format (raw faculty list)
                                faculty = data
                                # Try to extract university/department from first faculty member
                                if faculty and len(faculty) > 0:
                                    first_faculty = faculty[0]
                                    university = first_faculty.get('university', 'Unknown')
                                    department = first_faculty.get('department', 'Unknown')
                                else:
                                    university = 'Unknown'
                                    department = 'Unknown'
                                scrape_type = 'legacy'
                                total_count = len(faculty)
                            else:
                                # Fallback for other formats
                                university = 'Unknown'
                                department = 'Unknown'
                                scrape_type = 'unknown'
                                faculty = []
                                total_count = 0
                            
                            results.append({
                                "filename": json_file.name,
                                "full_path": str(json_file),
                                "timestamp": datetime.fromtimestamp(json_file.stat().st_mtime).isoformat(),
                                "university": university,
                                "department": department,
                                "scrape_type": scrape_type,
                                "count": total_count,
                                "preview": faculty[:3] if isinstance(faculty, list) else []
                            })
                        except Exception as e:
                            logger.warning(f"Failed to process {json_file}: {e}")
                            continue
            
            # Sort by timestamp (newest first)
            results.sort(key=lambda x: x['timestamp'], reverse=True)
            
            return JSONResponse({
                "success": True,
                "results": results[:10]  # Return last 10 results
            })
            
        except Exception as e:
            logger.error(f"Failed to load results: {e}")
            return JSONResponse({
                "success": False,
                "message": f"Failed to load results: {str(e)}"
            })
    
    @app.api_route("/api/results/{filename}", methods=["GET", "DELETE"])
    async def handle_results_file(request: Request, filename: str):
        """Handle both GET and DELETE requests for results files."""
        try:
            # Security check - ensure filename is safe
            if not filename.endswith(".json") or ".." in filename or "/" in filename:
                raise HTTPException(status_code=400, detail="Invalid filename")
            
            # Look for the file in both folders
            file_path = None
            for folder in ['scrape_results/adaptive', 'scrape_results/legacy']:
                potential_path = Path(folder) / filename
                if potential_path.exists():
                    file_path = potential_path
                    break
            
            if not file_path:
                raise HTTPException(status_code=404, detail="File not found")
            
            if request.method == "GET":
                # GET: Return file contents
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Handle both new structured format and old format
                if isinstance(data, dict) and 'faculty' in data:
                    # New structured format
                    faculty_data = data.get('faculty', [])
                    university = data.get('university_name', 'Unknown')
                    department = data.get('department_name', 'Unknown')
                    scrape_type = data.get('scrape_type', 'unknown')
                    total_count = data.get('total_count', len(faculty_data))
                else:
                    # Old format (raw faculty list)
                    faculty_data = data if isinstance(data, list) else [data]
                    university = 'Unknown'
                    department = 'Unknown'
                    scrape_type = 'legacy'
                    total_count = len(faculty_data)
                
                return JSONResponse({
                    "success": True,
                    "filename": filename,
                    "university": university,
                    "department": department,
                    "scrape_type": scrape_type,
                    "count": total_count,
                    "data": faculty_data,
                    "timestamp": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
            
            elif request.method == "DELETE":
                # DELETE: Remove the file
                file_path.unlink()
                logger.info(f"Deleted scrape results file: {filename}")
                
                return JSONResponse({
                    "success": True,
                    "message": f"Successfully deleted {filename}"
                })
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to handle {request.method} request for file {filename}: {e}")
            return JSONResponse({
                "success": False,
                "message": f"Failed to handle request: {str(e)}"
            }, status_code=500)
    
    @app.get("/results", response_class=HTMLResponse)
    async def results_page(request: Request):
        """Results viewing page."""
        return templates.TemplateResponse("results.html", {
            "request": request,
            "title": "Scraping Results"
        })
    
    @app.get("/cli", response_class=HTMLResponse)
    async def cli_page(request: Request):
        """CLI Commands page."""
        try:
            return templates.TemplateResponse("cli_simple.html", {
                "request": request,
                "title": "CLI Interface"
            })
        except Exception as e:
            logger.error(f"CLI page error: {e}")
            return HTMLResponse(f"<h1>CLI Page Error</h1><p>{str(e)}</p>", status_code=500)
    
    @app.get("/api/stats")
    async def get_stats():
        """Get scraping statistics from database."""
        try:
            async with MongoWriter() as writer:
                stats = await writer.get_scraping_statistics("University of Arizona")
                return JSONResponse({
                    "success": True,
                    "stats": stats
                })
        except Exception as e:
            return JSONResponse({
                "success": False,
                "message": f"Failed to get stats: {str(e)}",
                "stats": {
                    "university_name": "University of Arizona",
                    "programs": 0,
                    "faculty": 0,
                    "faculty_with_email": 0,
                    "faculty_with_personal_website": 0,
                    "faculty_with_lab": 0,
                    "lab_sites": 0,
                    "email_capture_rate": 0,
                    "website_detection_rate": 0,
                    "lab_detection_rate": 0
                }
            })
    
    @app.get("/health")
    async def health_check():
        """Health check endpoint."""
        return {"status": "healthy", "service": "lynnapse-web"}
    
    @app.get("/api/universities")
    async def search_universities(q: str = Query("", min_length=0), limit: int = Query(10, le=50)):
        """API endpoint for university autocomplete."""
        try:
            suggestions = await get_university_suggestions(q, limit=limit)
            return {"universities": suggestions}
        except Exception as e:
            logger.error(f"University search failed: {e}")
            return {"universities": []}
    
    @app.get("/api/departments")
    async def search_departments(q: str = Query("", min_length=0), limit: int = Query(10, le=20)):
        """API endpoint for department autocomplete."""
        try:
            suggestions = await get_department_suggestions(q, limit=limit)
            return {"departments": suggestions}
        except Exception as e:
            logger.error(f"Department search failed: {e}")
            return {"departments": []}
    
    @app.get("/api/states")
    async def get_states():
        """Get list of states with universities."""
        try:
            states = university_db.get_states()
            return {"states": [{"code": code, "name": name} for code, name in states]}
        except Exception as e:
            logger.error(f"States fetch failed: {e}")
            return {"states": []}
    
    @app.post("/api/validate-websites")
    async def validate_website_links(request: Request):
        """Validate and categorize website links from faculty data."""
        try:
            data = await request.json()
            faculty_data = data.get('faculty_data', [])
            filename = data.get('filename')  # Optional filename to save back to
            
            if not faculty_data:
                return JSONResponse({
                    "success": False,
                    "message": "No faculty data provided"
                })
            
            logger.info(f"Starting website validation for {len(faculty_data)} faculty members")
            
            # Import and run validation
            from lynnapse.core.website_validator import validate_faculty_websites
            
            enhanced_data, report = await validate_faculty_websites(faculty_data)
            
            # Save enhanced data back to file if filename provided
            if filename and enhanced_data:
                try:
                    import json
                    import os
                    file_path = os.path.join(RESULTS_DIR, filename)
                    
                    if os.path.exists(file_path):
                        # Load existing data structure
                        with open(file_path, 'r') as f:
                            existing_data = json.load(f)
                        
                        # Update faculty data while preserving other metadata
                        existing_data['faculty'] = enhanced_data
                        existing_data['last_validated'] = datetime.now().isoformat()
                        existing_data['validation_report'] = report
                        
                        # Save back to file
                        with open(file_path, 'w') as f:
                            json.dump(existing_data, f, indent=2)
                        
                        logger.info(f"Saved validation results to {filename}")
                    
                except Exception as e:
                    logger.warning(f"Failed to save validation results to file: {e}")
            
            logger.info(f"Website validation completed: {report['validation_stats']['valid_links']} valid links")
            
            return JSONResponse({
                "success": True,
                "enhanced_data": enhanced_data,
                "validation_report": report,
                "filename_updated": filename if filename else None,
                "message": f"Validated {len(enhanced_data)} faculty members"
            })
            
        except Exception as e:
            logger.error(f"Website validation failed: {e}")
            return JSONResponse({
                "success": False,
                "message": f"Validation failed: {str(e)}"
            }, status_code=500)
    
    @app.get("/api/link-categories")
    async def get_link_categories():
        """Get available link categories for filtering."""
        from lynnapse.core.website_validator import LinkType
        
        categories = {
            "google_scholar": {
                "name": "Google Scholar",
                "description": "Google Scholar profiles",
                "icon": "bi-mortarboard",
                "color": "primary"
            },
            "university_profile": {
                "name": "University Profile", 
                "description": "Official university faculty pages",
                "icon": "bi-building",
                "color": "success"
            },
            "personal_website": {
                "name": "Personal Website",
                "description": "Personal academic websites",
                "icon": "bi-person-circle",
                "color": "info"
            },
            "academic_profile": {
                "name": "Academic Profile",
                "description": "ResearchGate, Academia.edu, etc.",
                "icon": "bi-journal-text",
                "color": "secondary"
            },
            "lab_website": {
                "name": "Lab Website",
                "description": "Research laboratory websites",
                "icon": "bi-microscope",
                "color": "warning"
            },
            "social_media": {
                "name": "Social Media",
                "description": "Facebook, Twitter, etc.",
                "icon": "bi-share",
                "color": "danger"
            },
            "publication": {
                "name": "Publication",
                "description": "Journal articles, papers",
                "icon": "bi-file-text",
                "color": "secondary"
            },
            "unknown": {
                "name": "Unknown",
                "description": "Unclassified links",
                "icon": "bi-question-circle",
                "color": "muted"
            },
            "invalid": {
                "name": "Invalid",
                "description": "Invalid or broken links",
                "icon": "bi-x-circle",
                "color": "danger"
            }
        }
        
        return JSONResponse({"categories": categories})
    
    @app.post("/api/find-better-links")
    async def find_better_links(request: Request):
        """Find better academic links for faculty with poor quality links."""
        try:
            data = await request.json()
            faculty_data = data.get('faculty_data', [])
            filename = data.get('filename')  # Optional filename to save back to
            
            if not faculty_data:
                return JSONResponse({
                    "success": False,
                    "message": "No faculty data provided"
                })
            
            logger.info(f"Starting secondary link finding for {len(faculty_data)} faculty members")
            
            # Check if data needs validation first
            needs_validation = any(
                not any(f.get(f"{field}_validation") for field in ['profile_url', 'personal_website', 'lab_website'])
                for f in faculty_data
            )
            
            processed_data = faculty_data
            if needs_validation:
                logger.info("Faculty data needs validation first, running validation...")
                from lynnapse.core.website_validator import validate_faculty_websites
                processed_data, validation_report = await validate_faculty_websites(faculty_data)
                logger.info(f"Validation completed: {validation_report['validation_stats']['valid_links']} valid links")
            
            # Import and run secondary scraping
            from lynnapse.core.website_validator import identify_secondary_scraping_candidates
            from lynnapse.core.secondary_link_finder import enhance_faculty_with_secondary_scraping
            
            # Identify candidates for secondary scraping
            candidates, good_faculty = identify_secondary_scraping_candidates(processed_data)
            
            if not candidates:
                return JSONResponse({
                    "success": True,
                    "enhanced_data": processed_data,
                    "candidates_found": 0,
                    "enhanced_count": 0,
                    "new_links_count": 0,
                    "filename_updated": filename if filename else None,
                    "message": "All faculty already have good quality links!"
                })
            
            logger.info(f"Found {len(candidates)} candidates for secondary scraping")
            
            # Enhance candidates with better links
            enhanced_candidates = await enhance_faculty_with_secondary_scraping(candidates)
            
            # Merge with good faculty (preserve order)
            all_enhanced = []
            enhanced_dict = {f.get('name', ''): f for f in enhanced_candidates}
            good_dict = {f.get('name', ''): f for f in good_faculty}
            
            # Maintain original order
            for original in processed_data:
                name = original.get('name', '')
                if name in enhanced_dict:
                    all_enhanced.append(enhanced_dict[name])
                elif name in good_dict:
                    all_enhanced.append(good_dict[name])
                else:
                    all_enhanced.append(original)
            
            # Count successful enhancements
            enhanced_count = sum(1 for f in enhanced_candidates if 'secondary_link_candidates' in f)
            new_links_count = sum(len(f.get('secondary_link_candidates', [])) for f in enhanced_candidates)
            
            # Save enhanced data back to file if filename provided
            if filename and all_enhanced:
                try:
                    file_path = os.path.join(RESULTS_DIR, filename)
                    
                    if os.path.exists(file_path):
                        # Load existing data structure
                        with open(file_path, 'r') as f:
                            existing_data = json.load(f)
                        
                        # Update faculty data while preserving other metadata
                        existing_data['faculty'] = all_enhanced
                        existing_data['last_secondary_scraping'] = datetime.now().isoformat()
                        existing_data['secondary_scraping_stats'] = {
                            'candidates_found': len(candidates),
                            'enhanced_count': enhanced_count,
                            'new_links_count': new_links_count
                        }
                        
                        # Save back to file
                        with open(file_path, 'w') as f:
                            json.dump(existing_data, f, indent=2)
                        
                        logger.info(f"Saved secondary scraping results to {filename}")
                    
                except Exception as e:
                    logger.warning(f"Failed to save secondary scraping results to file: {e}")
            
            logger.info(f"Secondary scraping completed: {enhanced_count} faculty enhanced, {new_links_count} new links found")
            
            return JSONResponse({
                "success": True,
                "enhanced_data": all_enhanced,
                "candidates_found": len(candidates),
                "enhanced_count": enhanced_count,
                "new_links_count": new_links_count,
                "filename_updated": filename if filename else None,
                "message": f"Found {new_links_count} potential new links for {enhanced_count} faculty members"
            })
            
        except Exception as e:
            logger.error(f"Secondary link finding failed: {e}")
            return JSONResponse({
                "success": False,
                "message": f"Secondary scraping failed: {str(e)}"
            }, status_code=500)
    
    # CLI API Endpoints
    @app.post("/api/cli/adaptive-scrape")
    async def cli_adaptive_scrape(
        university: str = Form(...),
        department: Optional[str] = Form(None),
        max_faculty: Optional[int] = Form(None),
        lab_discovery: bool = Form(False),
        verbose: bool = Form(False)
    ):
        """Execute adaptive scraping command via API."""
        try:
            logger.info(f"CLI API: Starting adaptive scrape for {university}")
            
            # For now, return a success message without actually executing
            # This prevents subprocess issues in the web interface
            return JSONResponse({
                "success": True,
                "message": f"Command prepared for {university}. Please run this command in your terminal:",
                "command": f"python3 -m lynnapse.cli.adaptive_scrape \"{university}\"" + 
                          (f" -d \"{department}\"" if department else "") +
                          (f" -m {max_faculty}" if max_faculty else "") +
                          (" --lab-discovery" if lab_discovery else "") +
                          (" -v" if verbose else ""),
                "note": "For security reasons, commands are shown here for manual execution."
            })
                
        except Exception as e:
            logger.error(f"CLI API error: {e}")
            return JSONResponse({
                "success": False,
                "message": f"Failed to prepare command: {str(e)}"
            })
    
    @app.post("/api/cli/enhance-data")
    async def cli_enhance_data(
        input_file: str = Form(...),
        concurrent: int = Form(3),
        verbose: bool = Form(False),
        skip_validation: bool = Form(False)
    ):
        """Execute data enhancement command via API."""
        try:
            logger.info(f"CLI API: Preparing enhance-data command for {input_file}")
            
            # Build command string
            cmd = f"python3 -m lynnapse.cli.enhance_data scrape_results/adaptive/{input_file}"
            cmd += f" -c {concurrent}"
            if verbose:
                cmd += " -v"
            if skip_validation:
                cmd += " --no-validate"
            
            return JSONResponse({
                "success": True,
                "message": f"Command prepared for enhancing {input_file}. Please run this command in your terminal:",
                "command": cmd,
                "note": "This will transform sparse faculty data into rich profiles with research interests, biographies, and contact info."
            })
                
        except Exception as e:
            logger.error(f"CLI API error: {e}")
            return JSONResponse({
                "success": False,
                "message": f"Failed to prepare command: {str(e)}"
            })
    
    @app.post("/api/full-pipeline")
    async def run_full_pipeline(request: Request):
        """
        Execute the complete academic data pipeline:
        1. Adaptive scraping (university + department)
        2. Data enhancement (profiles, research interests, etc.)
        3. Link enrichment (metadata extraction)
        4. Conversion to new ID-based architecture
        5. Return comprehensive results
        """
        try:
            data = await request.json()
            university_name = data.get('university_name')
            department_name = data.get('department_name')
            max_faculty = int(data.get('max_faculty', 50))
            
            if not university_name or not department_name:
                return JSONResponse({
                    "success": False,
                    "message": "University name and department name are required"
                })
            
            logger.info(f"Starting full pipeline for {university_name} - {department_name}")
            
            # Generate timestamp for this pipeline run (needed for saving regardless of success/failure)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create progress tracking
            pipeline_results = {
                "university_name": university_name,
                "department_name": department_name,
                "started_at": datetime.now().isoformat(),
                "stages": {},
                "final_results": {}
            }
            
            # Stage 1: Adaptive Scraping
            logger.info("Stage 1: Adaptive Scraping")
            pipeline_results["stages"]["1_scraping"] = {"status": "running", "started_at": datetime.now().isoformat()}
            
            from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler
            
            crawler = AdaptiveFacultyCrawler(enable_lab_discovery=True)
            try:
                scrape_result = await crawler.scrape_university_faculty(
                    university_name=university_name,
                    department_filter=department_name,
                    max_faculty=max_faculty if max_faculty > 0 else None
                )
                
                if not scrape_result.get('success') or not scrape_result.get('faculty'):
                    return JSONResponse({
                        "success": False,
                        "message": f"Initial scraping failed: {scrape_result.get('message', 'Unknown error')}",
                        "pipeline_results": pipeline_results
                    })
                
                faculty_data = scrape_result['faculty']
                pipeline_results["stages"]["1_scraping"] = {
                    "status": "completed",
                    "faculty_count": len(faculty_data),
                    "metadata": scrape_result.get('metadata', {}),
                    "completed_at": datetime.now().isoformat()
                }
                
                logger.info(f"Scraping completed: {len(faculty_data)} faculty found")
                
            finally:
                await crawler.close()
            
            # Stage 2: Data Enhancement
            logger.info("Stage 2: Data Enhancement")
            pipeline_results["stages"]["2_enhancement"] = {"status": "running", "started_at": datetime.now().isoformat()}
            
            from lynnapse.core.profile_enricher import ProfileEnricher
            from lynnapse.core.website_validator import validate_faculty_websites
            
            # First validate links
            try:
                validated_faculty, validation_report = await validate_faculty_websites(faculty_data)
                
                # Then enhance profiles
                enricher = ProfileEnricher(max_concurrent=3, timeout=30)
                enhanced_faculty, enhancement_stats = await enricher.enrich_sparse_faculty_data(validated_faculty)
                
                pipeline_results["stages"]["2_enhancement"] = {
                    "status": "completed",
                    "validation_stats": validation_report.get('validation_stats', {}),
                    "enhancement_stats": enhancement_stats,
                    "enhanced_faculty_count": len(enhanced_faculty),
                    "completed_at": datetime.now().isoformat()
                }
                
                logger.info(f"Enhancement completed: {enhancement_stats.get('successfully_enriched', 0)} profiles enhanced")
                
            except Exception as e:
                logger.error(f"Enhancement failed: {e}")
                pipeline_results["stages"]["2_enhancement"] = {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }
                # Continue with original data
                enhanced_faculty = faculty_data
            
            # Stage 3: Comprehensive Link Enrichment (following the correct flow)
            logger.info("Stage 3: Comprehensive Link Enrichment")
            pipeline_results["stages"]["3_link_enrichment"] = {"status": "running", "started_at": datetime.now().isoformat()}
            
            try:
                # Complete flow: directory finding/scraping → link checking → smart link replacement → deep enrichment
                
                # Step 1: Link checking/validation (already done in enhancement stage)
                # Step 2: Smart link replacement (for social media and faculty with no links)
                # Step 3: Deep comprehensive enrichment (huge amounts of data from each link)
                
                from lynnapse.core.link_enrichment import LinkEnrichmentEngine
                from lynnapse.core.smart_link_replacer import SmartLinkReplacer
                
                # First, apply smart link replacement for faculty with missing links
                logger.info("Applying smart link replacement for missing faculty links...")
                replacer = SmartLinkReplacer(timeout=30, max_concurrent=3)
                
                faculty_with_smart_links = []
                for faculty in enhanced_faculty:
                    enhanced_faculty_member = faculty.copy()
                    
                    # Smart replacement for missing Google Scholar links
                    if not faculty.get('google_scholar_url'):
                        scholar_url = await replacer.find_google_scholar_profile(
                            faculty.get('name', ''), 
                            faculty.get('university', '')
                        )
                        if scholar_url:
                            enhanced_faculty_member['google_scholar_url'] = scholar_url
                            enhanced_faculty_member['google_scholar_source'] = 'smart_replacement'
                    
                    # Smart replacement for missing personal websites
                    if not faculty.get('personal_website'):
                        personal_url = await replacer.find_personal_website(
                            faculty.get('name', ''), 
                            faculty.get('university', '')
                        )
                        if personal_url:
                            enhanced_faculty_member['personal_website'] = personal_url
                            enhanced_faculty_member['personal_website_source'] = 'smart_replacement'
                    
                    # Find social media profiles (for context, not primary links)
                    social_profiles = await replacer.find_social_media_profiles(
                        faculty.get('name', ''), 
                        faculty.get('university', '')
                    )
                    if social_profiles:
                        enhanced_faculty_member['social_media_profiles'] = social_profiles
                    
                    faculty_with_smart_links.append(enhanced_faculty_member)
                
                # Now apply deep comprehensive enrichment to all accessible links
                logger.info("Starting deep comprehensive data extraction...")
                
                async with LinkEnrichmentEngine(timeout=60, max_concurrent=3) as enrichment_engine:
                    # Deep comprehensive enrichment - extract huge amounts of data
                    enriched_links_faculty, enrichment_report = await enrichment_engine.enrich_faculty_links(
                        faculty_with_smart_links
                    )
                
                # Merge enriched links back with all faculty
                enriched_dict = {f.get('name', ''): f for f in enriched_links_faculty}
                final_faculty = []
                
                for faculty in faculty_with_smart_links:
                    name = faculty.get('name', '')
                    if name in enriched_dict:
                        final_faculty.append(enriched_dict[name])
                    else:
                        final_faculty.append(faculty)
                
                # Calculate comprehensive metrics
                total_data_points = sum(
                    f.get('total_extracted_data_points', 0) for f in final_faculty
                )
                
                pipeline_results["stages"]["3_link_enrichment"] = {
                    "status": "completed",
                    "faculty_processed": len(final_faculty),
                    "links_processed": enrichment_report.total_links_processed,
                    "successful_enrichments": enrichment_report.successful_enrichments,
                    "scholar_profiles_enriched": enrichment_report.scholar_profiles_enriched,
                    "lab_sites_enriched": enrichment_report.lab_sites_enriched,
                    "university_profiles_enriched": enrichment_report.university_profiles_enriched,
                    "total_data_points_extracted": total_data_points,
                    "smart_links_added": sum(1 for f in final_faculty if f.get('google_scholar_source') == 'smart_replacement' or f.get('personal_website_source') == 'smart_replacement'),
                    "social_media_profiles_found": sum(len(f.get('social_media_profiles', [])) for f in final_faculty),
                    "completed_at": datetime.now().isoformat()
                }
                
                logger.info(f"Comprehensive link enrichment completed: {enrichment_report.successful_enrichments} links enriched, {total_data_points} data points extracted")
                
            except Exception as e:
                logger.error(f"Link enrichment failed: {e}")
                pipeline_results["stages"]["3_link_enrichment"] = {
                    "status": "failed", 
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }
                final_faculty = enhanced_faculty
            
            # Stage 4: Convert to New ID-based Architecture
            logger.info("Stage 4: Converting to ID-based Architecture")
            pipeline_results["stages"]["4_conversion"] = {"status": "running", "started_at": datetime.now().isoformat()}
            
            from lynnapse.core.data_manager import AcademicDataManager
            
            try:
                # Create data manager and convert legacy data
                data_manager = AcademicDataManager()
                
                # Convert the enhanced faculty data
                conversion_result = data_manager.ingest_legacy_faculty_data(final_faculty, f"pipeline_{timestamp}")
                
                # Generate aggregated views for LLM processing
                faculty_views = [data_manager.get_faculty_aggregated_view(fid) for fid in data_manager.faculty_entities.keys()]
                faculty_views = [view for view in faculty_views if view is not None]
                lab_views = [data_manager.get_lab_aggregated_view(lid) for lid in data_manager.lab_entities.keys()]
                lab_views = [view for view in lab_views if view is not None]
                
                pipeline_results["stages"]["4_conversion"] = {
                    "status": "completed",
                    "entities_created": {
                        "faculty": len(data_manager.faculty_entities),
                        "labs": len(data_manager.lab_entities),
                        "departments": len(data_manager.department_entities),
                        "universities": len(data_manager.university_entities)
                    },
                    "associations_created": {
                        "faculty_lab": len(data_manager.faculty_lab_associations),
                        "faculty_department": len(data_manager.faculty_dept_associations),
                        "faculty_enrichment": len(data_manager.faculty_enrichment_associations)
                    },
                    "deduplication_stats": conversion_result,
                    "completed_at": datetime.now().isoformat()
                }
                
                logger.info(f"Conversion completed: {len(faculty_views)} faculty entities created")
                
            except Exception as e:
                logger.error(f"Conversion failed: {e}")
                pipeline_results["stages"]["4_conversion"] = {
                    "status": "failed",
                    "error": str(e),
                    "completed_at": datetime.now().isoformat()
                }
                # Fallback to legacy format
                faculty_views = []
                lab_views = []
            
            # Save comprehensive results
            safe_university = university_name.replace(' ', '_').replace('/', '_')
            safe_department = department_name.replace(' ', '_').replace('/', '_')
            
            # Save detailed pipeline results
            pipeline_file = f"scrape_results/pipeline/{safe_university}_{safe_department}_{timestamp}.json"
            Path("scrape_results/pipeline").mkdir(parents=True, exist_ok=True)
            
            pipeline_results["completed_at"] = datetime.now().isoformat()
            pipeline_results["final_results"] = {
                "legacy_faculty_data": final_faculty,
                "faculty_entities": [view.dict() for view in faculty_views] if faculty_views else [],
                "lab_entities": [view.dict() for view in lab_views] if lab_views else [],
                "total_faculty": len(final_faculty),
                "total_entities": len(faculty_views) if faculty_views else 0
            }
            
            with open(pipeline_file, 'w', encoding='utf-8') as f:
                json.dump(pipeline_results, f, indent=2, ensure_ascii=False, default=str)
            
            # Return comprehensive response
            response_data = {
                "success": True,
                "message": f"Full pipeline completed successfully for {university_name} {department_name}",
                "pipeline_results": {
                    "university_name": university_name,
                    "department_name": department_name,
                    "total_faculty": len(final_faculty),
                    "total_entities": len(faculty_views) if faculty_views else 0,
                    "stages_completed": len([s for s in pipeline_results["stages"].values() if s.get("status") == "completed"]),
                    "stages_failed": len([s for s in pipeline_results["stages"].values() if s.get("status") == "failed"]),
                    "processing_time_minutes": (datetime.now() - datetime.fromisoformat(pipeline_results["started_at"])).total_seconds() / 60,
                    "output_file": pipeline_file
                },
                "preview_data": {
                    "legacy_faculty": final_faculty[:3],  # First 3 faculty in legacy format
                    "faculty_entities": [view.dict() for view in faculty_views[:3]] if faculty_views else [],  # First 3 in new format
                    "lab_entities": [view.dict() for view in lab_views[:2]] if lab_views else []  # First 2 labs
                },
                "stage_summary": {
                    "scraping": pipeline_results["stages"]["1_scraping"],
                    "enhancement": pipeline_results["stages"]["2_enhancement"],
                    "link_enrichment": pipeline_results["stages"]["3_link_enrichment"],
                    "conversion": pipeline_results["stages"]["4_conversion"]
                }
            }
            
            # Use custom JSON serializer to handle datetime objects
            response_json = json.dumps(response_data, default=json_serializer, ensure_ascii=False, indent=2)
            return JSONResponse(json.loads(response_json))
            
        except Exception as e:
            logger.error(f"Full pipeline failed: {e}")
            import traceback
            logger.error(f"Full traceback: {traceback.format_exc()}")
            return JSONResponse({
                "success": False,
                "message": f"Full pipeline failed: {str(e)}",
                "error": str(e)
            })
    
    return app 