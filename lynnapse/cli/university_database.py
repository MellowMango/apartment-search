#!/usr/bin/env python3
"""
CLI tool for testing the university database functionality.
"""

import asyncio
import argparse
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns

from ..config.university_database import UniversityDatabase, get_university_suggestions, get_department_suggestions

console = Console()

async def test_university_search(query: str, limit: int = 10):
    """Test university search functionality."""
    console.print(f"[bold blue]Searching for universities matching: '{query}'[/bold blue]")
    
    suggestions = await get_university_suggestions(query, limit)
    
    if not suggestions:
        console.print("[red]No universities found[/red]")
        return
    
    table = Table(title="University Search Results", show_header=True, header_style="bold magenta")
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Location", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Website", style="blue")
    
    for uni in suggestions:
        table.add_row(
            uni["name"],
            uni["location"],
            uni["type"],
            uni["website"][:40] + "..." if len(uni["website"]) > 40 else uni["website"]
        )
    
    console.print(table)

async def test_department_search(query: str = "", limit: int = 10):
    """Test department search functionality."""
    if query:
        console.print(f"[bold blue]Searching for departments matching: '{query}'[/bold blue]")
    else:
        console.print("[bold blue]Showing all available departments[/bold blue]")
    
    suggestions = await get_department_suggestions(query, limit)
    
    if not suggestions:
        console.print("[red]No departments found[/red]")
        return
    
    table = Table(title="Department Search Results", show_header=True, header_style="bold magenta")
    table.add_column("Department", style="cyan", no_wrap=True)
    table.add_column("Category", style="green")
    table.add_column("Common Names", style="yellow")
    
    for dept in suggestions:
        variations = ", ".join(dept["variations"][:3])  # Show first 3 variations
        if len(dept["variations"]) > 3:
            variations += f" (+{len(dept['variations']) - 3} more)"
        
        table.add_row(
            dept["name"],
            dept["category"],
            variations
        )
    
    console.print(table)

async def show_database_stats():
    """Show database statistics."""
    db = UniversityDatabase()
    await db.initialize(use_api=False)  # Use backup data for quick testing
    
    console.print(Panel("[bold green]University Database Statistics[/bold green]"))
    
    # University stats
    uni_stats = Table(title="Universities", show_header=True, header_style="bold cyan")
    uni_stats.add_column("Metric", style="yellow")
    uni_stats.add_column("Count", style="green")
    
    total_unis = len(db.universities)
    states = db.get_states()
    public_unis = len([u for u in db.universities if u.type == "public"])
    private_unis = len([u for u in db.universities if u.type.startswith("private")])
    
    uni_stats.add_row("Total Universities", str(total_unis))
    uni_stats.add_row("States Covered", str(len(states)))
    uni_stats.add_row("Public Universities", str(public_unis))
    uni_stats.add_row("Private Universities", str(private_unis))
    
    # Department stats
    dept_stats = Table(title="Departments", show_header=True, header_style="bold cyan")
    dept_stats.add_column("Category", style="yellow")
    dept_stats.add_column("Departments", style="green")
    
    categories = db.get_department_categories()
    for category in categories:
        depts = db.get_departments_by_category(category)
        dept_stats.add_row(category, str(len(depts)))
    
    dept_stats.add_row("[bold]Total", f"[bold]{len(db.departments)}")
    
    console.print(Columns([uni_stats, dept_stats]))

async def interactive_search():
    """Interactive search mode."""
    console.print(Panel("[bold green]Interactive University & Department Search[/bold green]"))
    console.print("Type 'exit' to quit, 'stats' for database statistics")
    
    while True:
        console.print()
        choice = console.input("[bold cyan]Search (u)niversities or (d)epartments? [u/d/stats/exit]: [/bold cyan]").lower().strip()
        
        if choice in ['exit', 'quit', 'q']:
            break
        elif choice == 'stats':
            await show_database_stats()
            continue
        elif choice in ['u', 'university', 'universities']:
            query = console.input("[yellow]Enter university search query: [/yellow]").strip()
            if query:
                await test_university_search(query)
        elif choice in ['d', 'department', 'departments']:
            query = console.input("[yellow]Enter department search query (or press Enter for all): [/yellow]").strip()
            await test_department_search(query)
        else:
            console.print("[red]Invalid choice. Please enter u, d, stats, or exit.[/red]")

async def main():
    parser = argparse.ArgumentParser(description="Test University Database")
    parser.add_argument("--university", "-u", help="Search for universities")
    parser.add_argument("--department", "-d", help="Search for departments")
    parser.add_argument("--stats", action="store_true", help="Show database statistics")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--limit", type=int, default=10, help="Limit number of results")
    
    args = parser.parse_args()
    
    if args.interactive:
        await interactive_search()
    elif args.stats:
        await show_database_stats()
    elif args.university:
        await test_university_search(args.university, args.limit)
    elif args.department:
        await test_department_search(args.department, args.limit)
    else:
        console.print("[yellow]No action specified. Use --help for options or --interactive for interactive mode.[/yellow]")
        await show_database_stats()

if __name__ == "__main__":
    asyncio.run(main()) 