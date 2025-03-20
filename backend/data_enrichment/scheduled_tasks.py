import os
import time
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from celery import Celery
from celery.schedules import crontab

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='deep_research_tasks.log'
)
logger = logging.getLogger(__name__)

# Import required modules
from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
from backend.data_enrichment.config import DB_CONFIG

# Create Celery app
celery_app = Celery('deep_research_tasks')

# Configure Celery to use PostgreSQL (Supabase) as both broker and result backend
# This follows the tech stack specification: "Using Supabase PostgreSQL as both broker and result backend"
celery_app.conf.update(
    # Use PostgreSQL for broker and result backend
    broker_url=os.environ.get(
        'CELERY_BROKER_URL', 
        f"db+postgresql://{os.environ.get('SUPABASE_DB_USER', 'postgres')}:"
        f"{os.environ.get('SUPABASE_DB_PASSWORD', '')}@"
        f"{os.environ.get('SUPABASE_DB_HOST', 'localhost')}:"
        f"{os.environ.get('SUPABASE_DB_PORT', '5432')}/"
        f"{os.environ.get('SUPABASE_DB_NAME', 'postgres')}"
    ),
    result_backend=os.environ.get(
        'CELERY_RESULT_BACKEND', 
        f"db+postgresql://{os.environ.get('SUPABASE_DB_USER', 'postgres')}:"
        f"{os.environ.get('SUPABASE_DB_PASSWORD', '')}@"
        f"{os.environ.get('SUPABASE_DB_HOST', 'localhost')}:"
        f"{os.environ.get('SUPABASE_DB_PORT', '5432')}/"
        f"{os.environ.get('SUPABASE_DB_NAME', 'postgres')}"
    ),
    # Additional configurations
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    # Task settings
    task_time_limit=3600,  # 1 hour max runtime
    task_soft_time_limit=3000,  # 50 minutes soft limit
    worker_max_tasks_per_child=200,  # Restart worker after 200 tasks
    worker_prefetch_multiplier=1,  # Don't prefetch tasks (better for long-running tasks)
)

# Configure periodic tasks
celery_app.conf.beat_schedule = {
    'research-new-properties-daily': {
        'task': 'backend.data_enrichment.scheduled_tasks.research_new_properties_task',
        'schedule': crontab(hour=1, minute=0),  # Run at 1:00 AM every day
        'args': ('standard',),
    },
    'refresh-outdated-research-weekly': {
        'task': 'backend.data_enrichment.scheduled_tasks.refresh_outdated_research_task',
        'schedule': crontab(day_of_week=0, hour=2, minute=0),  # Run at 2:00 AM every Sunday
        'args': ('standard', 30),  # Refresh research older than 30 days
    },
    'deep-research-high-priority-monthly': {
        'task': 'backend.data_enrichment.scheduled_tasks.deep_research_high_priority_task',
        'schedule': crontab(day_of_month=1, hour=3, minute=0),  # Run at 3:00 AM on the 1st of each month
        'args': (),
    },
    'research-database-maintenance-weekly': {
        'task': 'backend.data_enrichment.scheduled_tasks.research_database_maintenance_task',
        'schedule': crontab(day_of_week=6, hour=4, minute=0),  # Run at 4:00 AM every Saturday
        'args': (),
    },
}

# Helper to run async tasks in Celery
def run_async(coroutine):
    """Run an async coroutine within a Celery task."""
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(coroutine)

@celery_app.task(bind=True, name='backend.data_enrichment.scheduled_tasks.research_new_properties_task')
def research_new_properties_task(self, research_depth: str = 'standard'):
    """
    Research new properties added in the last 24 hours.
    
    Args:
        research_depth: Depth of research to perform (default: standard)
    """
    try:
        logger.info(f"Starting research of new properties with {research_depth} depth")
        
        # Initialize components
        db_ops = EnrichmentDatabaseOps()
        researcher = PropertyResearcher(db_ops=db_ops)
        
        # Get properties added in the last 24 hours
        properties = run_async(get_new_properties(db_ops, hours=24))
        
        if not properties:
            logger.info("No new properties found in the last 24 hours")
            return {"status": "success", "message": "No new properties found"}
        
        logger.info(f"Found {len(properties)} new properties to research")
        
        # Research properties
        results = run_async(researcher.batch_research_properties(
            properties=properties,
            research_depth=research_depth,
            concurrency=3,
            force_refresh=False
        ))
        
        # Count successful operations
        success_count = len([r for r in results.values() if "error" not in r])
        failed_count = len(results) - success_count
        
        logger.info(f"Completed research of new properties. Success: {success_count}, Failed: {failed_count}")
        
        return {
            "status": "success", 
            "message": f"Researched {len(properties)} new properties",
            "details": {
                "success_count": success_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error in research_new_properties_task: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # Ensure connections are closed
        if 'db_ops' in locals():
            db_ops.close()

@celery_app.task(bind=True, name='backend.data_enrichment.scheduled_tasks.refresh_outdated_research_task')
def refresh_outdated_research_task(self, research_depth: str = 'standard', days_threshold: int = 30):
    """
    Refresh research for properties with outdated results.
    
    Args:
        research_depth: Depth of research to perform (default: standard)
        days_threshold: Consider research outdated after this many days (default: 30)
    """
    try:
        logger.info(f"Starting refresh of outdated {research_depth} research (>{days_threshold} days old)")
        
        # Initialize components
        db_ops = EnrichmentDatabaseOps()
        researcher = PropertyResearcher(db_ops=db_ops)
        
        # Get properties with outdated research
        properties = run_async(db_ops.get_properties_needing_research(
            limit=50,  # Process in batches of 50
            research_depth=research_depth,
            days_threshold=days_threshold
        ))
        
        if not properties:
            logger.info(f"No properties found with outdated {research_depth} research")
            return {"status": "success", "message": "No outdated research found"}
        
        logger.info(f"Found {len(properties)} properties with outdated research to refresh")
        
        # Research properties
        results = run_async(researcher.batch_research_properties(
            properties=properties,
            research_depth=research_depth,
            concurrency=3,
            force_refresh=True  # Force refresh since we're explicitly updating
        ))
        
        # Count successful operations
        success_count = len([r for r in results.values() if "error" not in r])
        failed_count = len(results) - success_count
        
        logger.info(f"Completed refresh of outdated research. Success: {success_count}, Failed: {failed_count}")
        
        return {
            "status": "success", 
            "message": f"Refreshed research for {len(properties)} properties",
            "details": {
                "success_count": success_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error in refresh_outdated_research_task: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # Ensure connections are closed
        if 'db_ops' in locals():
            db_ops.close()

@celery_app.task(bind=True, name='backend.data_enrichment.scheduled_tasks.deep_research_high_priority_task')
def deep_research_high_priority_task(self):
    """
    Perform comprehensive research on high-priority properties.
    
    High-priority properties are identified based on criteria like:
    - Recently updated
    - High user interest (e.g., most viewed)
    - Properties in hot markets
    """
    try:
        logger.info("Starting comprehensive research on high-priority properties")
        
        # Initialize components
        db_ops = EnrichmentDatabaseOps()
        researcher = PropertyResearcher(db_ops=db_ops)
        
        # Get high-priority properties
        properties = run_async(get_high_priority_properties(db_ops))
        
        if not properties:
            logger.info("No high-priority properties found")
            return {"status": "success", "message": "No high-priority properties found"}
        
        logger.info(f"Found {len(properties)} high-priority properties to research")
        
        # Research properties with comprehensive depth
        results = run_async(researcher.batch_research_properties(
            properties=properties,
            research_depth='comprehensive',  # Use comprehensive depth for high-priority
            concurrency=2,  # Lower concurrency for more intensive research
            force_refresh=True
        ))
        
        # Count successful operations
        success_count = len([r for r in results.values() if "error" not in r])
        failed_count = len(results) - success_count
        
        logger.info(f"Completed comprehensive research. Success: {success_count}, Failed: {failed_count}")
        
        return {
            "status": "success", 
            "message": f"Performed comprehensive research on {len(properties)} high-priority properties",
            "details": {
                "success_count": success_count,
                "failed_count": failed_count
            }
        }
        
    except Exception as e:
        logger.error(f"Error in deep_research_high_priority_task: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # Ensure connections are closed
        if 'db_ops' in locals():
            db_ops.close()

@celery_app.task(bind=True, name='backend.data_enrichment.scheduled_tasks.research_database_maintenance_task')
def research_database_maintenance_task(self):
    """
    Perform maintenance tasks on the research database.
    
    Tasks include:
    - Clean up orphaned research records
    - Update statistics
    - Optimize database performance
    """
    try:
        logger.info("Starting research database maintenance task")
        
        # Initialize database operations
        db_ops = EnrichmentDatabaseOps()
        
        # Perform maintenance tasks
        
        # 1. Clean up orphaned research records
        orphaned_count = run_async(clean_orphaned_research(db_ops))
        logger.info(f"Cleaned up {orphaned_count} orphaned research records")
        
        # 2. Generate and log statistics
        stats = run_async(db_ops.get_research_summary_stats())
        logger.info(f"Research database statistics: {stats}")
        
        return {
            "status": "success", 
            "message": "Database maintenance completed",
            "details": {
                "orphaned_records_cleaned": orphaned_count,
                "total_research_records": stats.get('total_researched_properties', 0),
                "outdated_records": stats.get('outdated_research', 0)
            }
        }
        
    except Exception as e:
        logger.error(f"Error in research_database_maintenance_task: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # Ensure connections are closed
        if 'db_ops' in locals():
            db_ops.close()

@celery_app.task(bind=True, name='backend.data_enrichment.scheduled_tasks.research_single_property_task')
def research_single_property_task(self, property_id: str, research_depth: str = 'standard'):
    """
    Research a single property by its ID.
    
    Args:
        property_id: ID of the property to research
        research_depth: Depth of research to perform
    """
    try:
        logger.info(f"Starting {research_depth} research for property {property_id}")
        
        # Initialize components
        db_ops = EnrichmentDatabaseOps()
        researcher = PropertyResearcher(db_ops=db_ops)
        
        # Get property data
        properties = run_async(db_ops.get_properties_needing_research(
            limit=50,  # Search among a reasonable number
            research_depth=research_depth,
            days_threshold=0  # Ignore threshold since we're forcing specific property
        ))
        
        # Find the specific property
        property_data = None
        for prop in properties:
            if prop.get("id") == property_id:
                property_data = prop
                break
        
        if not property_data:
            logger.error(f"Property with ID {property_id} not found")
            return {"status": "error", "message": f"Property not found: {property_id}"}
        
        # Research the property
        result = run_async(researcher.research_property(
            property_data=property_data,
            research_depth=research_depth,
            force_refresh=True
        ))
        
        if "error" in result:
            logger.error(f"Error researching property {property_id}: {result['error']}")
            return {"status": "error", "message": result["error"]}
        
        logger.info(f"Completed {research_depth} research for property {property_id}")
        
        return {
            "status": "success", 
            "message": f"Researched property {property_id}",
            "research_date": result.get("research_date"),
            "modules": list(result.get("modules", {}).keys())
        }
        
    except Exception as e:
        logger.error(f"Error in research_single_property_task: {str(e)}")
        return {"status": "error", "message": str(e)}
    finally:
        # Ensure connections are closed
        if 'db_ops' in locals():
            db_ops.close()

# Helper functions

async def get_new_properties(db_ops: EnrichmentDatabaseOps, hours: int = 24) -> List[Dict[str, Any]]:
    """Get properties added within the specified hours."""
    if not db_ops.supabase:
        logger.error("Cannot get new properties: Supabase client not initialized")
        return []
    
    try:
        # Calculate threshold timestamp
        threshold_time = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        # Query for properties created after threshold
        query = f"""
        SELECT * FROM {DB_CONFIG["supabase"]["property_table"]}
        WHERE created_at > '{threshold_time}'
        ORDER BY created_at DESC
        """
        
        result = db_ops.supabase.rpc('exec_sql', {'query': query}).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error getting new properties: {str(e)}")
        return []

async def get_high_priority_properties(db_ops: EnrichmentDatabaseOps, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get high-priority properties for deep research.
    
    Criteria:
    1. Recently updated properties
    2. Properties with high view counts (if available)
    3. Properties in hot markets
    """
    if not db_ops.supabase:
        logger.error("Cannot get high priority properties: Supabase client not initialized")
        return []
    
    try:
        # For now, use a simple query to get recently updated properties
        # In a real implementation, this would incorporate more criteria
        
        # Calculate threshold timestamp (30 days)
        threshold_time = (datetime.now() - timedelta(days=30)).isoformat()
        
        # Query for recently updated properties
        query = f"""
        SELECT p.* FROM {DB_CONFIG["supabase"]["property_table"]} p
        LEFT JOIN {DB_CONFIG["supabase"]["research_table"]} r 
          ON p.id = r.property_id AND r.research_depth = 'comprehensive'
        WHERE p.updated_at > '{threshold_time}'
        AND (r.id IS NULL OR r.updated_at < p.updated_at)
        ORDER BY p.updated_at DESC
        LIMIT {limit}
        """
        
        result = db_ops.supabase.rpc('exec_sql', {'query': query}).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error getting high priority properties: {str(e)}")
        return []

async def clean_orphaned_research(db_ops: EnrichmentDatabaseOps) -> int:
    """
    Clean up orphaned research records.
    
    Returns:
        Number of orphaned records removed
    """
    if not db_ops.supabase:
        logger.error("Cannot clean orphaned research: Supabase client not initialized")
        return 0
    
    try:
        # Query to find orphaned research records
        query = f"""
        DELETE FROM {DB_CONFIG["supabase"]["research_table"]} r
        WHERE NOT EXISTS (
            SELECT 1 FROM {DB_CONFIG["supabase"]["property_table"]} p
            WHERE p.id = r.property_id
        )
        RETURNING id
        """
        
        result = db_ops.supabase.rpc('exec_sql', {'query': query}).execute()
        
        # Also clean up Neo4j if available
        if db_ops.neo4j_driver:
            with db_ops.neo4j_driver.session(database=db_ops.neo4j_database) as session:
                # Delete orphaned PropertyResearch nodes
                cypher = """
                MATCH (r:PropertyResearch)
                WHERE NOT EXISTS {
                    MATCH (p:Property)-[:HAS_RESEARCH]->(r)
                }
                DETACH DELETE r
                RETURN count(r) as deleted_count
                """
                
                neo4j_result = session.run(cypher)
                neo4j_deleted = neo4j_result.single()["deleted_count"] if neo4j_result.single() else 0
                
                logger.info(f"Cleaned up {neo4j_deleted} orphaned research nodes in Neo4j")
        
        return len(result.data)
    except Exception as e:
        logger.error(f"Error cleaning orphaned research: {str(e)}")
        return 0

# Manual test function for development
def test_tasks():
    """Run tasks manually for testing."""
    # Initialize database connections
    db_ops = EnrichmentDatabaseOps()
    
    # Test each task
    print("Testing research_new_properties_task:")
    result = research_new_properties_task('basic')
    print(result)
    
    print("\nTesting refresh_outdated_research_task:")
    result = refresh_outdated_research_task('standard', 7)  # Test with 7 days threshold
    print(result)
    
    print("\nTesting deep_research_high_priority_task:")
    result = deep_research_high_priority_task()
    print(result)
    
    print("\nTesting research_database_maintenance_task:")
    result = research_database_maintenance_task()
    print(result)
    
    # Clean up
    db_ops.close()

if __name__ == "__main__":
    # When run directly, test the tasks
    test_tasks()
