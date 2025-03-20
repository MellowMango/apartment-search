#!/usr/bin/env python3
import os
import sys
import unittest
from unittest.mock import patch, MagicMock
from celery.result import AsyncResult
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data_enrichment.scheduled_tasks import (
    research_new_properties_task,
    refresh_outdated_research_task,
    deep_research_high_priority_task,
    research_database_maintenance_task,
    research_single_property_task
)

class TestScheduledTasks(unittest.TestCase):
    """Test the scheduled tasks for the deep property research system."""
    
    def test_task_signatures(self):
        """Test that all tasks have the correct signature."""
        # Test research_new_properties_task
        self.assertTrue(hasattr(research_new_properties_task, 'name'))
        self.assertEqual(
            research_new_properties_task.name, 
            'backend.data_enrichment.scheduled_tasks.research_new_properties_task'
        )
        
        # Test refresh_outdated_research_task
        self.assertTrue(hasattr(refresh_outdated_research_task, 'name'))
        self.assertEqual(
            refresh_outdated_research_task.name, 
            'backend.data_enrichment.scheduled_tasks.refresh_outdated_research_task'
        )
        
        # Test deep_research_high_priority_task
        self.assertTrue(hasattr(deep_research_high_priority_task, 'name'))
        self.assertEqual(
            deep_research_high_priority_task.name, 
            'backend.data_enrichment.scheduled_tasks.deep_research_high_priority_task'
        )
        
        # Test research_database_maintenance_task
        self.assertTrue(hasattr(research_database_maintenance_task, 'name'))
        self.assertEqual(
            research_database_maintenance_task.name, 
            'backend.data_enrichment.scheduled_tasks.research_database_maintenance_task'
        )
        
        # Test research_single_property_task
        self.assertTrue(hasattr(research_single_property_task, 'name'))
        self.assertEqual(
            research_single_property_task.name, 
            'backend.data_enrichment.scheduled_tasks.research_single_property_task'
        )
    
    @patch('backend.data_enrichment.scheduled_tasks.EnrichmentDatabaseOps')
    @patch('backend.data_enrichment.scheduled_tasks.PropertyResearcher')
    @patch('backend.data_enrichment.scheduled_tasks.run_async')
    def test_research_new_properties_task(self, mock_run_async, mock_researcher, mock_db_ops):
        """Test the research_new_properties_task."""
        # Mock the get_new_properties function
        mock_run_async.return_value = [
            {"id": "test-1", "address": "123 Test St", "city": "Austin", "state": "TX"},
            {"id": "test-2", "address": "456 Test Ave", "city": "Austin", "state": "TX"}
        ]
        
        # Mock the batch_research_properties function
        mock_run_async.return_value = {
            "test-1": {"modules": {"property_details": {}}},
            "test-2": {"modules": {"property_details": {}}}
        }
        
        # Call the task
        result = research_new_properties_task("basic")
        
        # Verify the result
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertEqual(result['status'], 'success')
    
    def test_manual_task_invocation(self):
        """Test manual invocation of tasks for development purposes."""
        # This is a placeholder test that doesn't actually run the tasks
        # It's here to document how to manually invoke tasks for testing
        print("\nTo manually invoke tasks for testing, use:")
        print("research_new_properties_task.delay('basic')")
        print("refresh_outdated_research_task.delay('standard', 7)")
        print("deep_research_high_priority_task.delay()")
        print("research_database_maintenance_task.delay()")
        print("research_single_property_task.delay('some-property-id', 'basic')")
        
        # This test always passes
        self.assertTrue(True)

def run_tests():
    """Run the scheduled tasks tests."""
    unittest.main()

if __name__ == "__main__":
    run_tests() 