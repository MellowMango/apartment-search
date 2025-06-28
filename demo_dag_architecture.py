#!/usr/bin/env python3
"""
🚀 Demo: Enhanced DAG Architecture Overview

This script demonstrates the enhanced Lynnapse DAG architecture and workflow
without requiring complex external dependencies. It showcases the structure,
task dependencies, and integration points of the enhanced system.

Features demonstrated:
- DAG task structure and dependencies
- Error handling and retry logic patterns
- Enhanced link enrichment integration
- Docker deployment readiness
- Configuration management

Usage:
    python demo_dag_architecture.py
    python demo_dag_architecture.py --show-config
    python demo_dag_architecture.py --docker-info
"""

import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class DAGTaskNode:
    """Represents a task node in the DAG architecture."""
    
    def __init__(self, name: str, description: str, dependencies: List[str] = None, 
                 retry_count: int = 3, timeout: int = 300):
        self.name = name
        self.description = description
        self.dependencies = dependencies or []
        self.retry_count = retry_count
        self.timeout = timeout
        self.status = "pending"
        self.execution_time = 0.0
    
    def execute_simulation(self) -> Dict[str, Any]:
        """Simulate task execution."""
        import time
        import random
        
        # Simulate execution time
        execution_time = random.uniform(0.5, 2.0)
        time.sleep(execution_time)
        
        # Simulate occasional failures for retry demonstration
        if random.random() < 0.15:  # 15% failure rate
            self.status = "failed"
            return {
                "status": "failed",
                "error": f"Simulated failure in {self.name}",
                "execution_time": execution_time
            }
        
        self.status = "completed"
        self.execution_time = execution_time
        return {
            "status": "completed",
            "execution_time": execution_time,
            "output": f"Task {self.name} completed successfully"
        }


class EnhancedDAGWorkflow:
    """Enhanced DAG workflow orchestrator."""
    
    def __init__(self):
        self.tasks = self._create_dag_structure()
        self.execution_history = []
        
    def _create_dag_structure(self) -> Dict[str, DAGTaskNode]:
        """Create the enhanced DAG structure with task dependencies."""
        
        return {
            # Stage 1: Configuration & Setup
            "load_seeds": DAGTaskNode(
                "Load Seeds Configuration",
                "Load and validate university seeds configuration",
                dependencies=[],
                retry_count=3,
                timeout=30
            ),
            
            "create_job": DAGTaskNode(
                "Create Scraping Job",
                "Initialize job tracking and monitoring",
                dependencies=["load_seeds"],
                retry_count=3,
                timeout=60
            ),
            
            # Stage 2: Enhanced Faculty Scraping
            "scrape_faculty": DAGTaskNode(
                "Enhanced Faculty Scraping",
                "Scrape faculty using adaptive crawlers with university structure detection",
                dependencies=["create_job"],
                retry_count=3,
                timeout=300
            ),
            
            # Stage 3: Smart Link Processing
            "process_links": DAGTaskNode(
                "Smart Link Processing",
                "Process and replace social media links with academic equivalents",
                dependencies=["scrape_faculty"],
                retry_count=2,
                timeout=180
            ),
            
            # Stage 4: Advanced Link Enrichment
            "enrich_links": DAGTaskNode(
                "Advanced Link Enrichment",
                "Extract detailed metadata from academic links (Scholar, lab sites, profiles)",
                dependencies=["process_links"],
                retry_count=2,
                timeout=240
            ),
            
            # Stage 5: Data Storage & Quality Assessment
            "store_data": DAGTaskNode(
                "Store Enhanced Data",
                "Store enriched faculty data with quality metrics and metadata",
                dependencies=["enrich_links"],
                retry_count=3,
                timeout=120
            ),
            
            # Stage 6: Cleanup & Reporting
            "cleanup": DAGTaskNode(
                "Cleanup & Finalize",
                "Clean up resources and generate comprehensive reports",
                dependencies=["store_data"],
                retry_count=1,
                timeout=60
            )
        }
    
    def visualize_dag(self) -> Tree:
        """Create a visual representation of the DAG structure."""
        tree = Tree("🚀 [bold]Enhanced Lynnapse DAG Workflow[/bold]")
        
        # Create a mapping of tasks to their tree nodes
        task_nodes = {}
        
        # Add tasks in dependency order
        def add_task_to_tree(task_name: str, parent_tree: Tree = None):
            if task_name in task_nodes:
                return task_nodes[task_name]
            
            task = self.tasks[task_name]
            
            # Create visual representation based on status
            status_icon = {
                "pending": "⏳",
                "running": "🔄", 
                "completed": "✅",
                "failed": "❌"
            }.get(task.status, "⏳")
            
            task_display = f"{status_icon} {task.name}"
            if task.execution_time > 0:
                task_display += f" ({task.execution_time:.1f}s)"
            
            # Add to appropriate parent
            if parent_tree is None:
                tree_node = tree.add(task_display)
            else:
                tree_node = parent_tree.add(task_display)
            
            task_nodes[task_name] = tree_node
            
            # Add description
            tree_node.add(f"📝 {task.description}")
            tree_node.add(f"🔄 Retries: {task.retry_count} | ⏱️ Timeout: {task.timeout}s")
            
            return tree_node
        
        # Build tree following dependency order
        processed = set()
        
        def process_task(task_name: str):
            if task_name in processed:
                return
            
            task = self.tasks[task_name]
            
            # Process dependencies first
            for dep in task.dependencies:
                process_task(dep)
            
            # Find appropriate parent
            if not task.dependencies:
                add_task_to_tree(task_name, tree)
            else:
                # Add to the last dependency (simplified for visualization)
                parent_task = task.dependencies[-1]
                parent_node = task_nodes.get(parent_task)
                add_task_to_tree(task_name, parent_node if parent_node else tree)
            
            processed.add(task_name)
        
        # Process all tasks
        for task_name in self.tasks:
            process_task(task_name)
        
        return tree
    
    def get_execution_order(self) -> List[str]:
        """Get the correct execution order based on dependencies."""
        order = []
        processed = set()
        
        def add_task(task_name: str):
            if task_name in processed:
                return
            
            task = self.tasks[task_name]
            
            # Add dependencies first
            for dep in task.dependencies:
                add_task(dep)
            
            # Add this task
            order.append(task_name)
            processed.add(task_name)
        
        # Process all tasks
        for task_name in self.tasks:
            add_task(task_name)
        
        return order
    
    def simulate_execution(self, show_progress: bool = True) -> Dict[str, Any]:
        """Simulate the execution of the entire DAG workflow."""
        execution_order = self.get_execution_order()
        results = {}
        
        total_start_time = datetime.now()
        
        if show_progress:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                
                for task_name in execution_order:
                    task = self.tasks[task_name]
                    
                    progress_task = progress.add_task(f"🔄 Executing: {task.name}...", total=None)
                    
                    # Simulate retries
                    for attempt in range(task.retry_count):
                        task.status = "running"
                        result = task.execute_simulation()
                        
                        if result["status"] == "completed":
                            results[task_name] = result
                            break
                        elif attempt == task.retry_count - 1:
                            # Final failure
                            results[task_name] = result
                            console.print(f"❌ Task {task.name} failed after {task.retry_count} attempts")
                            break
                        else:
                            console.print(f"⚠️ Task {task.name} failed, retrying... (attempt {attempt + 1})")
                    
                    progress.stop_task(progress_task)
        else:
            # Execute without progress display
            for task_name in execution_order:
                task = self.tasks[task_name]
                result = task.execute_simulation()
                results[task_name] = result
        
        total_execution_time = (datetime.now() - total_start_time).total_seconds()
        
        return {
            "execution_order": execution_order,
            "task_results": results,
            "total_execution_time": total_execution_time,
            "success_rate": len([r for r in results.values() if r["status"] == "completed"]) / len(results),
            "timestamp": datetime.utcnow().isoformat()
        }


def show_dag_configuration():
    """Display the DAG configuration and structure."""
    console.print(Panel.fit("⚙️ [bold]Enhanced DAG Configuration[/bold]", style="blue"))
    
    workflow = EnhancedDAGWorkflow()
    
    # Show task configuration
    table = Table(title="DAG Task Configuration", show_header=True, header_style="bold cyan")
    table.add_column("Task", style="cyan", no_wrap=True)
    table.add_column("Dependencies", style="yellow")
    table.add_column("Retries", style="green", justify="center")
    table.add_column("Timeout", style="red", justify="center")
    table.add_column("Description", style="white")
    
    execution_order = workflow.get_execution_order()
    for task_name in execution_order:
        task = workflow.tasks[task_name]
        deps = ", ".join(task.dependencies) if task.dependencies else "None"
        table.add_row(
            task.name,
            deps,
            str(task.retry_count),
            f"{task.timeout}s",
            task.description
        )
    
    console.print(table)
    
    # Show DAG visualization
    console.print("\n")
    console.print(Panel.fit("🌳 [bold]DAG Structure Visualization[/bold]", style="green"))
    dag_tree = workflow.visualize_dag()
    console.print(dag_tree)
    
    return workflow


def show_docker_deployment_info():
    """Show Docker deployment information."""
    console.print(Panel.fit("🐳 [bold]Docker Deployment Information[/bold]", style="blue"))
    
    # Docker configuration
    docker_info = {
        "base_image": "python:3.11-slim",
        "dependencies": [
            "prefect>=2.0.0",
            "playwright>=1.40.0", 
            "openai>=1.0.0",
            "httpx>=0.24.0",
            "beautifulsoup4>=4.12.0",
            "pymongo>=4.0.0",
            "rich>=13.0.0"
        ],
        "environment_variables": [
            "MONGODB_URL",
            "OPENAI_API_KEY",
            "PLAYWRIGHT_HEADLESS=true",
            "LYNNAPSE_ENV=docker"
        ],
        "volumes": [
            "./output:/app/output",
            "./logs:/app/logs",
            "./seeds:/app/seeds"
        ],
        "networks": [
            "lynnapse-network"
        ]
    }
    
    # Dependencies table
    deps_table = Table(title="Docker Dependencies", show_header=True, header_style="bold cyan")
    deps_table.add_column("Package", style="cyan")
    deps_table.add_column("Version", style="green")
    
    for dep in docker_info["dependencies"]:
        pkg, ver = dep.split(">=")
        deps_table.add_row(pkg, f">= {ver}")
    
    console.print(deps_table)
    
    # Environment variables table
    env_table = Table(title="Environment Variables", show_header=True, header_style="bold yellow")
    env_table.add_column("Variable", style="yellow")
    env_table.add_column("Description", style="white")
    
    env_descriptions = {
        "MONGODB_URL": "MongoDB connection string for data storage",
        "OPENAI_API_KEY": "OpenAI API key for AI-assisted processing",
        "PLAYWRIGHT_HEADLESS": "Run browser in headless mode (true for Docker)",
        "LYNNAPSE_ENV": "Environment setting (docker/development/production)"
    }
    
    for env_var in docker_info["environment_variables"]:
        var_name = env_var.split("=")[0]
        description = env_descriptions.get(var_name, "Configuration variable")
        env_table.add_row(env_var, description)
    
    console.print(env_table)
    
    # Docker commands
    console.print("\n📋 [bold]Docker Commands:[/bold]")
    console.print("```bash")
    console.print("# Build the enhanced DAG image")
    console.print("docker build -t lynnapse:enhanced-dag .")
    console.print("")
    console.print("# Run enhanced DAG workflow")
    console.print("docker run --rm \\")
    console.print("  --network lynnapse-network \\")
    console.print("  -e MONGODB_URL=mongodb://admin:password@mongodb:27017/lynnapse \\")
    console.print("  -e PLAYWRIGHT_HEADLESS=true \\")
    console.print("  -v $(pwd)/output:/app/output \\")
    console.print("  lynnapse:enhanced-dag \\")
    console.print("  python demo_enhanced_dag_workflow.py --docker")
    console.print("")
    console.print("# Run with docker-compose")
    console.print("./docker_demo_enhanced_dag.sh")
    console.print("```")
    
    return docker_info


def run_dag_demo():
    """Run the complete DAG demo."""
    console.print(Panel.fit("🚀 [bold]Enhanced DAG Workflow Demo[/bold]", style="bold green"))
    console.print("Simulating complete pipeline: Scraping → Link Processing → Enrichment → Storage\n")
    
    # Create and show DAG structure
    workflow = EnhancedDAGWorkflow()
    
    console.print("📊 [bold]DAG Structure:[/bold]")
    dag_tree = workflow.visualize_dag()
    console.print(dag_tree)
    console.print()
    
    # Simulate execution
    console.print("🎬 [bold]Simulating DAG Execution:[/bold]")
    results = workflow.simulate_execution()
    
    # Show results
    console.print("\n" + "="*60)
    console.print(Panel.fit("📊 [bold]Execution Results[/bold]", style="bold magenta"))
    
    # Results table
    results_table = Table(title="Task Execution Results", show_header=True, header_style="bold green")
    results_table.add_column("Task", style="cyan")
    results_table.add_column("Status", style="green")
    results_table.add_column("Execution Time", style="yellow", justify="right")
    results_table.add_column("Notes", style="white")
    
    for task_name in results["execution_order"]:
        task_result = results["task_results"][task_name]
        task = workflow.tasks[task_name]
        
        status_display = "✅ Success" if task_result["status"] == "completed" else "❌ Failed"
        execution_time = f"{task_result['execution_time']:.1f}s"
        notes = task_result.get("error", "Completed successfully")
        
        results_table.add_row(task.name, status_display, execution_time, notes)
    
    console.print(results_table)
    
    # Summary statistics
    console.print(f"\n📈 [bold]Summary:[/bold]")
    console.print(f"   Total Execution Time: {results['total_execution_time']:.1f}s")
    console.print(f"   Success Rate: {results['success_rate']:.1%}")
    console.print(f"   Tasks Completed: {len([r for r in results['task_results'].values() if r['status'] == 'completed'])}")
    console.print(f"   Tasks Failed: {len([r for r in results['task_results'].values() if r['status'] == 'failed'])}")
    
    if results['success_rate'] == 1.0:
        console.print("🎉 [bold green]All tasks completed successfully![/bold green]")
    elif results['success_rate'] > 0.8:
        console.print("⚠️ [bold yellow]Most tasks completed successfully. Check failed tasks.[/bold yellow]")
    else:
        console.print("❌ [bold red]Multiple task failures detected. Review configuration.[/bold red]")
    
    # Save results
    results_file = f"dag_demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump({
            "demo_type": "enhanced_dag_architecture",
            "timestamp": datetime.utcnow().isoformat(),
            "execution_results": results,
            "task_configuration": {
                name: {
                    "description": task.description,
                    "dependencies": task.dependencies,
                    "retry_count": task.retry_count,
                    "timeout": task.timeout
                }
                for name, task in workflow.tasks.items()
            }
        }, f, indent=2)
    
    console.print(f"\n💾 Demo results saved to: {results_file}")
    
    return results


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Enhanced DAG Architecture Demo")
    parser.add_argument("--show-config", action="store_true", help="Show DAG configuration and structure")
    parser.add_argument("--docker-info", action="store_true", help="Show Docker deployment information")
    parser.add_argument("--run-demo", action="store_true", help="Run complete DAG simulation demo")
    
    args = parser.parse_args()
    
    console.print("🚀 [bold]Enhanced DAG Architecture Demo[/bold]")
    console.print("Demonstrating Lynnapse enhanced workflow structure and capabilities\n")
    
    try:
        if args.show_config:
            show_dag_configuration()
        elif args.docker_info:
            show_docker_deployment_info()
        elif args.run_demo:
            run_dag_demo()
        else:
            # Run all demonstrations
            console.print("Running comprehensive demonstration...\n")
            
            # 1. Show configuration
            workflow = show_dag_configuration()
            console.print("\n" + "="*60 + "\n")
            
            # 2. Show Docker info
            docker_info = show_docker_deployment_info()
            console.print("\n" + "="*60 + "\n")
            
            # 3. Run demo
            results = run_dag_demo()
            
            console.print(f"\n🎉 [bold green]Enhanced DAG Architecture Demo completed![/bold green]")
            console.print("The enhanced workflow is ready for production deployment.")
        
    except KeyboardInterrupt:
        console.print("\n⏹️ Demo interrupted by user")
        sys.exit(130)
    except Exception as e:
        console.print(f"\n💥 Demo failed: {e}")
        import traceback
        console.print(traceback.format_exc())
        sys.exit(1) 