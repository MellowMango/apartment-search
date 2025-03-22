from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
import json

from app.services.user_service import UserService
from app.services.property_service import PropertyService
from app.services.broker_service import BrokerService
from app.services.brokerage_service import BrokerageService
from app.services.neo4j_sync import Neo4jSyncService
from .... import schemas
from ....core.auth import get_current_active_superuser, get_current_active_user
from ....db.session import get_db
from ....data_enrichment.database_extensions import EnrichmentDatabaseOps

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

@router.get("/stats")
async def get_stats(
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(),
    property_service: PropertyService = Depends(),
    broker_service: BrokerService = Depends(),
    brokerage_service: BrokerageService = Depends()
):
    """
    Get admin statistics.
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Get counts
    property_count = await property_service.get_property_count()
    broker_count = await broker_service.get_broker_count()
    brokerage_count = await brokerage_service.get_brokerage_count()
    user_count = await user_service.get_user_count()
    
    return {
        "properties": property_count,
        "brokers": broker_count,
        "brokerages": brokerage_count,
        "users": user_count
    }

@router.post("/sync/neo4j")
async def sync_neo4j(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends(),
    neo4j_sync_service: Neo4jSyncService = Depends()
):
    """
    Trigger a sync of all data to Neo4j.
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # Start the sync in the background
    background_tasks.add_task(neo4j_sync_service.sync_all)
    
    return {"message": "Neo4j sync started"}

@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    token: str = Depends(oauth2_scheme),
    user_service: UserService = Depends()
):
    """
    Trigger a scrape of property listings.
    """
    # Check if the user is an admin
    current_user = await user_service.get_current_user(token)
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    
    # This would normally trigger a Celery task to start the scraper
    # For now, we'll just return a message
    
    return {"message": "Scrape job started"}

@router.get("/missing-info/reports", response_model=List[schemas.MissingInfoReport])
async def get_missing_info_reports(
    *,
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 10,
    days: int = 30,
    current_user: schemas.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get a list of missing information reports.
    Only accessible by superusers.
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Create database client
    db_ops = EnrichmentDatabaseOps()
    
    try:
        # Query reports
        query = """
        SELECT 
            id,
            report_date,
            total_properties_scanned,
            properties_with_missing_info,
            brokers_to_contact
        FROM 
            missing_info_reports
        WHERE 
            report_date BETWEEN $1 AND $2
        ORDER BY 
            report_date DESC
        LIMIT $3 OFFSET $4
        """
        
        results = await db_ops.execute_raw_query(
            query, [start_date.isoformat(), end_date.isoformat(), limit, skip]
        )
        
        if not results:
            return []
        
        # Format results
        reports = []
        for row in results:
            reports.append({
                "id": row[0],
                "report_date": row[1].isoformat() if isinstance(row[1], datetime) else row[1],
                "total_properties_scanned": row[2],
                "properties_with_missing_info": row[3],
                "brokers_to_contact": row[4]
            })
        
        return reports
    
    finally:
        await db_ops.close()

@router.get("/missing-info/reports/{report_id}", response_model=schemas.MissingInfoReportDetail)
async def get_missing_info_report_detail(
    *,
    report_id: int,
    current_user: schemas.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get detailed information for a specific missing info report.
    Only accessible by superusers.
    """
    # Create database client
    db_ops = EnrichmentDatabaseOps()
    
    try:
        # Query report
        query = """
        SELECT 
            id,
            report_date,
            total_properties_scanned,
            properties_with_missing_info,
            brokers_to_contact,
            properties,
            properties_by_broker
        FROM 
            missing_info_reports
        WHERE 
            id = $1
        """
        
        results = await db_ops.execute_raw_query(query, [report_id])
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Format result
        row = results[0]
        report = {
            "id": row[0],
            "report_date": row[1].isoformat() if isinstance(row[1], datetime) else row[1],
            "total_properties_scanned": row[2],
            "properties_with_missing_info": row[3],
            "brokers_to_contact": row[4],
            "properties": row[5] if isinstance(row[5], list) else json.loads(row[5]),
            "properties_by_broker": row[6] if isinstance(row[6], dict) else json.loads(row[6])
        }
        
        return report
    
    finally:
        await db_ops.close()

@router.post("/missing-info/send-emails", response_model=schemas.MissingInfoEmailResult)
async def send_missing_info_emails(
    *,
    report_id: int,
    broker_emails: Optional[List[str]] = None,
    current_user: schemas.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Send emails to brokers requesting missing property information.
    Can specify specific broker emails, or will send to all brokers in the report.
    Only accessible by superusers.
    """
    # Create database client
    db_ops = EnrichmentDatabaseOps()
    
    try:
        # First get the report data
        query = """
        SELECT 
            properties_by_broker
        FROM 
            missing_info_reports
        WHERE 
            id = $1
        """
        
        results = await db_ops.execute_raw_query(query, [report_id])
        
        if not results:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Report not found"
            )
        
        # Get the properties by broker
        properties_by_broker = results[0][0] if isinstance(results[0][0], dict) else json.loads(results[0][0])
        
        # Import the missing info detector
        from ....workers.missing_info_detector import MissingInfoDetector
        
        # Create detector
        detector = MissingInfoDetector(db_ops=db_ops)
        
        # Filter brokers if needed
        if broker_emails:
            filtered_brokers = {
                email: properties_by_broker[email] 
                for email in broker_emails 
                if email in properties_by_broker
            }
        else:
            filtered_brokers = properties_by_broker
        
        # Send emails
        if not filtered_brokers:
            return {
                "success": False,
                "emails_sent": 0,
                "message": "No matching brokers found"
            }
        
        # Create a report with just the filtered brokers
        report = {
            "properties_by_broker": filtered_brokers
        }
        
        # Generate and send emails
        results = await detector.generate_broker_request_emails(report, send_emails=True)
        
        return {
            "success": results.get("emails_sent", 0) > 0,
            "emails_sent": results.get("emails_sent", 0),
            "emails_generated": results.get("emails_generated", 0),
            "broker_emails": results.get("broker_emails", [])
        }
    
    finally:
        # Don't close db_ops here as detector uses it and will close it
        pass

@router.get("/missing-info/properties", response_model=List[schemas.PropertyWithMissingInfo])
async def get_properties_with_missing_info(
    *,
    broker_email: Optional[str] = None,
    days_since_update: int = 30,
    limit: int = 50,
    current_user: schemas.User = Depends(get_current_active_superuser),
) -> Any:
    """
    Get a list of properties with missing information.
    Can filter by broker email.
    Only accessible by superusers.
    """
    # Create database client and detector
    db_ops = EnrichmentDatabaseOps()
    
    try:
        # Import the missing info detector
        from ....workers.missing_info_detector import MissingInfoDetector
        
        # Create detector
        detector = MissingInfoDetector(db_ops=db_ops)
        
        # Run a scan
        report = await detector.scan_for_missing_info(
            days_since_update=days_since_update,
            limit=limit
        )
        
        # Filter by broker if needed
        if broker_email and report.get("properties"):
            properties = [
                prop for prop in report.get("properties", [])
                if prop.get("broker_email") == broker_email
            ]
        else:
            properties = report.get("properties", [])
        
        return properties
    
    finally:
        await db_ops.close() 