"""
ScrapeJob model for tracking scraping jobs and their status.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
from bson import ObjectId


class JobStatus(str, Enum):
    """Enumeration of possible job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ScrapeJob(BaseModel):
    """Model for tracking scraping jobs."""
    
    id: Optional[str] = Field(None, alias="_id")
    
    # Job identification
    job_name: str = Field(..., description="Name/identifier for the job")
    job_type: str = Field(..., description="Type of job (program, faculty, lab_site)")
    prefect_flow_run_id: Optional[str] = Field(None, description="Prefect flow run ID")
    
    # Target information
    target_url: str = Field(..., description="URL being scraped")
    university_name: str = Field(..., description="University being scraped")
    program_name: Optional[str] = Field(None, description="Program being scraped")
    
    # Job configuration
    scraper_config: Dict[str, Any] = Field(default_factory=dict, description="Scraper configuration")
    retry_attempts: int = Field(default=0, description="Number of retry attempts")
    max_retries: int = Field(default=3, description="Maximum retry attempts")
    
    # Status tracking
    status: JobStatus = Field(default=JobStatus.PENDING, description="Current job status")
    progress: float = Field(default=0.0, description="Job progress percentage (0-100)")
    
    # Timing information
    scheduled_at: Optional[datetime] = Field(None, description="When job was scheduled")
    started_at: Optional[datetime] = Field(None, description="When job started")
    completed_at: Optional[datetime] = Field(None, description="When job completed")
    duration_seconds: Optional[float] = Field(None, description="Job duration in seconds")
    
    # Results tracking
    items_scraped: int = Field(default=0, description="Number of items successfully scraped")
    items_failed: int = Field(default=0, description="Number of items that failed")
    total_items: Optional[int] = Field(None, description="Total expected items")
    
    # Error tracking
    error_message: Optional[str] = Field(None, description="Error message if job failed")
    error_traceback: Optional[str] = Field(None, description="Full error traceback")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    
    # Scraping method tracking
    methods_used: List[str] = Field(default_factory=list, description="Scraping methods used")
    method_success_rates: Dict[str, float] = Field(default_factory=dict, description="Success rate by method")
    
    # Output information
    output_files: List[str] = Field(default_factory=list, description="Generated output files")
    db_collections_updated: List[str] = Field(default_factory=list, description="Database collections updated")
    
    # Resource usage
    memory_usage_mb: Optional[float] = Field(None, description="Peak memory usage in MB")
    cpu_time_seconds: Optional[float] = Field(None, description="CPU time used in seconds")
    
    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Additional data
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional job metadata")
    
    class Config:
        populate_by_name = True
        json_encoders = {ObjectId: str}
        use_enum_values = True
        schema_extra = {
            "example": {
                "job_name": "uarizona_psychology_faculty_scrape",
                "job_type": "faculty",
                "target_url": "https://psychology.arizona.edu/people/faculty",
                "university_name": "University of Arizona",
                "program_name": "Psychology",
                "status": "completed",
                "progress": 100.0,
                "items_scraped": 45,
                "items_failed": 2,
                "total_items": 47,
                "methods_used": ["playwright", "requests"],
                "method_success_rates": {"playwright": 0.95, "requests": 0.85},
                "duration_seconds": 125.5
            }
        }
    
    def update_progress(self, current: int, total: int) -> None:
        """Update job progress."""
        self.progress = (current / total) * 100.0 if total > 0 else 0.0
        self.updated_at = datetime.utcnow()
    
    def mark_started(self) -> None:
        """Mark job as started."""
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def mark_completed(self) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
    
    def mark_failed(self, error_message: str, traceback: Optional[str] = None) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.error_message = error_message
        self.error_traceback = traceback
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        if self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds() 