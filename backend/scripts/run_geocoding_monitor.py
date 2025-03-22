#!/usr/bin/env python3
"""
Run Geocoding Monitor

This script provides a command-line interface to run the geocoding monitoring
system manually. It allows users to check geocoding quality, generate reports,
and visualize metrics without waiting for scheduled cron jobs.
"""

import os
import sys
import asyncio
import argparse
import logging
from datetime import datetime

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("geocoding-monitor")

async def run_monitoring(args):
    """Run the geocoding monitoring system with the specified arguments."""
    try:
        # Import the monitor here to avoid circular imports
        from app.workers.geocoding_monitor import GeocodingMonitor
        
        # Initialize monitor
        monitor = GeocodingMonitor(
            alert_threshold=args.alert_threshold,
            sample_size=args.sample_size,
            email_recipients=args.email.split(',') if args.email else None
        )
        
        # Run appropriate function based on arguments
        if args.generate_report:
            logger.info(f"Generating geocoding quality report: {args.output}")
            await monitor.generate_weekly_report(output_file=args.output)
            logger.info(f"Report generated successfully at {args.output}")
            
        elif args.check_suspicious:
            logger.info("Running check for suspicious coordinates...")
            suspicious_count = await monitor.check_suspicious_coordinates(limit=args.sample_size)
            logger.info(f"Found {suspicious_count} properties with suspicious coordinates")
            
        elif args.visualize:
            logger.info(f"Generating visualizations for the past {args.days} days...")
            # Import the visualization module
            sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
            from visualize_geocoding_metrics import generate_geocoding_visualizations
            await generate_geocoding_visualizations(days=args.days, output_dir=args.output_dir)
            logger.info(f"Visualizations generated in {args.output_dir}")
            
        else:
            # Run standard monitoring check
            logger.info(f"Running monitoring check with sample size {args.sample_size}...")
            report = await monitor.run_monitoring_check()
            
            if report['alert_triggered']:
                logger.warning("⚠️ Alert triggered! Reasons:")
                for reason in report['alert_reasons']:
                    logger.warning(f"  - {reason}")
            else:
                logger.info(f"✅ All checks passed! Accuracy: {report['accuracy']:.2f}%")
                
            logger.info(f"Failure distribution: {report['failure_types']}")
            
            # Send email if requested
            if args.email and report['alert_triggered']:
                logger.info(f"Sending alert email to {args.email}")
                await monitor.send_alert_email(report)
                
    except ImportError as e:
        logger.error(f"Import error: {e}. Make sure all required modules are installed.")
    except Exception as e:
        logger.error(f"Error running monitoring: {e}")

def main():
    """Parse command line arguments and run the monitoring system."""
    parser = argparse.ArgumentParser(description="Run the geocoding monitoring system manually")
    
    # Basic configuration
    parser.add_argument("--sample-size", type=int, default=100,
                      help="Number of properties to sample for monitoring")
    parser.add_argument("--alert-threshold", type=float, default=90.0,
                      help="Accuracy percentage threshold below which to trigger alerts")
    parser.add_argument("--email", type=str,
                      help="Email address(es) to send alerts to (comma-separated)")
    
    # Operating modes
    parser.add_argument("--generate-report", action="store_true",
                      help="Generate a comprehensive weekly report")
    parser.add_argument("--check-suspicious", action="store_true",
                      help="Check for suspicious coordinates only")
    parser.add_argument("--visualize", action="store_true",
                      help="Generate visualization charts of geocoding metrics")
    
    # Output options
    parser.add_argument("--output", type=str, default="geocoding_report.json",
                      help="Output file for report generation")
    parser.add_argument("--output-dir", type=str, default="geocoding_reports",
                      help="Output directory for visualizations")
    parser.add_argument("--days", type=int, default=30,
                      help="Number of days of history to include in report/visualization")
    
    # Parse arguments and run
    args = parser.parse_args()
    asyncio.run(run_monitoring(args))

if __name__ == "__main__":
    main() 