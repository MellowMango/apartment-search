"""
Lynnapse CLI interface.
"""

import asyncio
import logging
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn

from lynnapse.config import get_settings, get_seed_loader
from lynnapse.db import get_client
from lynnapse.scrapers import ScraperOrchestrator
from lynnapse.flows.scrape import run_university_scrape


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
def scrape(
    university: str = typer.Argument(..., help="University name to scrape"),
    program: Optional[str] = typer.Option(None, "--program", "-p", help="Specific program to scrape"),
    output_dir: str = typer.Option("output", "--output", "-o", help="Output directory"),
    max_concurrent: int = typer.Option(3, "--concurrent", "-c", help="Max concurrent requests"),
    headless: bool = typer.Option(True, "--headless/--no-headless", help="Run browser in headless mode"),
    save_html: bool = typer.Option(False, "--save-html", help="Save raw HTML files"),
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Verbose logging"),
):
    """Scrape a university's programs and faculty."""
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


@app.command()
def list_universities():
    """List available universities in seed configurations."""
    seed_loader = get_seed_loader()
    
    if not seed_loader.universities:
        console.print("[yellow]No universities found in seed configurations[/yellow]")
        console.print("[blue]Run 'lynnapse create-seed' to create an example seed file[/blue]")
        return
    
    console.print("[bold]Available Universities:[/bold]")
    
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
def init_db():
    """Initialize database indexes."""
    async def initialize():
        try:
            client = await get_client()
            await client.create_indexes()
            console.print("[green]✓ Database indexes created successfully![/green]")
        except Exception as e:
            console.print(f"[red]✗ Failed to create indexes: {e}[/red]")
    
    asyncio.run(initialize())


@app.command()
def version():
    """Show version information."""
    console.print("[bold]Lynnapse v0.1.0[/bold]")
    console.print("[blue]University Program & Faculty Scraper[/blue]")


if __name__ == "__main__":
    app() 