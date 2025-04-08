from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks, Query
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
# from sqlalchemy.orm import Session # Likely unused
import json
import logging

# Change back to relative imports
from ....core.dependencies import get_current_active_superuser
from .... import schemas # Import the top-level schemas
from ....schemas.architecture import ArchitectureMetrics, LayerComponentCount
from ....utils.monitoring import get_metrics, get_layer_metrics
from ....schemas.api import APIResponse
from ....services.user_service import UserService
from ....services.property_service import PropertyService
from ....services.broker_service import BrokerService
from ....services.brokerage_service import BrokerageService
from ....core.config import settings
# from ....services.neo4j_sync import Neo4jSyncService # Assuming this exists
# from ....services.metrics_service import MetricsService # Assuming this exists
# from ....data_enrichment.database_extensions import EnrichmentDatabaseOps # Assuming structure

logger = logging.getLogger(__name__)
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/access-token")

@router.get("/stats")
async def get_stats(
    current_user: schemas.User = Depends(get_current_active_superuser),
    user_service: UserService = Depends(),
    property_service: PropertyService = Depends(),
    broker_service: BrokerService = Depends(),
    # brokerage_service: BrokerageService = Depends() # Assuming BrokerageService exists
):
    """
    Get admin statistics.
    Only accessible by superusers.
    """
    property_count = await property_service.get_property_count()
    broker_count = await broker_service.get_broker_count()
    # brokerage_count = await brokerage_service.get_brokerage_count()
    user_count = await user_service.get_user_count()
    
    return {
        "properties": property_count,
        "brokers": broker_count,
        # "brokerages": brokerage_count,
        "users": user_count
    }

@router.post("/sync/neo4j")
async def sync_neo4j(
    background_tasks: BackgroundTasks,
    current_user: schemas.User = Depends(get_current_active_superuser),
    # neo4j_sync_service: Neo4jSyncService = Depends() # Assuming service exists
):
    """
    Trigger a sync of all data to Neo4j.
    Only accessible by superusers.
    """
    # background_tasks.add_task(neo4j_sync_service.sync_all)
    return {"message": "Neo4j sync started (placeholder)"}

@router.post("/scrape")
async def trigger_scrape(
    background_tasks: BackgroundTasks,
    current_user: schemas.User = Depends(get_current_active_superuser)
):
    """
    Trigger a scrape of property listings.
    Only accessible by superusers.
    """
    return {"message": "Scrape job started (placeholder)"}

# Architecture Diagnostics and Metrics Endpoints

@router.get("/architecture/metrics", response_model=APIResponse[ArchitectureMetrics])
async def get_architecture_metrics(
    current_user: schemas.User = Depends(get_current_active_superuser),
    # metrics_service: MetricsService = Depends() # Assuming service exists
):
    """
    Get current architecture metrics.
    Only accessible by superusers.
    """
    # metrics = await metrics_service.get_architecture_metrics()
    metrics = get_metrics() # Use direct monitoring function for now
    return APIResponse.success_response(data=metrics)

@router.get("/architecture/health")
async def get_architecture_health(
    current_user: schemas.User = Depends(get_current_active_superuser),
    # metrics_service: MetricsService = Depends() # Assuming service exists
):
    """
    Get health indicators for the architecture.
    Only accessible by superusers.
    """
    # health = await metrics_service.get_health_indicators()
    # Placeholder implementation
    health = {
        "status": "healthy",
        "checks": {
            "database_connection": "ok",
            "layer_interaction_errors": 0
        }
    }
    return APIResponse.success_response(data=health)

@router.post("/architecture/run-diagnostics")
async def run_architecture_diagnostics(
    background_tasks: BackgroundTasks,
    current_user: schemas.User = Depends(get_current_active_superuser),
    # metrics_service: MetricsService = Depends() # Assuming service exists
):
    """
    Run all architecture diagnostic scripts.
    This is a long-running operation, so it runs in the background.
    Only accessible by superusers.
    """
    # background_tasks.add_task(metrics_service.run_all_diagnostics)
    return APIResponse.success_response(
        message="Architecture diagnostics started (placeholder)",
        meta={"timestamp": datetime.utcnow().isoformat()}
    )

@router.post("/architecture/run-diagnostic/{script_name}")
async def run_specific_diagnostic(
    script_name: str,
    background_tasks: BackgroundTasks,
    current_user: schemas.User = Depends(get_current_active_superuser),
    # metrics_service: MetricsService = Depends() # Assuming service exists
):
    """
    Run a specific architecture diagnostic script.
    This is a long-running operation, so it runs in the background.
    Only accessible by superusers.
    
    Available script names:
    - test_layer_interactions
    - verify_property_tracking
    - test_architecture_flow
    """
    valid_scripts = ["test_layer_interactions", "verify_property_tracking", "test_architecture_flow"]
    if script_name not in valid_scripts:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid script name. Must be one of: {', '.join(valid_scripts)}"
        )
    
    # background_tasks.add_task(metrics_service.run_diagnostic_script, script_name)
    return APIResponse.success_response(
        message=f"Diagnostic script {script_name} started (placeholder)",
        meta={"timestamp": datetime.utcnow().isoformat()}
    )

@router.get("/architecture/diagnostics/latest")
async def get_latest_diagnostics(
    current_user: schemas.User = Depends(get_current_active_superuser),
    # metrics_service: MetricsService = Depends() # Assuming service exists
):
    """
    Get latest results from diagnostic scripts.
    Only accessible by superusers.
    """
    # latest_results = await metrics_service.get_latest_diagnostic_results()
    # Placeholder implementation
    latest_results = {
        "last_run_timestamp": datetime.utcnow().isoformat(),
        "script_results": {
            "test_layer_interactions": {"status": "passed", "details": "No violations found"}
        }
    }
    return APIResponse.success_response(data=latest_results)

@router.get("/architecture/diagnostics/history")
async def get_diagnostics_history(
    limit: int = Query(10, description="Maximum number of history entries to return"),
    current_user: schemas.User = Depends(get_current_active_superuser),
    # metrics_service: MetricsService = Depends() # Assuming service exists
):
    """
    Get history of diagnostic runs.
    Only accessible by superusers.
    """
    # history = await metrics_service.get_diagnostic_history(limit=limit)
    # Placeholder implementation
    history = [
        {
            "run_id": "diag_run_1",
            "timestamp": (datetime.utcnow() - timedelta(hours=1)).isoformat(),
            "status": "completed",
            "summary": "All diagnostics passed"
        }
    ]
    return APIResponse.success_response(data=history)

@router.post("/architecture/save-metrics")
async def save_current_metrics(
    current_user: schemas.User = Depends(get_current_active_superuser),
    # metrics_service: MetricsService = Depends() # Assuming service exists
):
    """
    Manually trigger saving current metrics to a file.
    Only accessible by superusers.
    """
    # result = await metrics_service.save_current_metrics()
    # Placeholder implementation
    # await save_metrics_to_file() # Using direct function
    result = {"message": "Metrics saved successfully (placeholder)", "filepath": "metrics.json"}
    return APIResponse.success_response(data=result)

# Original missing info endpoints require EnrichmentDatabaseOps and specific schemas
# Commenting out for now as dependencies might not be fully refactored/available

# @router.get("/missing-info/reports", response_model=List[schemas.MissingInfoReport])
# async def get_missing_info_reports(
#     *,
#     db: Session = Depends(get_db),
#     skip: int = 0,
#     limit: int = 10,
#     days: int = 30,
#     current_user: schemas.User = Depends(get_current_active_superuser),
# ) -> Any:
#     """
#     Get a list of missing information reports.
#     Only accessible by superusers.
#     """
#     end_date = datetime.now()
#     start_date = end_date - timedelta(days=days)
#     db_ops = EnrichmentDatabaseOps()
#     try:
#         query = """SELECT id, report_date, total_properties_scanned, properties_with_missing_info, brokers_to_contact
#                    FROM missing_info_reports WHERE report_date BETWEEN $1 AND $2 ORDER BY report_date DESC LIMIT $3 OFFSET $4"""
#         results = await db_ops.execute_raw_query(query, [start_date.isoformat(), end_date.isoformat(), limit, skip])
#         reports = [
#             schemas.MissingInfoReport(
#                 id=row[0], report_date=row[1], total_properties_scanned=row[2],
#                 properties_with_missing_info=row[3], brokers_to_contact=row[4]
#             ) for row in results
#         ]
#         return reports
#     finally:
#         await db_ops.close()

# @router.get("/missing-info/reports/{report_id}", response_model=schemas.MissingInfoReportDetail)
# async def get_missing_info_report_detail(
#     *,
#     report_id: int,
#     current_user: schemas.User = Depends(get_current_active_superuser),
# ) -> Any:
#     """
#     Get the details of a specific missing information report.
#     Only accessible by superusers.
#     """
#     db_ops = EnrichmentDatabaseOps()
#     try:
#         query = """SELECT id, report_date, total_properties_scanned, properties_with_missing_info, brokers_to_contact, properties, properties_by_broker
#                    FROM missing_info_reports WHERE id = $1"""
#         result = await db_ops.execute_raw_query(query, [report_id])
#         if not result or not result[0]:
#             raise HTTPException(status_code=404, detail="Report not found")
#         row = result[0]
#         # Pydantic needs dicts, not JSON strings for nested models
#         properties_data = json.loads(row[5]) if isinstance(row[5], str) else row[5]
#         broker_data = json.loads(row[6]) if isinstance(row[6], str) else row[6]
#         return schemas.MissingInfoReportDetail(
#             id=row[0], report_date=row[1], total_properties_scanned=row[2],
#             properties_with_missing_info=row[3], brokers_to_contact=row[4],
#             properties=[schemas.PropertyWithMissingInfo(**p) for p in properties_data],
#             properties_by_broker={
#                 email: schemas.BrokerEmailInfo(**info)
#                 for email, info in broker_data.items()
#             }
#         )
#     finally:
#         await db_ops.close()

# @router.post("/missing-info/send-emails", response_model=schemas.MissingInfoEmailResult)
# async def send_missing_info_emails(
#     *,
#     report_id: int,
#     broker_emails: Optional[List[str]] = None, # Optionally send to specific brokers
#     current_user: schemas.User = Depends(get_current_active_superuser),
# ) -> Any:
#     """
#     Send emails to brokers listed in a missing info report.
#     Only accessible by superusers.
#     """
#     from app.workers.missing_info_detector import MissingInfoDetector # Import here to avoid circular dependency
#     detector = MissingInfoDetector()
#     db_ops = EnrichmentDatabaseOps()
#     try:
#         # Fetch the report
#         query = "SELECT properties_by_broker FROM missing_info_reports WHERE id = $1"
#         result = await db_ops.execute_raw_query(query, [report_id])
#         if not result or not result[0]:
#             raise HTTPException(status_code=404, detail="Report not found")
#         properties_by_broker = json.loads(result[0][0]) if isinstance(result[0][0], str) else result[0][0]

#         # Filter brokers if specific emails are provided
#         if broker_emails:
#             properties_by_broker = {email: data for email, data in properties_by_broker.items() if email in broker_emails}
        
#         # Create a temporary report structure for the detector
#         temp_report = {"properties_by_broker": properties_by_broker}
        
#         # Generate and send emails
#         email_result = await detector.generate_broker_request_emails(temp_report, send_emails=True)
#         return email_result
#     finally:
#         await db_ops.close()

# @router.get("/missing-info/properties", response_model=List[schemas.PropertyWithMissingInfo])
# async def get_properties_with_missing_info(
#     *,
#     broker_email: Optional[str] = None,
#     days_since_update: int = 30,
#     limit: int = 50,
#     current_user: schemas.User = Depends(get_current_active_superuser),
# ) -> Any:
#     """
#     Get a list of properties with missing information, optionally filtered by broker.
#     Only accessible by superusers.
#     """
#     from app.workers.missing_info_detector import MissingInfoDetector # Import here
#     detector = MissingInfoDetector()
#     try:
#         report = await detector.scan_for_missing_info(days_since_update=days_since_update, limit=limit)
#         properties = report.get("properties", [])
        
#         if broker_email:
#             properties = [p for p in properties if p.get("broker_email") == broker_email]
            
#         return properties
#     finally:
#         await detector.db_ops.close() # Ensure db connection is closed 

@router.post("/trigger-missing-info-detection", status_code=status.HTTP_202_ACCEPTED, response_model=APIResponse[Dict[str, str]])
async def trigger_missing_info_detection_endpoint(
    # ... existing code ...
):
    # Dynamically import here if needed to avoid circular dependencies
    # from ....workers.missing_info_detector import MissingInfoDetector # Import here to avoid circular dependency
    detector = MissingInfoDetector()
    background_tasks.add_task(detector.run_detection)
    # ... existing code ...

@router.post("/test-missing-info-detection/{property_id}", status_code=status.HTTP_200_OK, response_model=APIResponse[Dict[str, Any]])
async def test_missing_info_detection_for_property(
    # ... existing code ...
):
    # Dynamically import here if needed to avoid circular dependencies
    # from ....workers.missing_info_detector import MissingInfoDetector # Import here
    detector = MissingInfoDetector()
    # ... existing code ... 