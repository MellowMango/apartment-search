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
            include_profiles = data.get('include_profiles', False)
            
            if not university_name or not department_name:
                return JSONResponse({
                    "success": False,
                    "message": "University name and department name are required"
                })
            
            # Use the adaptive scraper directly (not via subprocess)
            from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler
            
            logger.info(f"Starting adaptive scrape for {university_name} - {department_name}")
            
            # Create and run the adaptive crawler
            crawler = AdaptiveFacultyCrawler(enable_lab_discovery=True)  # Enable detailed profile extraction
            
            try:
                scrape_result = await crawler.scrape_university_faculty(
                    university_name=university_name,
                    department_filter=department_name,
                    max_faculty=max_faculty if max_faculty > 0 else None
                )
                
                logger.info(f"Scrape completed: success={scrape_result.get('success')}, faculty_count={len(scrape_result.get('faculty', []))}")
                
                if scrape_result.get('success') and scrape_result.get('faculty'):
                    faculty_data = scrape_result['faculty']
                    
                    # Format faculty data for web interface
                    formatted_faculty = []
                    for faculty in faculty_data[:10]:  # Show first 10 for display
                        formatted_faculty.append({
                            'name': faculty.get('name', 'Unknown'),
                            'title': faculty.get('title', ''),
                            'email': faculty.get('email', ''),
                            'website': faculty.get('profile_url', '')
                        })
                    
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
                else:
                    # Handle failure cases
                    error_msg = scrape_result.get('error', 'Unknown error')
                    
                    if "Could not find base URL" in error_msg or "URL discovery failed" in error_msg:
                        suggestion = f"❌ {university_name} has a complex website structure. Try Stanford University or University of Arizona instead!"
                    elif "No departments found" in error_msg:
                        suggestion = f"❌ Could not find {department_name} department. Try 'Psychology' or 'Computer Science'."
                    else:
                        suggestion = f"❌ No faculty found at {university_name} {department_name}. This university may need special handling."
                    
                    result = {
                        'success': False,
                        'faculty': [],
                        'message': suggestion,
                        'total_count': 0,
                        'error': error_msg
                    }
                    
            finally:
                await crawler.close()
            
            if result.get('success'):
                # Save to organized folder structure  
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
    
    return app 