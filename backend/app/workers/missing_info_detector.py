#!/usr/bin/env python3
"""
Missing Information Detector

This script identifies properties with missing or incomplete information,
generates reports for admin review, and can send email requests to brokers
to provide that information.
"""

import os
import sys
import asyncio
import logging
import argparse
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple, Set

# Add parent directory to path to allow imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Import required modules
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("missing_info_detector.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("missing-info-detector")

class MissingInfoDetector:
    """
    Detector for missing or incomplete property information.
    
    This class identifies properties with missing critical information,
    prioritizes them based on importance, and can generate email requests
    to brokers to provide the missing data.
    """
    
    # Define critical fields that should be present for all properties
    CRITICAL_FIELDS = {
        # Property identification
        'property_name': 'Property Name',
        'address': 'Street Address',
        'city': 'City',
        'state': 'State',
        'zip_code': 'ZIP Code',
        
        # Core property details
        'units_count': 'Number of Units',
        'property_type': 'Property Type',
        'year_built': 'Year Built',
        'square_footage': 'Square Footage',
        
        # Pricing info
        'price': 'Asking Price',
        'price_per_unit': 'Price Per Unit',
        
        # Location info
        'latitude': 'Latitude',
        'longitude': 'Longitude',
        
        # Status
        'status': 'Listing Status'
    }
    
    # Define additional important but non-critical fields
    IMPORTANT_FIELDS = {
        'description': 'Property Description',
        'cap_rate': 'Cap Rate',
        'lot_size': 'Lot Size',
        'zoning': 'Zoning',
        'parking_spaces': 'Parking Spaces',
        'amenities': 'Amenities',
        'broker_name': 'Broker Name',
        'broker_phone': 'Broker Phone',
        'broker_email': 'Broker Email',
        'images': 'Property Images'
    }
    
    def __init__(self, db_ops: Optional[EnrichmentDatabaseOps] = None):
        """
        Initialize the missing information detector.
        
        Args:
            db_ops: Optional database operations object
        """
        self.db_ops = db_ops or EnrichmentDatabaseOps()
        
        # Email settings from environment
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", 587))
        self.smtp_username = os.getenv("SMTP_USERNAME", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.email_sender = os.getenv("EMAIL_SENDER", "info@acquire-apartments.com")
        
        logger.info("Missing information detector initialized")
    
    async def scan_for_missing_info(self, days_since_update: int = 30, limit: int = 100) -> Dict[str, Any]:
        """
        Scan the database for properties with missing information.
        
        Args:
            days_since_update: Only scan properties updated more than this many days ago
            limit: Maximum number of properties to scan
            
        Returns:
            Report on properties with missing information
        """
        logger.info(f"Scanning for properties with missing information (limit: {limit})")
        
        # Query for properties that haven't been updated recently
        cutoff_date = datetime.now() - timedelta(days=days_since_update)
        
        query = """
        SELECT 
            p.id,
            p.property_name,
            p.address,
            p.city,
            p.state,
            p.zip_code,
            p.latitude,
            p.longitude,
            p.units_count,
            p.property_type,
            p.year_built,
            p.square_footage,
            p.price,
            p.price_per_unit,
            p.status,
            p.description,
            p.cap_rate,
            p.lot_size,
            p.zoning,
            p.parking_spaces,
            p.amenities,
            b.name as broker_name,
            b.phone as broker_phone,
            b.email as broker_email,
            (SELECT COUNT(*) FROM property_images pi WHERE pi.property_id = p.id) as image_count,
            p.last_updated,
            p.source_url,
            br.name as brokerage_name,
            br.website as brokerage_website
        FROM 
            properties p
        LEFT JOIN 
            brokers b ON p.broker_id = b.id
        LEFT JOIN 
            brokerages br ON b.brokerage_id = br.id
        WHERE 
            p.last_updated < $1
            AND p.status = 'active'
        ORDER BY 
            p.last_updated ASC
        LIMIT $2
        """
        
        results = await self.db_ops.execute_raw_query(query, [cutoff_date.isoformat(), limit])
        
        if not results:
            logger.info("No properties found that need updating")
            return {
                "status": "no_properties",
                "message": "No properties found that need information updates"
            }
        
        # Process results
        properties_with_missing_info = []
        properties_by_broker = {}
        
        for row in results:
            # Convert row to dictionary for easier handling
            property_data = {
                "id": row[0],
                "property_name": row[1],
                "address": row[2],
                "city": row[3],
                "state": row[4],
                "zip_code": row[5],
                "latitude": row[6],
                "longitude": row[7],
                "units_count": row[8],
                "property_type": row[9],
                "year_built": row[10],
                "square_footage": row[11],
                "price": row[12],
                "price_per_unit": row[13],
                "status": row[14],
                "description": row[15],
                "cap_rate": row[16],
                "lot_size": row[17],
                "zoning": row[18],
                "parking_spaces": row[19],
                "amenities": row[20],
                "broker_name": row[21],
                "broker_phone": row[22],
                "broker_email": row[23],
                "image_count": row[24],
                "last_updated": row[25].isoformat() if row[25] else None,
                "source_url": row[26],
                "brokerage_name": row[27],
                "brokerage_website": row[28]
            }
            
            # Check for missing critical fields
            missing_critical = []
            for field, display_name in self.CRITICAL_FIELDS.items():
                if field in property_data and (property_data[field] is None or property_data[field] == "" or 
                                           (field in ['latitude', 'longitude'] and property_data[field] == 0)):
                    missing_critical.append(display_name)
            
            # Check for missing important fields
            missing_important = []
            for field, display_name in self.IMPORTANT_FIELDS.items():
                if field in property_data and (property_data[field] is None or property_data[field] == "" or 
                                           (field == 'images' and property_data['image_count'] == 0)):
                    missing_important.append(display_name)
            
            # If we have missing fields, add to our lists
            if missing_critical or missing_important:
                property_summary = {
                    "id": property_data["id"],
                    "property_name": property_data["property_name"] or f"Property at {property_data['address']}",
                    "address": f"{property_data['address']}, {property_data['city']}, {property_data['state']} {property_data['zip_code']}",
                    "missing_critical": missing_critical,
                    "missing_important": missing_important,
                    "broker_email": property_data["broker_email"],
                    "broker_name": property_data["broker_name"],
                    "brokerage_name": property_data["brokerage_name"],
                    "last_updated": property_data["last_updated"],
                    "source_url": property_data["source_url"],
                    "days_since_update": (datetime.now() - datetime.fromisoformat(property_data["last_updated"])).days if property_data["last_updated"] else None
                }
                
                properties_with_missing_info.append(property_summary)
                
                # Group by broker for email generation
                if property_data["broker_email"]:
                    if property_data["broker_email"] not in properties_by_broker:
                        properties_by_broker[property_data["broker_email"]] = {
                            "broker_name": property_data["broker_name"],
                            "broker_email": property_data["broker_email"],
                            "brokerage_name": property_data["brokerage_name"],
                            "properties": []
                        }
                    
                    properties_by_broker[property_data["broker_email"]]["properties"].append(property_summary)
        
        # Generate the report
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_properties_scanned": len(results),
            "properties_with_missing_info": len(properties_with_missing_info),
            "brokers_to_contact": len(properties_by_broker),
            "properties": properties_with_missing_info,
            "properties_by_broker": properties_by_broker
        }
        
        # Save report to database
        report_id = await self.save_missing_info_report(report)
        report["report_id"] = report_id
        
        logger.info(f"Found {len(properties_with_missing_info)} properties with missing information across {len(properties_by_broker)} brokers")
        return report
    
    async def save_missing_info_report(self, report: Dict[str, Any]) -> str:
        """
        Save missing information report to database.
        
        Args:
            report: Missing information report data
            
        Returns:
            ID of the saved report
        """
        try:
            # Check if missing_info_reports table exists
            check_table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'missing_info_reports'
            )
            """
            
            table_exists = await self.db_ops.execute_raw_query(check_table_query)
            
            # Create table if it doesn't exist
            if not table_exists or not table_exists[0][0]:
                create_table_query = """
                CREATE TABLE missing_info_reports (
                    id SERIAL PRIMARY KEY,
                    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    total_properties_scanned INTEGER,
                    properties_with_missing_info INTEGER,
                    brokers_to_contact INTEGER,
                    properties JSONB,
                    properties_by_broker JSONB,
                    full_report JSONB
                );
                """
                await self.db_ops.execute_raw_query(create_table_query)
                logger.info("Created missing_info_reports table")
            
            # Insert report
            insert_query = """
            INSERT INTO missing_info_reports 
            (report_date, total_properties_scanned, properties_with_missing_info, brokers_to_contact, properties, properties_by_broker, full_report)
            VALUES (NOW(), $1, $2, $3, $4, $5, $6)
            RETURNING id;
            """
            
            report_id = await self.db_ops.execute_raw_query(
                insert_query, 
                [
                    report.get("total_properties_scanned", 0),
                    report.get("properties_with_missing_info", 0),
                    report.get("brokers_to_contact", 0),
                    json.dumps(report.get("properties", [])),
                    json.dumps(report.get("properties_by_broker", {})),
                    json.dumps(report)
                ]
            )
            
            report_id_str = str(report_id[0][0]) if report_id and report_id[0] else "unknown"
            logger.info(f"Saved missing info report to database with ID {report_id_str}")
            return report_id_str
            
        except Exception as e:
            logger.error(f"Error saving missing info report: {e}")
            return "error"
    
    async def generate_broker_request_emails(self, report: Dict[str, Any], 
                                          send_emails: bool = False) -> Dict[str, Any]:
        """
        Generate emails to brokers requesting missing information.
        
        Args:
            report: Missing information report data
            send_emails: Whether to actually send the emails
            
        Returns:
            Results of email generation and sending
        """
        if not report.get("properties_by_broker"):
            logger.info("No brokers to contact in the report")
            return {
                "status": "no_brokers",
                "message": "No brokers to contact in the report"
            }
        
        email_results = {
            "emails_generated": 0,
            "emails_sent": 0,
            "broker_emails": []
        }
        
        for broker_email, broker_data in report.get("properties_by_broker", {}).items():
            if not broker_email:
                continue
                
            # Create email content
            subject = f"Request for Additional Property Information - {broker_data.get('brokerage_name', 'Your Listings')}"
            
            # Create HTML content
            html_content = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2>Request for Additional Property Information</h2>
                    <p>Hello {broker_data.get('broker_name', 'Broker')},</p>
                    
                    <p>We are reaching out regarding some of your property listings on Acquire Apartments. 
                    To ensure the highest quality information for our users, we'd like to request some additional details 
                    for the following properties:</p>
                    
                    <ul style="padding-left: 20px;">
            """
            
            for property_data in broker_data.get("properties", []):
                html_content += f"""
                    <li>
                        <strong>{property_data.get('property_name')}</strong> - {property_data.get('address')}
                        <ul style="padding-left: 20px;">
                """
                
                if property_data.get("missing_critical"):
                    html_content += f"""
                            <li>
                                <strong>Critical information needed:</strong>
                                <ul style="padding-left: 20px;">
                    """
                    
                    for field in property_data.get("missing_critical", []):
                        html_content += f"<li>{field}</li>"
                    
                    html_content += """
                                </ul>
                            </li>
                    """
                
                if property_data.get("missing_important"):
                    html_content += f"""
                            <li>
                                <strong>Additional information requested:</strong>
                                <ul style="padding-left: 20px;">
                    """
                    
                    for field in property_data.get("missing_important", []):
                        html_content += f"<li>{field}</li>"
                    
                    html_content += """
                                </ul>
                            </li>
                    """
                
                # Add link to original listing
                if property_data.get("source_url"):
                    html_content += f"""
                            <li>
                                <a href="{property_data.get('source_url')}" target="_blank">View Original Listing</a>
                            </li>
                    """
                
                html_content += """
                        </ul>
                    </li>
                """
            
            html_content += """
                    </ul>
                    
                    <p>You can provide this information by:</p>
                    <ol style="padding-left: 20px;">
                        <li>Replying directly to this email with the requested details</li>
                        <li>Updating your listings on your website (we'll automatically capture the changes)</li>
                        <li>Logging into your Acquire Apartments account and updating the listings directly</li>
                    </ol>
                    
                    <p>Complete, accurate listings get more engagement from qualified buyers. Thank you for helping us maintain the highest quality information for your properties.</p>
                    
                    <p>Best regards,<br>
                    The Acquire Apartments Team</p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #dddddd; font-size: 12px; color: #666666;">
                        <p>This email was sent automatically as part of our data quality process. If you have questions, please contact support@acquire-apartments.com.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Create plain text content
            text_content = f"""
            Request for Additional Property Information
            
            Hello {broker_data.get('broker_name', 'Broker')},
            
            We are reaching out regarding some of your property listings on Acquire Apartments. 
            To ensure the highest quality information for our users, we'd like to request some additional details 
            for the following properties:
            
            """
            
            for property_data in broker_data.get("properties", []):
                text_content += f"""
            * {property_data.get('property_name')} - {property_data.get('address')}
                """
                
                if property_data.get("missing_critical"):
                    text_content += f"""
              Critical information needed:
                """
                    
                    for field in property_data.get("missing_critical", []):
                        text_content += f"              - {field}\n"
                
                if property_data.get("missing_important"):
                    text_content += f"""
              Additional information requested:
                """
                    
                    for field in property_data.get("missing_important", []):
                        text_content += f"              - {field}\n"
                
                # Add link to original listing
                if property_data.get("source_url"):
                    text_content += f"""
              Original listing: {property_data.get('source_url')}
                """
            
            text_content += """
            You can provide this information by:
            1. Replying directly to this email with the requested details
            2. Updating your listings on your website (we'll automatically capture the changes)
            3. Logging into your Acquire Apartments account and updating the listings directly
            
            Complete, accurate listings get more engagement from qualified buyers. Thank you for helping us maintain the highest quality information for your properties.
            
            Best regards,
            The Acquire Apartments Team
            
            ---
            This email was sent automatically as part of our data quality process. If you have questions, please contact support@acquire-apartments.com.
            """
            
            # Record the email for our results
            email_record = {
                "broker_email": broker_email,
                "broker_name": broker_data.get("broker_name"),
                "subject": subject,
                "property_count": len(broker_data.get("properties", [])),
                "sent": False
            }
            
            email_results["emails_generated"] += 1
            
            # Send the email if requested
            if send_emails and self.smtp_username and self.smtp_password:
                try:
                    # Create message
                    message = MIMEMultipart("alternative")
                    message["Subject"] = subject
                    message["From"] = self.email_sender
                    message["To"] = broker_email
                    message["Reply-To"] = "support@acquire-apartments.com"
                    
                    # Add content
                    message.attach(MIMEText(text_content, "plain"))
                    message.attach(MIMEText(html_content, "html"))
                    
                    # Connect to server and send
                    with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                        server.ehlo()
                        server.starttls()
                        server.login(self.smtp_username, self.smtp_password)
                        server.send_message(message)
                    
                    logger.info(f"Sent email to {broker_email}")
                    email_record["sent"] = True
                    email_results["emails_sent"] += 1
                    
                except Exception as e:
                    logger.error(f"Error sending email to {broker_email}: {e}")
            
            email_results["broker_emails"].append(email_record)
        
        return email_results
    
    async def run_weekly_missing_info_scan(self, days_since_update: int = 30, 
                                        limit: int = 500, 
                                        send_emails: bool = False) -> Dict[str, Any]:
        """
        Run a weekly scan for missing property information.
        
        Args:
            days_since_update: Only scan properties updated more than this many days ago
            limit: Maximum number of properties to scan
            send_emails: Whether to send emails to brokers
            
        Returns:
            Results of the scan and email generation
        """
        logger.info(f"Running weekly missing info scan (limit: {limit}, send_emails: {send_emails})")
        
        # Scan for missing info
        report = await self.scan_for_missing_info(days_since_update, limit)
        
        # Generate email requests
        if report.get("properties_with_missing_info", 0) > 0:
            email_results = await self.generate_broker_request_emails(report, send_emails)
            report["email_results"] = email_results
        
        return report


async def run_missing_info_detector(args):
    """Run missing info detector with command-line arguments."""
    detector = MissingInfoDetector()
    
    if args.weekly_scan:
        # Run weekly scan
        logger.info(f"Running weekly missing info scan (limit: {args.limit}, send_emails: {args.send_emails})")
        report = await detector.run_weekly_missing_info_scan(
            days_since_update=args.days_since_update,
            limit=args.limit,
            send_emails=args.send_emails
        )
        
        # Write report to file
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Weekly missing info scan complete. Report saved to {args.output}")
        
        # Print summary
        print(f"Missing Information Scan Results:")
        print(f"Properties scanned: {report.get('total_properties_scanned', 0)}")
        print(f"Properties with missing info: {report.get('properties_with_missing_info', 0)}")
        print(f"Brokers to contact: {report.get('brokers_to_contact', 0)}")
        
        if args.send_emails:
            print(f"Emails sent: {report.get('email_results', {}).get('emails_sent', 0)}")
    
    else:
        # Run basic scan
        logger.info(f"Running basic missing info scan (limit: {args.limit})")
        report = await detector.scan_for_missing_info(
            days_since_update=args.days_since_update,
            limit=args.limit
        )
        
        # Write report to file
        with open(args.output, "w") as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Missing info scan complete. Report saved to {args.output}")
        
        # Print summary
        print(f"Missing Information Scan Results:")
        print(f"Properties scanned: {report.get('total_properties_scanned', 0)}")
        print(f"Properties with missing info: {report.get('properties_with_missing_info', 0)}")
        print(f"Brokers to contact: {report.get('brokers_to_contact', 0)}")
    
    # Close database connections
    await detector.db_ops.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Missing Information Detector")
    parser.add_argument("--days-since-update", type=int, default=30, 
                      help="Only scan properties updated more than this many days ago")
    parser.add_argument("--limit", type=int, default=100, 
                      help="Maximum number of properties to scan")
    parser.add_argument("--output", type=str, default="missing_info_report.json", 
                      help="Output file for the report")
    parser.add_argument("--weekly-scan", action="store_true", 
                      help="Run a comprehensive weekly scan")
    parser.add_argument("--send-emails", action="store_true", 
                      help="Send email requests to brokers")
    args = parser.parse_args()
    
    asyncio.run(run_missing_info_detector(args)) 