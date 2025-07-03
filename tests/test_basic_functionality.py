"""
Basic functionality tests for Lynnapse.
"""

import pytest
import asyncio
from pathlib import Path

from lynnapse.config import get_settings
from lynnapse.models import Program, Faculty, LabSite, ScrapeJob
from lynnapse.db import MongoDBClient


def test_settings_load():
    """Test that settings load correctly."""
    settings = get_settings()
    assert settings.app_name == "Lynnapse"
    assert settings.mongodb_database == "lynnapse"



def test_program_model():
    """Test Program model validation."""
    program_data = {
        "university_name": "University of Arizona",
        "program_name": "Psychology",
        "program_type": "graduate",
        "department": "Psychology",
        "college": "College of Science",
        "program_url": "https://psychology.arizona.edu/graduate",
        "source_url": "https://psychology.arizona.edu"
    }
    
    program = Program(**program_data)
    assert program.university_name == "University of Arizona"
    assert program.program_name == "Psychology"
    assert program.program_type == "graduate"


def test_faculty_model():
    """Test Faculty model validation."""
    faculty_data = {
        "program_id": "507f1f77bcf86cd799439011",
        "name": "Dr. Test Professor",
        "title": "Professor",
        "department": "Psychology",
        "college": "College of Science",
        "profile_url": "https://psychology.arizona.edu/people/test-professor",
        "source_url": "https://psychology.arizona.edu/people/faculty"
    }
    
    faculty = Faculty(**faculty_data)
    assert faculty.name == "Dr. Test Professor"
    assert faculty.title == "Professor"
    assert faculty.department == "Psychology"


def test_lab_site_model():
    """Test LabSite model validation."""
    lab_data = {
        "faculty_id": "507f1f77bcf86cd799439012",
        "program_id": "507f1f77bcf86cd799439011",
        "lab_name": "Test Laboratory",
        "lab_url": "https://testlab.arizona.edu",
        "principal_investigator": "Dr. Test Professor",
        "scraper_method": "playwright",
        "source_url": "https://testlab.arizona.edu"
    }
    
    lab_site = LabSite(**lab_data)
    assert lab_site.lab_name == "Test Laboratory"
    assert lab_site.principal_investigator == "Dr. Test Professor"
    assert lab_site.scraper_method == "playwright"


def test_scrape_job_model():
    """Test ScrapeJob model and methods."""
    job_data = {
        "job_name": "test_scrape_job",
        "job_type": "faculty",
        "target_url": "https://psychology.arizona.edu/people/faculty",
        "university_name": "University of Arizona"
    }
    
    scrape_job = ScrapeJob(**job_data)
    assert scrape_job.job_name == "test_scrape_job"
    assert scrape_job.status == "pending"
    assert scrape_job.progress == 0.0
    
    # Test status methods
    scrape_job.mark_started()
    assert scrape_job.status == "running"
    assert scrape_job.started_at is not None
    
    scrape_job.update_progress(5, 10)
    assert scrape_job.progress == 50.0
    
    scrape_job.mark_completed()
    assert scrape_job.status == "completed"
    assert scrape_job.completed_at is not None


@pytest.mark.asyncio
async def test_mongodb_client():
    """Test MongoDB client connection (if available)."""
    try:
        client = MongoDBClient("mongodb://localhost:27017")
        await client.connect()
        
        # Test health check
        healthy = await client.health_check()
        assert healthy
        
        await client.disconnect()
        
    except Exception as e:
        # MongoDB might not be available in test environment
        pytest.skip(f"MongoDB not available: {e}")




if __name__ == "__main__":
    pytest.main([__file__]) 