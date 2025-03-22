#!/usr/bin/env python3
"""
Geocoding Metrics Visualization

This script creates visualizations of geocoding quality metrics from the database.
It generates charts showing accuracy trends, failure types, and other relevant
metrics to help monitor and improve the geocoding system.
"""

import os
import sys
import json
import asyncio
import argparse
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import required modules
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps

def parse_iso_date(date_string: str) -> datetime:
    """Parse ISO format date string to datetime."""
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except ValueError:
        # Fall back to simpler parsing if the above fails
        return datetime.strptime(date_string.split('T')[0], '%Y-%m-%d')

async def fetch_geocoding_data(db_ops: EnrichmentDatabaseOps, 
                            days: int = 30) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Fetch geocoding validation and monitoring data from the database.
    
    Args:
        db_ops: Database operations object
        days: Number of days of data to fetch
        
    Returns:
        Tuple of (validation data, monitoring data)
    """
    start_date = datetime.now() - timedelta(days=days)
    
    # Fetch validation data
    validation_query = """
    SELECT 
        report_date,
        properties_count,
        passed_count,
        failed_count,
        success_rate,
        failure_types
    FROM geocoding_validation_reports
    WHERE report_date >= $1
    ORDER BY report_date
    """
    
    validation_results = await db_ops.execute_raw_query(validation_query, [start_date.isoformat()])
    
    # Fetch monitoring data
    monitoring_query = """
    SELECT 
        report_date,
        sample_size,
        accuracy,
        alert_triggered,
        alert_reasons,
        failure_types
    FROM geocoding_monitoring_reports
    WHERE report_date >= $1
    ORDER BY report_date
    """
    
    monitoring_results = await db_ops.execute_raw_query(monitoring_query, [start_date.isoformat()])
    
    # Process validation data
    validation_data = {
        "dates": [],
        "counts": {
            "total": [],
            "passed": [],
            "failed": []
        },
        "success_rates": [],
        "failure_types": {}
    }
    
    for row in validation_results:
        validation_data["dates"].append(row[0])
        validation_data["counts"]["total"].append(row[1])
        validation_data["counts"]["passed"].append(row[2])
        validation_data["counts"]["failed"].append(row[3])
        validation_data["success_rates"].append(float(row[4]))
        
        # Process failure types
        failure_types = row[5] if isinstance(row[5], dict) else json.loads(row[5])
        for failure_type, count in failure_types.items():
            if failure_type not in validation_data["failure_types"]:
                validation_data["failure_types"][failure_type] = []
                # Pad with zeros for previous dates
                validation_data["failure_types"][failure_type].extend([0] * (len(validation_data["dates"]) - 1))
            
            # Ensure all failure type lists have the same length
            while len(validation_data["failure_types"][failure_type]) < len(validation_data["dates"]) - 1:
                validation_data["failure_types"][failure_type].append(0)
                
            validation_data["failure_types"][failure_type].append(count)
    
    # Process monitoring data
    monitoring_data = {
        "dates": [],
        "sample_sizes": [],
        "accuracy_rates": [],
        "alerts": [],
        "alert_reasons": {},
        "failure_types": {}
    }
    
    for row in monitoring_results:
        monitoring_data["dates"].append(row[0])
        monitoring_data["sample_sizes"].append(row[1])
        monitoring_data["accuracy_rates"].append(float(row[2]))
        monitoring_data["alerts"].append(row[3])  # Boolean value
        
        # Process alert reasons
        alert_reasons = row[4] if isinstance(row[4], dict) else json.loads(row[4])
        for reason in alert_reasons:
            key = reason[:50] + "..." if len(reason) > 50 else reason  # Truncate long reasons
            if key not in monitoring_data["alert_reasons"]:
                monitoring_data["alert_reasons"][key] = 0
            monitoring_data["alert_reasons"][key] += 1
        
        # Process failure types
        failure_types = row[5] if isinstance(row[5], dict) else json.loads(row[5])
        for failure_type, count in failure_types.items():
            if failure_type not in monitoring_data["failure_types"]:
                monitoring_data["failure_types"][failure_type] = []
                # Pad with zeros for previous dates
                monitoring_data["failure_types"][failure_type].extend([0] * (len(monitoring_data["dates"]) - 1))
            
            # Ensure all failure type lists have the same length
            while len(monitoring_data["failure_types"][failure_type]) < len(monitoring_data["dates"]) - 1:
                monitoring_data["failure_types"][failure_type].append(0)
                
            monitoring_data["failure_types"][failure_type].append(count)
    
    return validation_data, monitoring_data

def plot_success_rate_trend(validation_data: Dict[str, Any], monitoring_data: Dict[str, Any], 
                          output_dir: str, filename: str = "success_rate_trend.png"):
    """
    Plot success rate trend over time.
    
    Args:
        validation_data: Validation data dictionary
        monitoring_data: Monitoring data dictionary
        output_dir: Directory to save the plot
        filename: Output filename
    """
    plt.figure(figsize=(12, 6))
    
    # Plot validation success rates if available
    if validation_data["dates"] and validation_data["success_rates"]:
        plt.plot(validation_data["dates"], validation_data["success_rates"], 
                marker='o', linestyle='-', label='Validation Success Rate')
    
    # Plot monitoring accuracy rates if available
    if monitoring_data["dates"] and monitoring_data["accuracy_rates"]:
        plt.plot(monitoring_data["dates"], monitoring_data["accuracy_rates"], 
                marker='x', linestyle='--', label='Monitoring Accuracy Rate')
    
    plt.title('Geocoding Success Rate Trend')
    plt.xlabel('Date')
    plt.ylabel('Success Rate (%)')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Format x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
    
    # Set y-axis to start from 0 and have a reasonable upper limit
    plt.ylim(bottom=min(50, min(validation_data["success_rates"] + [100]) - 10) if validation_data["success_rates"] else 50,
             top=100.5)
    
    # Add horizontal line at 90% for reference
    plt.axhline(y=90, color='r', linestyle=':', alpha=0.7, label='90% Threshold')
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

def plot_failure_types(validation_data: Dict[str, Any], output_dir: str, 
                     filename: str = "failure_types.png", top_n: int = 6):
    """
    Plot distribution of failure types.
    
    Args:
        validation_data: Validation data dictionary
        output_dir: Directory to save the plot
        filename: Output filename
        top_n: Number of top failure types to show
    """
    if not validation_data["failure_types"]:
        print("No failure type data available to plot")
        return
    
    # Aggregate failure counts
    failure_counts = {}
    for failure_type, counts in validation_data["failure_types"].items():
        failure_counts[failure_type] = sum(counts)
    
    # Sort and get top N
    top_failures = dict(sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)[:top_n])
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.bar(top_failures.keys(), top_failures.values())
    plt.title(f'Top {top_n} Geocoding Failure Types')
    plt.xlabel('Failure Type')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

def plot_alert_reasons(monitoring_data: Dict[str, Any], output_dir: str, 
                     filename: str = "alert_reasons.png"):
    """
    Plot distribution of alert reasons.
    
    Args:
        monitoring_data: Monitoring data dictionary
        output_dir: Directory to save the plot
        filename: Output filename
    """
    if not monitoring_data["alert_reasons"]:
        print("No alert reason data available to plot")
        return
    
    # Sort reasons by count
    sorted_reasons = dict(sorted(monitoring_data["alert_reasons"].items(), key=lambda x: x[1], reverse=True))
    
    # Create the plot
    plt.figure(figsize=(10, 6))
    plt.bar(sorted_reasons.keys(), sorted_reasons.values())
    plt.title('Geocoding Alert Reasons')
    plt.xlabel('Alert Reason')
    plt.ylabel('Count')
    plt.xticks(rotation=45, ha='right')
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

def plot_failure_types_over_time(validation_data: Dict[str, Any], output_dir: str, 
                               filename: str = "failure_trends.png", top_n: int = 5):
    """
    Plot trends of top failure types over time.
    
    Args:
        validation_data: Validation data dictionary
        output_dir: Directory to save the plot
        filename: Output filename
        top_n: Number of top failure types to show
    """
    if not validation_data["failure_types"] or not validation_data["dates"]:
        print("No failure trend data available to plot")
        return
    
    # Determine top N failure types by total count
    failure_totals = {ft: sum(counts) for ft, counts in validation_data["failure_types"].items()}
    top_failures = dict(sorted(failure_totals.items(), key=lambda x: x[1], reverse=True)[:top_n])
    
    # Create the plot
    plt.figure(figsize=(12, 6))
    
    for failure_type in top_failures.keys():
        # Ensure data lists are the same length
        counts = validation_data["failure_types"][failure_type]
        dates = validation_data["dates"][:len(counts)]
        
        plt.plot(dates, counts, marker='o', linestyle='-', label=failure_type)
    
    plt.title(f'Top {top_n} Failure Types Over Time')
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Format x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

def plot_validation_counts(validation_data: Dict[str, Any], output_dir: str, 
                         filename: str = "validation_counts.png"):
    """
    Plot counts of total, passed, and failed validations over time.
    
    Args:
        validation_data: Validation data dictionary
        output_dir: Directory to save the plot
        filename: Output filename
    """
    if not validation_data["dates"] or not validation_data["counts"]["total"]:
        print("No validation count data available to plot")
        return
    
    plt.figure(figsize=(12, 6))
    
    plt.plot(validation_data["dates"], validation_data["counts"]["total"], 
            marker='o', linestyle='-', label='Total Properties Checked')
    plt.plot(validation_data["dates"], validation_data["counts"]["passed"], 
            marker='o', linestyle='-', label='Passed Validation')
    plt.plot(validation_data["dates"], validation_data["counts"]["failed"], 
            marker='o', linestyle='-', label='Failed Validation')
    
    plt.title('Property Validation Counts Over Time')
    plt.xlabel('Date')
    plt.ylabel('Count')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.legend()
    
    # Format x-axis to show dates nicely
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.DayLocator(interval=5))
    plt.gcf().autofmt_xdate()
    
    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, filename), dpi=300)
    plt.close()

async def generate_geocoding_visualizations(days: int = 30, output_dir: str = "geocoding_reports"):
    """
    Generate all geocoding visualization charts.
    
    Args:
        days: Number of days of data to visualize
        output_dir: Directory to save visualizations
    """
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize database connection
    db_ops = EnrichmentDatabaseOps()
    
    try:
        # Fetch data
        print(f"Fetching geocoding data for the past {days} days...")
        validation_data, monitoring_data = await fetch_geocoding_data(db_ops, days)
        
        # Generate visualizations
        print("Generating visualizations...")
        
        # Check if we have any data
        if not validation_data["dates"] and not monitoring_data["dates"]:
            print("No geocoding data available for the specified time period")
            return
        
        # Create plots
        plot_success_rate_trend(validation_data, monitoring_data, output_dir)
        plot_failure_types(validation_data, output_dir)
        plot_alert_reasons(monitoring_data, output_dir)
        plot_failure_types_over_time(validation_data, output_dir)
        plot_validation_counts(validation_data, output_dir)
        
        print(f"Visualizations generated and saved to {output_dir}/")
        
    except Exception as e:
        print(f"Error generating visualizations: {e}")
    finally:
        # Close database connection
        await db_ops.close()

def main():
    """Parse arguments and run visualization generation."""
    parser = argparse.ArgumentParser(description="Generate geocoding quality visualizations")
    parser.add_argument("--days", type=int, default=30, help="Number of days of data to visualize")
    parser.add_argument("--output-dir", type=str, default="geocoding_reports", 
                      help="Directory to save visualizations")
    args = parser.parse_args()
    
    # Run the visualization generation
    asyncio.run(generate_geocoding_visualizations(days=args.days, output_dir=args.output_dir))
    
if __name__ == "__main__":
    main() 