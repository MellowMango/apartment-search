"""
Lynnapse CLI interface.
"""

import asyncio
import json
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.table import Table

from lynnapse.config import get_settings, get_seed_loader
from lynnapse.db import get_client
from lynnapse.scrapers.university.arizona_psychology import ArizonaPsychologyScraper

# New modular components
try:
    from lynnapse.flows import main_scrape_flow
    FLOWS_AVAILABLE = True
except ImportError:
    main_scrape_flow = None
    FLOWS_AVAILABLE = False

# Adaptive scraping components
try:
    from lynnapse.core import AdaptiveFacultyCrawler
    ADAPTIVE_AVAILABLE = True
except ImportError:
    AdaptiveFacultyCrawler = None
    ADAPTIVE_AVAILABLE = False

# Enhanced DAG flow components
try:
    from lynnapse.flows.enhanced_scraping_flow import (
        enhanced_faculty_scraping_flow,
        university_enhanced_scraping_flow
    )
    ENHANCED_FLOWS_AVAILABLE = True
except ImportError:
    enhanced_faculty_scraping_flow = None
    university_enhanced_scraping_flow = None
    ENHANCED_FLOWS_AVAILABLE = False

# Legacy imports (may not exist)
try:
    from lynnapse.scrapers import ScraperOrchestrator
    from lynnapse.flows.scrape import run_university_scrape
except ImportError:
    ScraperOrchestrator = None
    run_university_scrape = None


app = typer.Typer(
    name="lynnapse",
    help="Lynnapse - University Program & Faculty Scraper",
    rich_markup_mode="rich"
)
console = Console()


def setup_logging(level: str = "INFO"):
    """Setup logging with Rich handler."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(message)s",
        datefmt="[%X]",
        handlers=[RichHandler(rich_tracebacks=True)]
    )


@app.command()
def scrape_university(
    university: str = typer.Argument(..., help="University identifier (e.g., 'arizona-psychology')"),
    output_format: str = typer.Option("json", "--format", "-f", help="Output format: json, mongodb"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path"),
    include_profiles: bool = typer.Option(False, "--profiles", help="Scrape detailed faculty profiles (slower)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """Scrape university faculty using specialized scrapers."""
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    async def run_university_scrape():
        nonlocal output_file  # Fix scope issue
        try:
            # Select scraper based on university identifier
            if university == "arizona-psychology":
                async with ArizonaPsychologyScraper() as scraper:
                    console.print(f"🎓 Scraping {scraper.university_name} - {scraper.department}")
                    
                    faculty_data = await scraper.scrape_all_faculty(
                        include_detailed_profiles=include_profiles
                    )
                    
                    # Output results
                    if output_format == "json":
                        if not output_file:
                            timestamp = int(asyncio.get_event_loop().time())
                            output_file = f"arizona_psychology_faculty_{timestamp}.json"
                        
                        with open(output_file, 'w', encoding='utf-8') as f:
                            json.dump(faculty_data, f, indent=2, ensure_ascii=False)
                        
                        console.print(f"💾 Saved {len(faculty_data)} faculty to {output_file}")
                    
                    elif output_format == "mongodb":
                        # TODO: Implement MongoDB saving
                        console.print("📦 MongoDB output not yet implemented")
                    
                    # Display statistics
                    console.print(f"\n📊 Scraping Results:")
                    console.print(f"   Total Faculty: {len(faculty_data)}")
                    console.print(f"   With Email: {sum(1 for f in faculty_data if f.get('email'))}")
                    console.print(f"   With Personal Website: {sum(1 for f in faculty_data if f.get('personal_website'))}")
                    console.print(f"   With Lab: {sum(1 for f in faculty_data if f.get('lab_name'))}")
                    
                    return faculty_data
            else:
                console.print(f"[red]Unknown university identifier: {university}[/red]")
                console.print("[yellow]Available: arizona-psychology[/yellow]")
                return None
                
        except Exception as e:
            console.print(f"[red]✗ Scrape failed: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            return None
    
    asyncio.run(run_university_scrape())


@app.command()
def test_scraper(
    university: str = typer.Argument("arizona-psychology", help="University scraper to test"),
    save_results: bool = typer.Option(True, "--save/--no-save", help="Save test results to file"),
):
    """Test university scrapers with sample data."""
    
    async def run_test():
        try:
            if university == "arizona-psychology":
                from lynnapse.scrapers.test_scrapers import test_arizona_psychology_scraper
                
                console.print("🧪 Testing Arizona Psychology scraper...")
                faculty_data = await test_arizona_psychology_scraper(
                    save_to_json=save_results,
                    include_profiles=False
                )
                
                console.print(f"✅ Test completed: {len(faculty_data)} faculty scraped")
                
            else:
                console.print(f"[red]Unknown university scraper: {university}[/red]")
                console.print("[yellow]Available: arizona-psychology[/yellow]")
                
        except Exception as e:
            console.print(f"[red]✗ Test failed: {e}[/red]")
    
    asyncio.run(run_test())


@app.command()
def scrape(
    university: str = typer.Argument(..., help="University name to scrape"),
    program: Optional[str] = typer.Option(None, "--program", "-p", help="Specific program to scrape"),
    output_dir: str = typer.Option("output", "--output", "-o", help="Output directory"),
    max_concurrent: int = typer.Option(3, "--concurrent", "-c", help="Max concurrent requests"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    save_html: bool = typer.Option(False, "--save-html", help="Save raw HTML files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """Scrape a university's programs and faculty (legacy seed-based scraper)."""
    
    if run_university_scrape is None:
        console.print("[red]Legacy scraper not available. Use 'scrape-university' command instead.[/red]")
        return
    
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    logger = logging.getLogger(__name__)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Initializing scraper...", total=None)
        
        async def run_scrape():
            try:
                # Load seed configuration
                seed_loader = get_seed_loader()
                university_config = seed_loader.get_university_config(university)
                
                if not university_config:
                    console.print(f"[red]University '{university}' not found in seed configurations[/red]")
                    console.print(f"[yellow]Available universities: {list(seed_loader.universities.keys())}[/yellow]")
                    return
                
                progress.update(task, description="Starting scrape job...")
                
                # Run the scrape
                result = await run_university_scrape(
                    university_name=university,
                    program_name=program,
                    output_directory=output_dir,
                    max_concurrent=max_concurrent,
                    headless=headless,
                    save_html=save_html
                )
                
                if result["success"]:
                    console.print(f"[green]✓ Scrape completed successfully![/green]")
                    console.print(f"[blue]Programs scraped: {result.get('programs_scraped', 0)}[/blue]")
                    console.print(f"[blue]Faculty scraped: {result.get('faculty_scraped', 0)}[/blue]")
                    console.print(f"[blue]Lab sites scraped: {result.get('lab_sites_scraped', 0)}[/blue]")
                else:
                    console.print(f"[red]✗ Scrape failed: {result.get('error', 'Unknown error')}[/red]")
                
                progress.update(task, description="Scrape completed")
                
            except Exception as e:
                logger.error(f"Scrape failed: {e}")
                console.print(f"[red]✗ Scrape failed: {e}[/red]")
        
        asyncio.run(run_scrape())


@app.command("adaptive-scrape")
def adaptive_scrape(
    university_name: str = typer.Argument(..., help="University name (e.g., 'Arizona State University')"),
    department: Optional[str] = typer.Option(None, "--department", "-d", help="Target specific department (e.g., 'psychology')"),
    max_faculty: Optional[int] = typer.Option(None, "--max-faculty", "-m", help="Maximum number of faculty to extract"),
    base_url: Optional[str] = typer.Option(None, "--base-url", "-u", help="Base URL if known"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file path (JSON)"),
    enable_lab_discovery: bool = typer.Option(True, "--lab-discovery/--no-lab-discovery", help="Enable enhanced lab discovery features"),
    enable_external_search: bool = typer.Option(False, "--external-search/--no-external-search", help="Enable external search APIs (costs money)"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose logging"),
):
    """
    Scrape faculty from any university using adaptive strategies.
    
    This command can automatically discover and adapt to any university's
    website structure without manual configuration.
    
    Examples:
    
        # Scrape psychology faculty from Arizona State University
        lynnapse adaptive-scrape "Arizona State University" -d psychology -m 10
        
        # Scrape all faculty from Stanford University
        lynnapse adaptive-scrape "Stanford University" -o stanford_faculty.json
        
        # Scrape with enhanced lab discovery and external search
        lynnapse adaptive-scrape "MIT" --external-search -v
    """
    if not ADAPTIVE_AVAILABLE:
        console.print("[red]Adaptive scraping not available. Please check lynnapse.core module.[/red]")
        return
    
    # Configure logging
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    async def run_adaptive_scrape():
        console.print(f"🎯 Starting adaptive scrape for [bold]{university_name}[/bold]")
        
        if department:
            console.print(f"📚 Targeting department: [blue]{department}[/blue]")
        if max_faculty:
            console.print(f"👥 Max faculty limit: [blue]{max_faculty}[/blue]")
        
        # Initialize the adaptive crawler
        crawler = AdaptiveFacultyCrawler(
            enable_lab_discovery=enable_lab_discovery,
            enable_external_search=enable_external_search
        )
        
        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task("Discovering university structure...", total=None)
                
                result = await crawler.scrape_university_faculty(
                    university_name=university_name,
                    department_filter=department,
                    max_faculty=max_faculty,
                    base_url=base_url
                )
                
                progress.update(task, description="Scraping completed")
            
            # Display results
            if result["success"]:
                console.print(f"[green]✅ Successfully scraped {result['metadata']['total_faculty']} faculty[/green]")
                console.print(f"🏛️  Base URL: [blue]{result['base_url']}[/blue]")
                console.print(f"📊 Departments processed: [blue]{result['metadata']['departments_processed']}[/blue]")
                console.print(f"🎯 Discovery confidence: [blue]{result['metadata']['discovery_confidence']:.2f}[/blue]")
                
                # Show department breakdown
                if result['metadata']['department_results']:
                    console.print("\n[bold]📚 Department Results:[/bold]")
                    for dept_name, dept_info in result['metadata']['department_results'].items():
                        console.print(f"  • [green]{dept_name}[/green]: {dept_info['faculty_count']} faculty "
                                     f"(confidence: {dept_info['confidence']:.2f})")
                
                # Show sample faculty
                if result["faculty"]:
                    console.print(f"\n[bold]👥 Sample Faculty (showing first 3):[/bold]")
                    for i, faculty in enumerate(result["faculty"][:3]):
                        console.print(f"  {i+1}. [green]{faculty['name']}[/green]")
                        if faculty.get('title'):
                            console.print(f"     Title: [blue]{faculty['title']}[/blue]")
                        if faculty.get('email'):
                            console.print(f"     Email: [blue]{faculty['email']}[/blue]")
                        if faculty.get('lab_urls'):
                            console.print(f"     Lab URLs: [yellow]{len(faculty['lab_urls'])} found[/yellow]")
                        console.print()
                
                # Show crawler statistics
                stats = crawler.get_stats()
                if any(stats.values()):
                    console.print("[bold]📈 Crawler Statistics:[/bold]")
                    for key, value in stats.items():
                        if value > 0:
                            console.print(f"  • {key.replace('_', ' ').title()}: [blue]{value}[/blue]")
                
                # Save output if requested
                if output:
                    output_path = Path(output)
                    with output_path.open('w') as f:
                        json.dump(result, f, indent=2, default=str)
                    console.print(f"💾 Results saved to [blue]{output_path}[/blue]")
                
            else:
                console.print(f"[red]❌ Scraping failed: {result['error']}[/red]")
                return 1
        
        except Exception as e:
            console.print(f"[red]💥 Unexpected error: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            return 1
        
        finally:
            await crawler.close()
        
        return 0
    
    asyncio.run(run_adaptive_scrape())


@app.command()
def list_universities():
    """List available universities in seed configurations."""
    console.print("[bold]University Scrapers:[/bold]")
    console.print("[green]• arizona-psychology[/green] - University of Arizona Psychology Department")
    console.print("  Captures: Faculty profiles, personal websites, lab information")
    console.print()
    
    seed_loader = get_seed_loader()
    
    if not seed_loader.universities:
        console.print("[yellow]No seed-based universities found[/yellow]")
        console.print("[blue]Run 'lynnapse create-seed' to create seed configurations[/blue]")
        return
    
    console.print("[bold]Seed-based Universities:[/bold]")
    
    for name, config in seed_loader.universities.items():
        console.print(f"[green]• {name}[/green]")
        console.print(f"  [blue]Base URL: {config.base_url}[/blue]")
        console.print(f"  [blue]Programs: {len(config.programs)}[/blue]")
        for program in config.programs:
            console.print(f"    - {program.name} ({program.department})")
        console.print()


@app.command()
def create_seed(
    university_name: str = typer.Argument(..., help="University name"),
    output_path: Optional[str] = typer.Option(None, "--output", "-o", help="Output path for seed file"),
):
    """Create a new seed configuration file."""
    if not output_path:
        safe_name = university_name.lower().replace(" ", "_").replace("-", "_")
        output_path = f"seeds/{safe_name}.yml"
    
    seed_loader = get_seed_loader()
    
    # Create a basic template
    template = {
        "name": university_name,
        "base_url": f"https://{university_name.lower().replace(' ', '')}.edu",
        "programs": [
            {
                "name": "Example Program",
                "department": "Example Department",
                "college": "Example College",
                "program_url": f"https://{university_name.lower().replace(' ', '')}.edu/program",
                "faculty_directory_url": f"https://{university_name.lower().replace(' ', '')}.edu/faculty",
                "program_type": "graduate",
                "selectors": {
                    "faculty_links": ".faculty-list a, .people-list a",
                    "faculty_name": "h1, .name",
                    "faculty_title": ".title, .position",
                    "faculty_email": "a[href^='mailto:']",
                    "research_interests": ".research-interests"
                }
            }
        ],
        "scraping_config": {
            "user_agent": "Mozilla/5.0 (compatible; LynnapseBot/1.0)",
            "wait_for_selector": ".content, .main",
            "timeout": 30
        },
        "rate_limit_delay": 2.0,
        "max_concurrent_requests": 2,
        "max_retries": 3,
        "retry_delay": 5.0
    }
    
    # Ensure directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write the template
    import yaml
    with open(output_path, 'w', encoding='utf-8') as f:
        yaml.dump(template, f, default_flow_style=False, indent=2)
    
    console.print(f"[green]✓ Created seed template: {output_path}[/green]")
    console.print("[blue]Edit the file to customize selectors and URLs for your university[/blue]")


@app.command()
def test_db():
    """Test database connection."""
    async def test_connection():
        try:
            client = await get_client()
            healthy = await client.health_check()
            
            if healthy:
                console.print("[green]✓ Database connection successful![/green]")
                console.print(f"[blue]Database: {client.database_name}[/blue]")
            else:
                console.print("[red]✗ Database connection failed![/red]")
                
        except Exception as e:
            console.print(f"[red]✗ Database connection failed: {e}[/red]")
    
    asyncio.run(test_connection())


@app.command()
def init():
    """Initialize Lynnapse configuration and database."""
    console.print("[bold]Initializing Lynnapse...[/bold]")
    
    async def initialize():
        try:
            # Test database connection
            console.print("🔌 Testing database connection...")
            client = await get_client()
            healthy = await client.health_check()
            
            if healthy:
                console.print("[green]✓ Database connected[/green]")
            else:
                console.print("[red]✗ Database connection failed[/red]")
                return
            
            console.print("[green]✓ Lynnapse initialized successfully![/green]")
            
        except Exception as e:
            console.print(f"[red]✗ Initialization failed: {e}[/red]")
    
    asyncio.run(initialize())


@app.command()
def flow(
    seeds_file: str = typer.Argument("seeds/university_of_arizona.yml", help="Path to seeds YAML file"),
    university: Optional[str] = typer.Option(None, "--university", "-u", help="Filter by university name"),
    department: Optional[str] = typer.Option(None, "--department", "-d", help="Filter by department name"),
    max_programs: int = typer.Option(3, "--max-programs", help="Max concurrent programs"),
    max_faculty: int = typer.Option(5, "--max-faculty", help="Max concurrent faculty"),
    max_labs: int = typer.Option(2, "--max-labs", help="Max concurrent labs"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate configuration only"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """Run the new modular scraping flow with Prefect orchestration."""
    
    if not FLOWS_AVAILABLE:
        console.print("[red]Modular flows not available. Please install requirements and check lynnapse.flows module.[/red]")
        return
    
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    async def run_flow():
        try:
            console.print("🎓 [bold]Starting Lynnapse Modular Scraping Flow[/bold]")
            console.print(f"📁 Seeds file: {seeds_file}")
            if university:
                console.print(f"🏫 University filter: {university}")
            if department:
                console.print(f"🏛️ Department filter: {department}")
            
            # Run the Prefect flow
            result = await main_scrape_flow(
                seeds_file=seeds_file,
                university_filter=university,
                department_filter=department,
                max_concurrent_programs=max_programs,
                max_concurrent_faculty=max_faculty,
                max_concurrent_labs=max_labs,
                dry_run=dry_run
            )
            
            if dry_run:
                console.print("[green]✓ Configuration validation successful![/green]")
                console.print(f"Universities: {result['configuration']['total_universities']}")
                console.print(f"Programs: {result['configuration']['total_programs']}")
            else:
                console.print("[green]✓ Scraping flow completed successfully![/green]")
                console.print(f"Job ID: {result.get('job_id')}")
                console.print(f"Universities: {result.get('universities_processed')}")
                console.print(f"Programs: {result.get('programs_processed')}")
                console.print(f"Faculty: {result.get('faculty_processed')}")
                console.print(f"Execution time: {result.get('execution_time_seconds', 0):.1f}s")
            
            return result
            
        except Exception as e:
            console.print(f"[red]✗ Flow failed: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            return None
    
    asyncio.run(run_flow())


@app.command()
def web(
    host: str = typer.Option("0.0.0.0", "--host", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", help="Port to bind to"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """Start the web interface for interactive scraping."""
    
    try:
        from lynnapse.web.app import create_app
        import uvicorn
        WEB_AVAILABLE = True
    except ImportError:
        WEB_AVAILABLE = False
    
    if not WEB_AVAILABLE:
        console.print("[red]❌ Web interface not available[/red]")
        console.print("[yellow]💡 Install with: pip install fastapi uvicorn jinja2 python-multipart[/yellow]")
        raise typer.Exit(1)
    
    console.print("[blue]🌐 Starting Lynnapse Web Interface...[/blue]")
    console.print(f"[green]📍 Access at: http://localhost:{port}[/green]")
    console.print(f"[cyan]📊 API docs at: http://localhost:{port}/docs[/cyan]")
    console.print("[yellow]🔧 Press Ctrl+C to stop[/yellow]")
    console.print()
    
    try:
        app = create_app()
        uvicorn.run(
            app,
            host=host,
            port=port,
            reload=reload,
            log_level="info"
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]👋 Web interface stopped[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Failed to start web interface: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def validate_websites(
    input_file: str = typer.Argument(..., help="Path to JSON file containing faculty data"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for validated data"),
    report_file: Optional[str] = typer.Option(None, "--report", "-r", help="Output file for validation report"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output"),
    max_concurrent: int = typer.Option(5, "--concurrent", "-c", help="Maximum concurrent requests"),
    min_confidence: float = typer.Option(0.0, "--min-confidence", help="Minimum confidence threshold for filtering")
):
    """
    Validate faculty website links from scraped data.
    
    This tool checks the accessibility and categorizes different types of links
    (personal websites, Google Scholar, university profiles, etc.).
    """
    import subprocess
    import sys
    
    # Build command arguments
    cmd = [sys.executable, "-m", "lynnapse.cli.validate_websites", input_file]
    
    if output_file:
        cmd.extend(["--output", output_file])
    if report_file:
        cmd.extend(["--report", report_file])
    if verbose:
        cmd.append("--verbose")
    if max_concurrent != 5:
        cmd.extend(["--concurrent", str(max_concurrent)])
    if min_confidence != 0.0:
        cmd.extend(["--min-confidence", str(min_confidence)])
    
    # Execute the validation script
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Validation failed with exit code {e.returncode}[/red]")
        raise typer.Exit(e.returncode)
    except Exception as e:
        console.print(f"[red]❌ Failed to run validation: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def find_better_links(
    input_file: str = typer.Argument(..., help="Path to JSON file containing faculty data"),
    output_file: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for enhanced data"),
    targets_file: Optional[str] = typer.Option(None, "--targets", "-t", help="Output file for scraping targets"),
    validate_first: bool = typer.Option(True, "--validate/--no-validate", help="Run validation first"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Only identify candidates, don't scrape"),
    max_concurrent: int = typer.Option(3, "--concurrent", "-c", help="Maximum concurrent requests"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Show detailed output")
):
    """
    Find better academic links for faculty with poor quality links.
    
    This tool identifies faculty with social media links, broken links, or unknown links,
    then performs targeted searches to find their actual academic websites.
    """
    import subprocess
    import sys
    
    # Build command arguments
    cmd = [sys.executable, "lynnapse/cli/secondary_scraping.py", input_file]
    
    if output_file:
        cmd.extend(["--output", output_file])
    if targets_file:
        cmd.extend(["--targets", targets_file])
    if not validate_first:
        cmd.append("--no-validate")
    if dry_run:
        cmd.append("--dry-run")
    if max_concurrent != 3:
        cmd.extend(["--concurrent", str(max_concurrent)])
    if verbose:
        cmd.append("--verbose")
    
    # Execute the secondary scraping script
    try:
        result = subprocess.run(cmd, check=True)
        return result.returncode
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Secondary scraping failed with exit code {e.returncode}[/red]")
        raise typer.Exit(e.returncode)
    except Exception as e:
        console.print(f"[red]❌ Failed to run secondary scraping: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def enhanced_flow(
    seeds_file: str = typer.Argument("seeds/university_of_arizona.yml", help="Path to seeds YAML file"),
    university: Optional[str] = typer.Option(None, "--university", "-u", help="Filter by university name"),
    department: Optional[str] = typer.Option(None, "--department", "-d", help="Filter by department name"),
    max_scraping: int = typer.Option(5, "--max-scraping", help="Max concurrent scraping operations"),
    max_enrichment: int = typer.Option(3, "--max-enrichment", help="Max concurrent enrichment operations"),
    enable_ai: bool = typer.Option(True, "--enable-ai/--disable-ai", help="Enable AI-assisted link discovery"),
    enable_enrichment: bool = typer.Option(True, "--enable-enrichment/--disable-enrichment", help="Enable detailed link enrichment"),
    openai_api_key: Optional[str] = typer.Option(None, "--openai-key", help="OpenAI API key (or use OPENAI_API_KEY env var)"),
    dry_run: bool = typer.Option(False, "--dry-run", help="Validate configuration only"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """
    🚀 Run the enhanced DAG workflow with integrated link enrichment.
    
    This command orchestrates the complete pipeline:
    Scraping → Link Processing → Enrichment → Storage
    
    Features:
    - Adaptive faculty discovery with university structure detection
    - Smart link processing with social media replacement
    - Detailed academic link enrichment with metadata extraction
    - Comprehensive error handling and retry logic
    - Production-ready Docker compatibility
    
    Example usage:
    lynnapse enhanced-flow seeds/university_of_arizona.yml -u "University of Vermont" -d Psychology
    lynnapse enhanced-flow seeds/cmu.yml --enable-ai --max-enrichment 5 -v
    """
    
    if not ENHANCED_FLOWS_AVAILABLE:
        console.print("[red]Enhanced flows not available. Please install requirements and check lynnapse.flows module.[/red]")
        return
    
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    async def run_enhanced_flow():
        try:
            console.print("🚀 [bold]Starting Enhanced DAG Workflow[/bold]")
            console.print(f"📁 Seeds file: {seeds_file}")
            if university:
                console.print(f"🏫 University filter: {university}")
            if department:
                console.print(f"🏛️ Department filter: {department}")
            
            console.print(f"🤖 AI assistance: {'[green]enabled[/green]' if enable_ai else '[red]disabled[/red]'}")
            console.print(f"🔬 Link enrichment: {'[green]enabled[/green]' if enable_enrichment else '[red]disabled[/red]'}")
            
            # Show progress for enhanced flow
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                transient=False
            ) as progress:
                
                if dry_run:
                    task = progress.add_task("🔍 Validating configuration...", total=100)
                else:
                    task = progress.add_task("🎓 Running enhanced scraping flow...", total=100)
                
                progress.update(task, advance=10)
                
                # Run the enhanced Prefect flow
                result = await enhanced_faculty_scraping_flow(
                    seeds_file=seeds_file,
                    university_filter=university,
                    department_filter=department,
                    enable_ai_assistance=enable_ai,
                    enable_link_enrichment=enable_enrichment,
                    max_concurrent_scraping=max_scraping,
                    max_concurrent_enrichment=max_enrichment,
                    openai_api_key=openai_api_key,
                    dry_run=dry_run
                )
                
                progress.update(task, completed=100)
            
            if dry_run:
                console.print("[green]✓ Enhanced configuration validation successful![/green]")
                console.print(f"Universities: {result['configuration']['total_universities']}")
                console.print(f"Programs: {result['configuration']['total_programs']}")
                console.print(f"AI assistance available: {result.get('ai_assistance_available', False)}")
                console.print(f"Link enrichment enabled: {result.get('link_enrichment_enabled', False)}")
            else:
                console.print("[green]✓ Enhanced DAG workflow completed successfully![/green]")
                
                # Display comprehensive results
                table = Table(title="Enhanced Scraping Results", show_header=True, header_style="bold magenta")
                table.add_column("Metric", style="cyan", no_wrap=True)
                table.add_column("Value", style="green")
                
                table.add_row("Job ID", result.get('job_id', 'N/A'))
                table.add_row("Universities Processed", str(result.get('universities_processed', 0)))
                table.add_row("Departments Processed", str(result.get('departments_processed', 0)))
                table.add_row("Faculty Processed", str(result.get('total_faculty_processed', 0)))
                table.add_row("Links Processed", str(result.get('total_links_processed', 0)))
                table.add_row("Links Enriched", str(result.get('total_links_enriched', 0)))
                table.add_row("Execution Time", f"{result.get('execution_time_seconds', 0):.1f}s")
                table.add_row("Throughput", f"{result.get('throughput_faculty_per_second', 0):.2f} faculty/sec")
                
                console.print(table)
                
                # Show detailed results for each university
                if result.get('university_results'):
                    console.print("\n📊 [bold]Detailed Results by University:[/bold]")
                    for univ_result in result['university_results']:
                        console.print(f"🏫 {univ_result['university_name']} - {univ_result['department_name']}")
                        console.print(f"   Faculty: {univ_result['faculty_enriched']}")
                        if univ_result.get('processing_report'):
                            replacement_rate = univ_result['processing_report']['replacement_report'].get('replacement_success_rate', 0)
                            console.print(f"   Link Replacement: {replacement_rate:.1%}")
                        if univ_result.get('enrichment_report'):
                            enrichment_rate = univ_result['enrichment_report'].get('enrichment_success_rate', 0)
                            console.print(f"   Link Enrichment: {enrichment_rate:.1%}")
            
            return result
            
        except Exception as e:
            console.print(f"[red]✗ Enhanced workflow failed: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            return None
    
    asyncio.run(run_enhanced_flow())


@app.command()
def university_enhanced(
    university_config_file: str = typer.Argument(..., help="Path to university configuration file"),
    department: str = typer.Option("Psychology", "--department", "-d", help="Department name"),
    enable_ai: bool = typer.Option(True, "--enable-ai/--disable-ai", help="Enable AI-assisted link discovery"),
    enable_enrichment: bool = typer.Option(True, "--enable-enrichment/--disable-enrichment", help="Enable detailed link enrichment"),
    openai_api_key: Optional[str] = typer.Option(None, "--openai-key", help="OpenAI API key"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """
    🏫 Run enhanced scraping for a single university with full DAG pipeline.
    
    This command processes a single university through the complete enhanced workflow.
    Ideal for testing and debugging specific universities.
    """
    
    if not ENHANCED_FLOWS_AVAILABLE:
        console.print("[red]Enhanced flows not available. Please install requirements and check lynnapse.flows module.[/red]")
        return
    
    log_level = "DEBUG" if verbose else "INFO"
    setup_logging(log_level)
    
    import yaml
    
    async def run_university_enhanced():
        try:
            # Load university configuration
            with open(university_config_file, 'r') as f:
                university_config = yaml.safe_load(f)
            
            console.print(f"🏫 [bold]Starting Enhanced University Scraping[/bold]")
            console.print(f"University: {university_config.get('name', 'Unknown')}")
            console.print(f"Department: {department}")
            
            # Run the enhanced university flow
            result = await university_enhanced_scraping_flow(
                university_config=university_config,
                department_name=department,
                enable_ai_assistance=enable_ai,
                enable_link_enrichment=enable_enrichment,
                openai_api_key=openai_api_key
            )
            
            console.print("[green]✓ Enhanced university scraping completed![/green]")
            
            # Display results
            table = Table(title="University Scraping Results", show_header=True, header_style="bold magenta")
            table.add_column("Metric", style="cyan", no_wrap=True)
            table.add_column("Value", style="green")
            
            table.add_row("University", result.get('university_name', 'N/A'))
            table.add_row("Department", result.get('department_name', 'N/A'))
            table.add_row("Faculty Scraped", str(result.get('faculty_scraped', 0)))
            table.add_row("Faculty Processed", str(result.get('faculty_processed', 0)))
            table.add_row("Faculty Enriched", str(result.get('faculty_enriched', 0)))
            table.add_row("Status", result.get('status', 'Unknown'))
            
            console.print(table)
            
            return result
            
        except Exception as e:
            console.print(f"[red]✗ University enhanced scraping failed: {e}[/red]")
            if verbose:
                import traceback
                console.print(traceback.format_exc())
            return None
    
    asyncio.run(run_university_enhanced())


@app.command()
def version():
    """Show version information."""
    console.print("🎓 [bold]Lynnapse[/bold] v2.0.0 - Enhanced DAG Architecture")
    console.print("University Program & Faculty Scraper with Link Enrichment")
    console.print("✨ Features: Prefect orchestration, smart link processing, AI-assisted discovery, comprehensive enrichment")
    console.print("📋 Available commands:")
    console.print("  • [blue]enhanced-flow[/blue] - Run enhanced DAG workflow with link enrichment (⭐ RECOMMENDED)")
    console.print("  • [blue]university-enhanced[/blue] - Run enhanced scraping for a single university")
    console.print("  • [blue]web[/blue] - Start web interface")
    console.print("  • [blue]flow[/blue] - Run modular scraping flow")
    console.print("  • [blue]scrape-university[/blue] - Run specialized scrapers")
    console.print("  • [blue]adaptive-scrape[/blue] - Run adaptive faculty discovery")
    console.print("  • [blue]validate-websites[/blue] - Check and categorize faculty website links")
    console.print("  • [blue]find-better-links[/blue] - Find better academic links for faculty with poor quality links")


if __name__ == "__main__":
    app() 