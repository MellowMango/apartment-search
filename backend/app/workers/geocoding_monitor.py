#!/usr/bin/env python3
"""
Geocoding Quality Monitor

This module provides monitoring capabilities for the geocoding system.
It periodically:
1. Runs validation tests on geocoded properties
2. Generates reports on geocoding quality
3. Sends alerts when quality issues are detected
4. Tracks geocoding accuracy trends over time

This component serves as a monitoring layer on top of the geocoding validation system.
"""

import os
import sys
import asyncio
import logging
import argparse
import json
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import random
from collections import Counter

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import required modules
# from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
# from backend.tests.geocoding.test_geocoding_validation import GeocodingValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geocoding_monitor.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("geocoding_monitor")

class GeocodingMonitor:
    """
    Monitor for geocoding quality and accuracy.
    
    This class provides capabilities for monitoring the geocoding system,
    generating reports, and sending alerts when issues are detected.
    """
    
    def __init__(self, 
                alert_threshold: float = 90.0,
                sample_size: int = 100,
                email_recipients: Optional[List[str]] = None):
        """
        Initialize the geocoding monitor.
        
        Args:
            alert_threshold: Accuracy threshold below which alerts are triggered (%)
            sample_size: Number of properties to sample for monitoring
            email_recipients: List of email addresses to receive alerts
        """
        # self.db_ops = EnrichmentDatabaseOps()
        # self.validator = GeocodingValidator()
        self.alert_threshold = alert_threshold
        self.sample_size = sample_size
        self.email_recipients = email_recipients or []
        
        # Email settings from environment
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_sender = os.getenv("EMAIL_SENDER", "geocoding-monitor@acquire.com")
        
        logger.info(f"Geocoding monitor initialized with alert threshold {alert_threshold}%")
    
    async def run_monitoring_check(self) -> Dict[str, Any]:
        """
        Run a monitoring check on geocoding quality.
        
        Returns:
            Monitoring results including validation results and trends
        """
        logger.info(f"Running geocoding monitoring check on {self.sample_size} properties")
        start_time = datetime.now()
        
        # Run validation on a sample of properties
        validation_results = await self.validator.batch_validate_properties(
            limit=self.sample_size,
            include_recently_verified=True  # Include a mix of properties
        )
        
        # Calculate duration
        duration = datetime.now() - start_time
        duration_seconds = duration.total_seconds()
        
        # Get historical trends
        trends = await self.get_accuracy_trends()
        
        # Determine if an alert should be triggered
        should_alert = False
        alert_reasons = []
        
        # Check if accuracy is below threshold
        accuracy = validation_results.get("success_rate", 0)
        if accuracy < self.alert_threshold:
            should_alert = True
            alert_reasons.append(f"Accuracy ({accuracy:.2f}%) below threshold ({self.alert_threshold}%)")
        
        # Check for specific failure patterns that are concerning
        failure_types = validation_results.get("failure_types", {})
        
        # Alert on critical failure types with significant counts
        critical_failures = {
            "has_coordinates": "Missing coordinates",
            "valid_coordinate_range": "Invalid coordinate ranges",
            "duplicate_coordinates": "Duplicate coordinates across properties",
            "mismatched_city_coordinates": "City/coordinate mismatches"
        }
        
        for failure_type, description in critical_failures.items():
            for key, count in failure_types.items():
                if failure_type in key and count >= 5:  # Alert if 5 or more instances
                    should_alert = True
                    alert_reasons.append(f"{description}: {count} instances")
        
        # Generate monitoring report
        monitoring_report = {
            "timestamp": datetime.now().isoformat(),
            "duration_seconds": duration_seconds,
            "sample_size": self.sample_size,
            "accuracy": accuracy,
            "failure_types": failure_types,
            "trends": trends,
            "alert_triggered": should_alert,
            "alert_reasons": alert_reasons,
            "validation_details": validation_results
        }
        
        # Save report to database
        report_id = await self.save_monitoring_report(monitoring_report)
        monitoring_report["report_id"] = report_id
        
        # Send alert if needed
        if should_alert and self.email_recipients:
            await self.send_alert(monitoring_report)
        
        return monitoring_report
    
    async def get_accuracy_trends(self) -> Dict[str, Any]:
        """
        Get historical trends of geocoding accuracy.
        
        Returns:
            Dictionary with trend data
        """
        try:
            # Query the last 30 days of validation reports
            query = """
            SELECT 
                report_date,
                properties_count,
                passed_count,
                failed_count,
                success_rate,
                failure_types
            FROM geocoding_validation_reports
            WHERE report_date >= NOW() - INTERVAL '30 days'
            ORDER BY report_date
            """
            
            results = await self.db_ops.execute_raw_query(query)
            
            if not results:
                return {"status": "no_data", "message": "No historical data available"}
            
            # Process results into trend data
            trends = {
                "dates": [],
                "success_rates": [],
                "sample_sizes": [],
                "failure_trends": {}
            }
            
            for row in results:
                report_date = row[0].isoformat() if isinstance(row[0], datetime) else row[0]
                trends["dates"].append(report_date)
                trends["success_rates"].append(float(row[4]))
                trends["sample_sizes"].append(int(row[1]))
                
                # Track failure types over time
                failure_types = row[5] if isinstance(row[5], dict) else json.loads(row[5])
                for failure_type, count in failure_types.items():
                    if failure_type not in trends["failure_trends"]:
                        trends["failure_trends"][failure_type] = []
                    
                    # Append count for this date
                    trends["failure_trends"][failure_type].append(count)
            
            # Calculate trend statistics
            if trends["success_rates"]:
                trends["current_accuracy"] = trends["success_rates"][-1]
                trends["average_accuracy"] = sum(trends["success_rates"]) / len(trends["success_rates"])
                
                # Calculate week-over-week change if enough data
                if len(trends["success_rates"]) >= 7:
                    current_week_avg = sum(trends["success_rates"][-7:]) / 7
                    prev_week_avg = sum(trends["success_rates"][-14:-7]) / 7 if len(trends["success_rates"]) >= 14 else None
                    
                    if prev_week_avg:
                        trends["week_over_week_change"] = current_week_avg - prev_week_avg
            
            return trends
            
        except Exception as e:
            logger.error(f"Error getting accuracy trends: {e}")
            return {"status": "error", "message": str(e)}
    
    async def save_monitoring_report(self, report: Dict[str, Any]) -> str:
        """
        Save monitoring report to database.
        
        Args:
            report: Monitoring report data
            
        Returns:
            ID of the saved report
        """
        try:
            # Check if geocoding_monitoring_reports table exists
            check_table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'geocoding_monitoring_reports'
            )
            """
            
            table_exists = await self.db_ops.execute_raw_query(check_table_query)
            
            # Create table if it doesn't exist
            if not table_exists or not table_exists[0][0]:
                create_table_query = """
                CREATE TABLE geocoding_monitoring_reports (
                    id SERIAL PRIMARY KEY,
                    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    sample_size INTEGER,
                    accuracy NUMERIC,
                    alert_triggered BOOLEAN,
                    alert_reasons JSONB,
                    failure_types JSONB,
                    full_report JSONB
                );
                """
                await self.db_ops.execute_raw_query(create_table_query)
                logger.info("Created geocoding_monitoring_reports table")
            
            # Insert report
            insert_query = """
            INSERT INTO geocoding_monitoring_reports 
            (report_date, sample_size, accuracy, alert_triggered, alert_reasons, failure_types, full_report)
            VALUES (NOW(), $1, $2, $3, $4, $5, $6)
            RETURNING id;
            """
            
            report_id = await self.db_ops.execute_raw_query(
                insert_query, 
                [
                    report.get("sample_size", 0),
                    report.get("accuracy", 0),
                    report.get("alert_triggered", False),
                    json.dumps(report.get("alert_reasons", [])),
                    json.dumps(report.get("failure_types", {})),
                    json.dumps(report)
                ]
            )
            
            report_id_str = str(report_id[0][0]) if report_id and report_id[0] else "unknown"
            logger.info(f"Saved monitoring report to database with ID {report_id_str}")
            return report_id_str
            
        except Exception as e:
            logger.error(f"Error saving monitoring report: {e}")
            return "error"
    
    async def send_alert(self, report: Dict[str, Any]) -> bool:
        """
        Send an alert email about geocoding issues.
        
        Args:
            report: Monitoring report data
            
        Returns:
            True if alert was sent successfully, False otherwise
        """
        if not self.email_recipients or not self.smtp_username or not self.smtp_password:
            logger.warning("Email configuration incomplete, skipping alert")
            return False
            
        try:
            # Create email content
            subject = f"ALERT: Geocoding Quality Issue - {report.get('accuracy', 0):.2f}% Accuracy"
            
            # Create HTML content
            html_content = f"""
            <html>
            <body>
                <h2>Geocoding Quality Alert</h2>
                <p>The geocoding system has detected quality issues that require attention.</p>
                
                <h3>Alert Details:</h3>
                <ul>
                    <li><strong>Accuracy:</strong> {report.get('accuracy', 0):.2f}%</li>
                    <li><strong>Sample Size:</strong> {report.get('sample_size', 0)} properties</li>
                    <li><strong>Date:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</li>
                    <li><strong>Report ID:</strong> {report.get('report_id', 'unknown')}</li>
                </ul>
                
                <h3>Alert Reasons:</h3>
                <ul>
            """
            
            for reason in report.get("alert_reasons", []):
                html_content += f"<li>{reason}</li>"
                
            html_content += """
                </ul>
                
                <h3>Failure Types:</h3>
                <ul>
            """
            
            for failure_type, count in report.get("failure_types", {}).items():
                html_content += f"<li>{failure_type}: {count} instances</li>"
                
            html_content += """
                </ul>
                
                <p>Please check the geocoding system and address these issues.</p>
                <p>This is an automated message from the Geocoding Monitor.</p>
            </body>
            </html>
            """
            
            # Create plain text content
            text_content = f"""
            Geocoding Quality Alert
            
            The geocoding system has detected quality issues that require attention.
            
            Alert Details:
            - Accuracy: {report.get('accuracy', 0):.2f}%
            - Sample Size: {report.get('sample_size', 0)} properties
            - Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
            - Report ID: {report.get('report_id', 'unknown')}
            
            Alert Reasons:
            """
            
            for reason in report.get("alert_reasons", []):
                text_content += f"- {reason}\n"
                
            text_content += "\nFailure Types:\n"
            
            for failure_type, count in report.get("failure_types", {}).items():
                text_content += f"- {failure_type}: {count} instances\n"
                
            text_content += """
            Please check the geocoding system and address these issues.
            
            This is an automated message from the Geocoding Monitor.
            """
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = self.email_sender
            message["To"] = ", ".join(self.email_recipients)
            
            # Add content
            message.attach(MIMEText(text_content, "plain"))
            message.attach(MIMEText(html_content, "html"))
            
            # Connect to server and send
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.ehlo()
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)
            
            logger.info(f"Alert email sent to {len(self.email_recipients)} recipients")
            return True
            
        except Exception as e:
            logger.error(f"Error sending alert email: {e}")
            return False
    
    async def generate_weekly_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive weekly report on geocoding quality.
        
        Returns:
            Weekly report data
        """
        try:
            # Get data for the past week
            one_week_ago = datetime.now() - timedelta(days=7)
            
            # Get validation reports from the past week
            query = """
            SELECT 
                id, report_date, properties_count, passed_count, 
                failed_count, success_rate, failure_types
            FROM geocoding_validation_reports
            WHERE report_date >= $1
            ORDER BY report_date
            """
            
            validation_reports = await self.db_ops.execute_raw_query(query, [one_week_ago.isoformat()])
            
            if not validation_reports:
                return {"status": "no_data", "message": "No validation reports available for the past week"}
            
            # Process validation reports
            avg_success_rate = sum(float(r[5]) for r in validation_reports) / len(validation_reports)
            total_properties = sum(int(r[2]) for r in validation_reports)
            total_passed = sum(int(r[3]) for r in validation_reports)
            total_failed = sum(int(r[4]) for r in validation_reports)
            
            # Aggregate failure types
            failure_types = {}
            for report in validation_reports:
                report_failures = report[6] if isinstance(report[6], dict) else json.loads(report[6])
                for failure_type, count in report_failures.items():
                    failure_types[failure_type] = failure_types.get(failure_type, 0) + count
            
            # Get monitoring reports from the past week
            query = """
            SELECT 
                id, report_date, sample_size, accuracy, 
                alert_triggered, alert_reasons
            FROM geocoding_monitoring_reports
            WHERE report_date >= $1
            ORDER BY report_date
            """
            
            monitoring_reports = await self.db_ops.execute_raw_query(query, [one_week_ago.isoformat()])
            alerts_triggered = sum(1 for r in monitoring_reports if r[4])  # Count of True values
            
            # Get current accuracy based on a new validation run
            current_results = await self.validator.batch_validate_properties(
                limit=200,  # Larger sample for weekly report
                include_recently_verified=True
            )
            
            # Compile weekly report
            weekly_report = {
                "report_date": datetime.now().isoformat(),
                "period_start": one_week_ago.isoformat(),
                "period_end": datetime.now().isoformat(),
                "validation_reports_count": len(validation_reports),
                "monitoring_reports_count": len(monitoring_reports),
                "alerts_triggered": alerts_triggered,
                "average_success_rate": avg_success_rate,
                "total_properties_checked": total_properties,
                "total_passed": total_passed,
                "total_failed": total_failed,
                "current_accuracy": current_results.get("success_rate", 0),
                "most_common_failures": dict(sorted(failure_types.items(), key=lambda x: x[1], reverse=True)[:10]),
                "trends": await self.get_accuracy_trends(),
                "recommendations": await self.generate_recommendations(
                    failure_types, 
                    avg_success_rate, 
                    alerts_triggered
                )
            }
            
            return weekly_report
            
        except Exception as e:
            logger.error(f"Error generating weekly report: {e}")
            return {"status": "error", "message": str(e)}
    
    async def generate_recommendations(self, 
                                    failure_types: Dict[str, int], 
                                    avg_accuracy: float, 
                                    alerts_count: int) -> List[str]:
        """
        Generate recommendations based on monitoring data.
        
        Args:
            failure_types: Dictionary of failure types and counts
            avg_accuracy: Average accuracy from reports
            alerts_count: Number of alerts triggered
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Accuracy-based recommendations
        if avg_accuracy < 85:
            recommendations.append("Urgent: Overall geocoding accuracy is critically low. Consider full review of geocoding system.")
        elif avg_accuracy < 95:
            recommendations.append("Consider improvements to geocoding accuracy through provider tuning or address normalization.")
        
        # Failure-based recommendations
        for failure_type, count in failure_types.items():
            if "duplicate_coordinates" in failure_type and count > 10:
                recommendations.append("High number of duplicate coordinates detected. Check for city/zip centroid fallbacks in geocoding service.")
            
            if "coordinates_match" in failure_type and count > 20:
                recommendations.append("Many coordinates don't match when re-geocoded. Consider refreshing coordinates for better accuracy.")
            
            if "valid_coordinate_range" in failure_type and count > 5:
                recommendations.append("Invalid coordinates detected. Review geocoding validation logic and coordinate normalization.")
            
            if "mismatched_city_coordinates" in failure_type and count > 5:
                recommendations.append("City/coordinate mismatches detected. Investigate possible geocoding errors with city centroids.")
        
        # Alert-based recommendations
        if alerts_count > 5:
            recommendations.append(f"Multiple alerts ({alerts_count}) triggered in past week. Consider increasing geocoding monitoring frequency.")
        
        # Generic recommendations if none specific
        if not recommendations:
            if avg_accuracy > 98:
                recommendations.append("Geocoding system performing well. Consider expanding validation to more edge cases.")
            else:
                recommendations.append("Consider periodic review of geocoding providers and accuracy benchmarking.")
        
        return recommendations


async def run_monitoring(args):
    """Run geocoding monitoring with command-line arguments."""
    monitor = GeocodingMonitor(
        alert_threshold=args.threshold,
        sample_size=args.sample_size,
        email_recipients=args.email.split(",") if args.email else []
    )
    
    if args.weekly_report:
        # Generate weekly report
        logger.info("Generating weekly geocoding report")
        report = await monitor.generate_weekly_report()
        
        # Write report to file
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Weekly report saved to {args.output}")
        
        # Print summary
        print(f"Weekly Geocoding Report:")
        print(f"Period: {report.get('period_start')} to {report.get('period_end')}")
        print(f"Average Success Rate: {report.get('average_success_rate', 0):.2f}%")
        print(f"Current Accuracy: {report.get('current_accuracy', 0):.2f}%")
        print(f"Alerts Triggered: {report.get('alerts_triggered', 0)}")
        print(f"Total Properties Checked: {report.get('total_properties_checked', 0)}")
        
        if report.get("recommendations"):
            print("\nRecommendations:")
            for i, rec in enumerate(report.get("recommendations", []), 1):
                print(f"{i}. {rec}")
    else:
        # Run monitoring check
        logger.info("Running geocoding monitoring check")
        report = await monitor.run_monitoring_check()
        
        # Write report to file
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Monitoring report saved to {args.output}")
        
        # Print summary
        print(f"Geocoding Monitoring Results:")
        print(f"Timestamp: {report.get('timestamp')}")
        print(f"Accuracy: {report.get('accuracy', 0):.2f}%")
        print(f"Sample Size: {report.get('sample_size', 0)}")
        
        if report.get("alert_triggered"):
            print("\nALERT TRIGGERED!")
            for reason in report.get("alert_reasons", []):
                print(f"- {reason}")
        else:
            print("\nNo alerts triggered. Geocoding quality is within acceptable threshold.")
    
    # Close database connections
    await monitor.db_ops.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Geocoding Quality Monitor")
    parser.add_argument("--threshold", type=float, default=90.0, help="Alert threshold for accuracy percentage")
    parser.add_argument("--sample-size", type=int, default=100, help="Number of properties to sample")
    parser.add_argument("--email", type=str, default="", help="Email recipients for alerts (comma-separated)")
    parser.add_argument("--output", type=str, default="geocoding_monitor_report.json", help="Output file for monitoring report")
    parser.add_argument("--weekly-report", action="store_true", help="Generate weekly report instead of monitoring check")
    args = parser.parse_args()
    
    asyncio.run(run_monitoring(args)) 