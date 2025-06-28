#!/usr/bin/env python3
"""
Comprehensive System Validation Suite for Lynnapse

This suite validates that the Lynnapse system is:
1. Scraping everything nicely
2. Storing data correctly and in a well-organized way  
3. Capturing all expected data we expect to be able to capture
4. Working on a variety of different university sites
"""

import asyncio
import json
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

# Rich terminal output
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn
from rich.panel import Panel

# Import Lynnapse components
sys.path.append('.')
from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler

console = Console()

@dataclass
class ValidationResult:
    """Validation result for a university."""
    university: str
    department: str
    extraction_success: bool = False
    faculty_count: int = 0
    extraction_time_seconds: float = 0.0
    data_quality_score: float = 0.0
    field_coverage: Dict[str, float] = None
    error_message: Optional[str] = None

class SystemValidationSuite:
    """Comprehensive system validation suite."""
    
    def __init__(self, quick_mode: bool = False):
        self.console = console
        self.quick_mode = quick_mode
        self.results: List[ValidationResult] = []
        
        # Test universities
        self.test_universities = [
            {"name": "Carnegie Mellon University", "department": "Psychology"},
            {"name": "University of Arizona", "department": "Psychology"},
            {"name": "University of Vermont", "department": "Psychology"},
            {"name": "Stanford University", "department": "Psychology"},
        ]
    
    async def run_validation_suite(self):
        """Run the complete validation suite."""
        self.console.print(Panel.fit(
            "🧪 [bold blue]Lynnapse System Validation Suite[/bold blue]\n\n"
            "Testing comprehensive system functionality",
            title="🚀 System Validation"
        ))
        
        await self._run_extraction_tests()
        await self._analyze_results()
        await self._generate_report()
    
    async def _run_extraction_tests(self):
        """Run extraction tests on universities."""
        self.console.print(f"\n�� Testing {len(self.test_universities)} universities...")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            task = progress.add_task("Testing universities...", total=len(self.test_universities))
            
            for university_config in self.test_universities:
                university_name = university_config["name"] 
                department = university_config["department"]
                
                progress.update(task, description=f"Testing {university_name}")
                
                result = await self._test_university(university_name, department)
                self.results.append(result)
                
                status = "✅" if result.extraction_success else "❌"
                self.console.print(f"   {status} {university_name}: {result.faculty_count} faculty")
                
                progress.advance(task)
    
    async def _test_university(self, university_name: str, department: str) -> ValidationResult:
        """Test extraction for a single university."""
        result = ValidationResult(university=university_name, department=department)
        
        try:
            start_time = datetime.now()
            
            crawler = AdaptiveFacultyCrawler(
                enable_lab_discovery=True,
                enable_external_search=False
            )
            
            extraction_result = await crawler.scrape_university_faculty(
                university_name=university_name,
                department_filter=department,
                max_faculty=50
            )
            
            await crawler.close()
            
            # Process results
            faculty_list = extraction_result.get("faculty", [])
            result.extraction_success = extraction_result.get("success", False)
            result.faculty_count = len(faculty_list)
            result.extraction_time_seconds = (datetime.now() - start_time).total_seconds()
            
            # Calculate data quality
            if faculty_list:
                result.data_quality_score = self._calculate_quality(faculty_list)
                result.field_coverage = self._calculate_coverage(faculty_list)
            
        except Exception as e:
            result.error_message = str(e)
            
        return result
    
    def _calculate_quality(self, faculty_list: List[Dict]) -> float:
        """Calculate data quality score."""
        if not faculty_list:
            return 0.0
        
        total = len(faculty_list)
        name_complete = sum(1 for f in faculty_list if f.get("name")) / total
        email_complete = sum(1 for f in faculty_list if f.get("email")) / total
        title_complete = sum(1 for f in faculty_list if f.get("title")) / total
        
        return (name_complete + email_complete + title_complete) / 3
    
    def _calculate_coverage(self, faculty_list: List[Dict]) -> Dict[str, float]:
        """Calculate field coverage."""
        if not faculty_list:
            return {}
        
        total = len(faculty_list)
        fields = ["name", "title", "email", "profile_url", "research_interests", "personal_website"]
        
        coverage = {}
        for field in fields:
            count = sum(1 for f in faculty_list if f.get(field))
            coverage[field] = (count / total) * 100
        
        return coverage
    
    async def _analyze_results(self):
        """Analyze validation results."""
        self.console.print(f"\n📊 [bold blue]Analysis Results[/bold blue]")
        
        successful = [r for r in self.results if r.extraction_success]
        failed = [r for r in self.results if not r.extraction_success]
        
        total_tests = len(self.results)
        success_rate = len(successful) / total_tests * 100 if total_tests > 0 else 0
        total_faculty = sum(r.faculty_count for r in successful)
        
        # Create analysis table
        table = Table(title="System Performance")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Universities Tested", str(total_tests))
        table.add_row("Success Rate", f"{success_rate:.1f}%")
        table.add_row("Total Faculty Extracted", str(total_faculty))
        
        if successful:
            avg_quality = sum(r.data_quality_score for r in successful) / len(successful)
            table.add_row("Average Data Quality", f"{avg_quality:.2f}")
        
        self.console.print(table)
    
    async def _generate_report(self):
        """Generate final report."""
        self.console.print(f"\n📋 [bold blue]Detailed Results[/bold blue]")
        
        results_table = Table(title="University Test Results")
        results_table.add_column("University", style="cyan")
        results_table.add_column("Status", style="green")
        results_table.add_column("Faculty", style="yellow")
        results_table.add_column("Quality", style="magenta")
        
        for result in self.results:
            status = "✅ Success" if result.extraction_success else "❌ Failed"
            quality_str = f"{result.data_quality_score:.2f}" if result.extraction_success else "N/A"
            
            results_table.add_row(
                result.university,
                status,
                str(result.faculty_count),
                quality_str
            )
        
        self.console.print(results_table)
        
        # Save results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"validation_results_{timestamp}.json"
        
        results_data = {
            "timestamp": timestamp,
            "results": [
                {
                    "university": r.university,
                    "department": r.department,
                    "success": r.extraction_success,
                    "faculty_count": r.faculty_count,
                    "quality_score": r.data_quality_score,
                    "field_coverage": r.field_coverage,
                    "error": r.error_message
                }
                for r in self.results
            ]
        }
        
        with open(filename, 'w') as f:
            json.dump(results_data, f, indent=2)
        
        self.console.print(f"\n�� Results saved to: {filename}")
        self.console.print("\n✅ [bold green]Validation completed![/bold green]")

async def main():
    """Run the validation suite."""
    suite = SystemValidationSuite()
    await suite.run_validation_suite()

if __name__ == "__main__":
    asyncio.run(main())
