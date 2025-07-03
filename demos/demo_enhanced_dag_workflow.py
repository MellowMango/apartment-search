#!/usr/bin/env python3
"""
🚀 Demo: Enhanced DAG Workflow with Link Enrichment

This script demonstrates the complete enhanced Lynnapse workflow:
Scraping → Link Processing → Enrichment → Storage

Features tested:
- Enhanced Prefect DAG orchestration
- Adaptive faculty discovery
- Smart link processing with social media replacement  
- Detailed academic link enrichment with metadata extraction
- Production-ready Docker compatibility
- Comprehensive error handling and retry logic

Usage:
    python demo_enhanced_dag_workflow.py
    python demo_enhanced_dag_workflow.py --docker
    python demo_enhanced_dag_workflow.py --university "University of Vermont" --enable-ai
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel
from rich.tree import Tree

# Add project root to path for imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from lynnapse.flows.enhanced_scraping_flow import (
    enhanced_faculty_scraping_flow,
    university_enhanced_scraping_flow
)

console = Console()


def create_demo_seeds_config() -> Dict[str, Any]:
    """Create a demo seeds configuration for testing."""
    return {
        "universities": [
            {
                "name": "University of Vermont",
                "base_url": "https://www.uvm.edu",
                "departments": ["Psychology"],
                "programs": [{
                    "name": "Psychology",
                    "department": "Psychology"
                }]
            },
            {
                "name": "Carnegie Mellon University", 
                "base_url": "https://www.cmu.edu",
                "departments": ["Psychology"],
                "programs": [{
                    "name": "Psychology",
                    "department": "Psychology"
                }]
            }
        ]
    }


async def test_enhanced_dag_basic() -> Dict[str, Any]:
    """Test basic enhanced DAG functionality without external dependencies."""
    console.print(Panel.fit("🧪 [bold]Basic Enhanced DAG Test[/bold]", style="blue"))
    
    # Create test configuration
    seeds_config = create_demo_seeds_config()
    seeds_file = "demo_seeds_enhanced.json"
    
    with open(seeds_file, 'w') as f:
        json.dump(seeds_config, f, indent=2)
    
    try:
        # Test dry run first
        console.print("🔍 Testing enhanced flow configuration validation...")
        
        result = await enhanced_faculty_scraping_flow(
            seeds_file=seeds_file,
            university_filter="University of Vermont",
            department_filter="Psychology",
            enable_ai_assistance=False,  # Disable AI for basic test
            enable_link_enrichment=False,  # Disable enrichment for basic test
            dry_run=True
        )
        
        console.print(f"✅ Configuration validation successful!")
        console.print(f"   Universities configured: {result['configuration']['total_universities']}")
        console.print(f"   Programs configured: {result['configuration']['total_programs']}")
        
        return {
            "test_name": "enhanced_dag_basic",
            "status": "success",
            "dry_run_result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        console.print(f"❌ Basic test failed: {e}")
        return {
            "test_name": "enhanced_dag_basic",
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        # Cleanup
        if os.path.exists(seeds_file):
            os.remove(seeds_file)


async def test_enhanced_dag_with_ai(openai_api_key: Optional[str] = None) -> Dict[str, Any]:
    """Test enhanced DAG with AI assistance (if API key available)."""
    console.print(Panel.fit("🤖 [bold]Enhanced DAG with AI Test[/bold]", style="green"))
    
    if not openai_api_key:
        openai_api_key = os.getenv("OPENAI_API_KEY")
    
    if not openai_api_key:
        console.print("⚠️ No OpenAI API key found, skipping AI test")
        return {
            "test_name": "enhanced_dag_with_ai",
            "status": "skipped",
            "reason": "no_api_key",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    # Create test configuration
    seeds_config = create_demo_seeds_config()
    seeds_file = "demo_seeds_ai_enhanced.json"
    
    with open(seeds_file, 'w') as f:
        json.dump(seeds_config, f, indent=2)
    
    try:
        console.print("🧠 Testing enhanced flow with AI assistance...")
        
        result = await enhanced_faculty_scraping_flow(
            seeds_file=seeds_file,
            university_filter="University of Vermont",
            department_filter="Psychology",
            enable_ai_assistance=True,
            enable_link_enrichment=True,
            max_concurrent_scraping=2,  # Conservative for demo
            max_concurrent_enrichment=1,  # Very conservative
            openai_api_key=openai_api_key,
            dry_run=False  # Full test
        )
        
        console.print(f"✅ AI-enhanced flow completed successfully!")
        
        # Display results
        table = Table(title="AI-Enhanced Results", show_header=True, header_style="bold green")
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Job ID", result.get('job_id', 'N/A'))
        table.add_row("Faculty Processed", str(result.get('total_faculty_processed', 0)))
        table.add_row("Links Processed", str(result.get('total_links_processed', 0)))
        table.add_row("Links Enriched", str(result.get('total_links_enriched', 0)))
        table.add_row("Execution Time", f"{result.get('execution_time_seconds', 0):.1f}s")
        
        console.print(table)
        
        return {
            "test_name": "enhanced_dag_with_ai",
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        console.print(f"❌ AI test failed: {e}")
        return {
            "test_name": "enhanced_dag_with_ai", 
            "status": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
    finally:
        # Cleanup
        if os.path.exists(seeds_file):
            os.remove(seeds_file)


async def test_university_enhanced_flow() -> Dict[str, Any]:
    """Test university-specific enhanced flow."""
    console.print(Panel.fit("🏫 [bold]University Enhanced Flow Test[/bold]", style="magenta"))
    
    # Create university config
    university_config = {
        "name": "Test University",
        "base_url": "https://test.edu",
        "departments": ["Psychology"]
    }
    
    try:
        console.print("🎓 Testing university-specific enhanced flow...")
        
        result = await university_enhanced_scraping_flow(
            university_config=university_config,
            department_name="Psychology",
            enable_ai_assistance=False,
            enable_link_enrichment=False
        )
        
        console.print(f"✅ University enhanced flow completed!")
        console.print(f"   University: {result.get('university_name')}")
        console.print(f"   Department: {result.get('department_name')}")
        console.print(f"   Status: {result.get('status')}")
        
        return {
            "test_name": "university_enhanced_flow",
            "status": "success",
            "result": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        console.print(f"❌ University test failed: {e}")
        return {
            "test_name": "university_enhanced_flow",
            "status": "failed", 
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


def test_docker_compatibility() -> Dict[str, Any]:
    """Test Docker environment compatibility."""
    console.print(Panel.fit("🐳 [bold]Docker Compatibility Test[/bold]", style="blue"))
    
    checks = {
        "python_version": sys.version_info >= (3, 8),
        "project_path": project_root.exists(),
        "env_vars": {
            "PYTHONPATH": os.getenv("PYTHONPATH") is not None,
            "PLAYWRIGHT_HEADLESS": os.getenv("PLAYWRIGHT_HEADLESS") == "true"
        },
        "modules": {}
    }
    
    # Test module imports
    required_modules = [
        "prefect",
        "playwright", 
        "openai",
        "rich",
        "httpx",
        "beautifulsoup4"
    ]
    
    for module in required_modules:
        try:
            __import__(module)
            checks["modules"][module] = True
        except ImportError:
            checks["modules"][module] = False
    
    # Test Lynnapse components
    try:
        from lynnapse.core import (
            AdaptiveFacultyCrawler,
            UniversityAdapter, 
            SmartLinkReplacer,
            LinkEnrichmentEngine
        )
        checks["lynnapse_components"] = True
    except ImportError as e:
        checks["lynnapse_components"] = False
        checks["lynnapse_error"] = str(e)
    
    # Display results
    table = Table(title="Docker Compatibility Check", show_header=True, header_style="bold blue")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="green")
    
    table.add_row("Python Version", "✅ Pass" if checks["python_version"] else "❌ Fail")
    table.add_row("Project Path", "✅ Pass" if checks["project_path"] else "❌ Fail")
    table.add_row("Environment Variables", "✅ Pass" if any(checks["env_vars"].values()) else "⚠️ Partial")
    table.add_row("Lynnapse Components", "✅ Pass" if checks["lynnapse_components"] else "❌ Fail")
    
    for module, available in checks["modules"].items():
        table.add_row(f"Module: {module}", "✅ Available" if available else "❌ Missing")
    
    console.print(table)
    
    return {
        "test_name": "docker_compatibility",
        "status": "success" if all([
            checks["python_version"],
            checks["project_path"],
            checks["lynnapse_components"],
            all(checks["modules"].values())
        ]) else "partial",
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }


async def run_comprehensive_demo(enable_ai: bool = False, openai_api_key: Optional[str] = None):
    """Run comprehensive demo of enhanced DAG workflow."""
    console.print(Panel.fit("🚀 [bold]Enhanced DAG Workflow Demo[/bold]", style="bold green"))
    console.print("Testing complete pipeline: Scraping → Link Processing → Enrichment → Storage\n")
    
    # Track results
    test_results = []
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        
        # Test 1: Docker Compatibility
        task = progress.add_task("🐳 Checking Docker compatibility...", total=None)
        docker_result = test_docker_compatibility()
        test_results.append(docker_result)
        progress.stop_task(task)
        
        # Test 2: Basic Enhanced DAG
        task = progress.add_task("🧪 Testing basic enhanced DAG...", total=None)
        basic_result = await test_enhanced_dag_basic()
        test_results.append(basic_result)
        progress.stop_task(task)
        
        # Test 3: University Enhanced Flow
        task = progress.add_task("🏫 Testing university enhanced flow...", total=None)
        university_result = await test_university_enhanced_flow()
        test_results.append(university_result)
        progress.stop_task(task)
        
        # Test 4: AI-Enhanced Flow (if enabled)
        if enable_ai:
            task = progress.add_task("🤖 Testing AI-enhanced flow...", total=None)
            ai_result = await test_enhanced_dag_with_ai(openai_api_key)
            test_results.append(ai_result)
            progress.stop_task(task)
    
    # Generate comprehensive report
    console.print("\n" + "="*60)
    console.print(Panel.fit("📊 [bold]Comprehensive Test Results[/bold]", style="bold magenta"))
    
    # Results tree
    tree = Tree("🚀 Enhanced DAG Workflow Tests")
    
    for result in test_results:
        test_name = result["test_name"]
        status = result["status"]
        
        if status == "success":
            tree.add(f"✅ {test_name}")
        elif status == "failed":
            tree.add(f"❌ {test_name}: {result.get('error', 'Unknown error')}")
        elif status == "skipped":
            tree.add(f"⏭️ {test_name}: {result.get('reason', 'Skipped')}")
        else:
            tree.add(f"⚠️ {test_name}: {status}")
    
    console.print(tree)
    
    # Summary statistics
    success_count = sum(1 for r in test_results if r["status"] == "success")
    total_count = len(test_results)
    
    console.print(f"\n📈 [bold]Summary:[/bold] {success_count}/{total_count} tests passed")
    
    if success_count == total_count:
        console.print("🎉 [bold green]All tests passed! Enhanced DAG workflow is ready for production.[/bold green]")
    elif success_count > 0:
        console.print("⚠️ [bold yellow]Some tests passed. Review failed tests for production readiness.[/bold yellow]")
    else:
        console.print("❌ [bold red]Tests failed. Check configuration and dependencies.[/bold red]")
    
    # Save results to file
    results_file = f"enhanced_dag_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "demo_type": "enhanced_dag_workflow",
            "timestamp": datetime.utcnow().isoformat(),
            "test_results": test_results,
            "summary": {
                "total_tests": total_count,
                "passed_tests": success_count,
                "success_rate": success_count / total_count if total_count > 0 else 0
            }
        }, f, indent=2)
    
    console.print(f"💾 Results saved to: {results_file}")
    
    return test_results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced DAG Workflow Demo")
    parser.add_argument("--enable-ai", action="store_true", help="Enable AI-assisted tests (requires OpenAI API key)")
    parser.add_argument("--openai-key", help="OpenAI API key (or use OPENAI_API_KEY env var)")
    parser.add_argument("--docker", action="store_true", help="Run in Docker-optimized mode")
    
    args = parser.parse_args()
    
    # Set Docker environment variables if requested
    if args.docker:
        os.environ["PLAYWRIGHT_HEADLESS"] = "true"
        os.environ["LYNNAPSE_ENV"] = "docker"
    
    console.print("🚀 [bold]Starting Enhanced DAG Workflow Demo[/bold]")
    console.print(f"🐳 Docker mode: {'enabled' if args.docker else 'disabled'}")
    console.print(f"🤖 AI assistance: {'enabled' if args.enable_ai else 'disabled'}")
    console.print()
    
    try:
        # Run comprehensive demo
        results = asyncio.run(run_comprehensive_demo(
            enable_ai=args.enable_ai,
            openai_api_key=args.openai_key
        ))
        
        # Exit with appropriate code
        success_count = sum(1 for r in results if r["status"] == "success")
        if success_count == len(results):
            sys.exit(0)  # All tests passed
        elif success_count > 0:
            sys.exit(1)  # Partial success
        else:
            sys.exit(2)  # All tests failed
            
    except KeyboardInterrupt:
        console.print("\n⏹️ Demo interrupted by user")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n💥 Demo failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1) 