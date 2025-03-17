#!/usr/bin/env python3
"""
Scheduled Data Cleaning Tasks

This module defines Celery tasks for scheduled data cleaning operations.
"""

import logging
import os
import json
import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path

from celery import Celery
from celery.schedules import crontab

from backend.data_cleaning.data_cleaner import DataCleaner
from backend.data_cleaning.database.db_operations import DatabaseOperations

# Configure logging
logger = logging.getLogger(__name__)

# Initialize Celery app
celery_app = Celery('data_cleaning_tasks')

# Load Celery configuration
celery_app.conf.update(
    broker_url=os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
    result_backend=os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0'),
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

# Define periodic tasks
celery_app.conf.beat_schedule = {
    'clean-all-properties-daily': {
        'task': 'backend.data_cleaning.scheduled.cleaning_tasks.clean_all_properties',
        'schedule': crontab(hour=2, minute=0),  # Run at 2:00 AM every day
        'args': (),
    },
    'clean-new-properties-hourly': {
        'task': 'backend.data_cleaning.scheduled.cleaning_tasks.clean_new_properties',
        'schedule': crontab(minute=0),  # Run every hour at minute 0
        'args': (),
    },
}

@celery_app.task(name='backend.data_cleaning.scheduled.cleaning_tasks.clean_all_properties')
def clean_all_properties() -> Dict[str, Any]:
    """
    Celery task to clean all properties in the database.
    
    Returns:
        Dictionary with cleaning statistics
    """
    logger.info("Starting scheduled task to clean all properties")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Fetch all properties from the database
    properties = db_ops.fetch_all_properties()
    
    if not properties:
        logger.warning("No properties found in database")
        return {'error': 'No properties found in database'}
    
    # Initialize data cleaner
    data_cleaner = DataCleaner()
    
    # Clean the properties
    cleaned_properties, cleaning_stats = data_cleaner.clean_properties(properties)
    
    # Save cleaning log to database
    db_ops.save_cleaning_log(cleaning_stats)
    
    # Update database with cleaned properties
    update_database_with_cleaned_properties(db_ops, properties, cleaned_properties)
    
    logger.info(f"Completed scheduled task to clean all properties: {cleaning_stats['final_count']} properties cleaned")
    
    return cleaning_stats

@celery_app.task(name='backend.data_cleaning.scheduled.cleaning_tasks.clean_new_properties')
def clean_new_properties() -> Dict[str, Any]:
    """
    Celery task to clean new properties added in the last hour.
    
    Returns:
        Dictionary with cleaning statistics
    """
    logger.info("Starting scheduled task to clean new properties")
    
    # Initialize database operations
    db_ops = DatabaseOperations()
    
    # Calculate timestamp for 1 hour ago
    one_hour_ago = (datetime.datetime.now() - datetime.timedelta(hours=1)).isoformat()
    
    # Fetch new properties from the database
    try:
        # Assuming there's a created_at field in the properties table
        response = db_ops.supabase_client.table("properties").select("*").gte("created_at", one_hour_ago).execute()
        properties = response.data
        
        logger.info(f"Found {len(properties)} new properties added in the last hour")
    except Exception as e:
        logger.error(f"Error fetching new properties: {e}")
        return {'error': f'Error fetching new properties: {str(e)}'}
    
    if not properties:
        logger.info("No new properties found")
        return {'message': 'No new properties found'}
    
    # Initialize data cleaner
    data_cleaner = DataCleaner()
    
    # Clean the properties
    cleaned_properties, cleaning_stats = data_cleaner.clean_properties(properties)
    
    # Save cleaning log to database
    db_ops.save_cleaning_log(cleaning_stats)
    
    # Update database with cleaned properties
    update_database_with_cleaned_properties(db_ops, properties, cleaned_properties)
    
    logger.info(f"Completed scheduled task to clean new properties: {cleaning_stats['final_count']} properties cleaned")
    
    return cleaning_stats

def update_database_with_cleaned_properties(db_ops: DatabaseOperations, 
                                           original_properties: List[Dict[str, Any]], 
                                           cleaned_properties: List[Dict[str, Any]]) -> bool:
    """
    Update the database with cleaned properties.
    
    Args:
        db_ops: DatabaseOperations instance
        original_properties: List of original property dictionaries
        cleaned_properties: List of cleaned property dictionaries
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        logger.info("Updating database with cleaned properties")
        
        # Create a map of original property IDs to properties
        original_map = {prop.get('id'): prop for prop in original_properties if prop.get('id')}
        
        # Create a map of cleaned property IDs to properties
        cleaned_map = {prop.get('id'): prop for prop in cleaned_properties if prop.get('id')}
        
        # Track statistics
        updated_count = 0
        error_count = 0
        
        # Update each property in the database
        for prop_id, cleaned_prop in cleaned_map.items():
            # Skip properties without IDs
            if not prop_id:
                continue
                
            # Update the property in the database
            success = db_ops.update_property(prop_id, cleaned_prop)
            
            if success:
                updated_count += 1
            else:
                error_count += 1
        
        logger.info(f"Database update complete: {updated_count} properties updated, {error_count} errors")
        return updated_count > 0
    except Exception as e:
        logger.error(f"Error updating database with cleaned properties: {e}")
        return False 