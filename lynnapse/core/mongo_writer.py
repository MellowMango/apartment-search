"""
MongoWriter - Database operations and persistence layer.

Handles all MongoDB operations for the Lynnapse scraping system
with proper error handling, upsert logic, and data validation.
"""

import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Union
from bson import ObjectId

from lynnapse.db import get_client
from lynnapse.models import Program, Faculty, LabSite, ScrapeJob


logger = logging.getLogger(__name__)


class MongoWriter:
    """Handles all MongoDB write operations for scraped data."""
    
    def __init__(self):
        """Initialize the MongoDB writer."""
        self.client = None
        self.database = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self) -> None:
        """Connect to MongoDB."""
        try:
            self.client = await get_client()
            self.database = await self.client.get_database()
            logger.info("MongoWriter connected to database")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    async def close(self) -> None:
        """Close MongoDB connection."""
        if self.client:
            await self.client.close()
            logger.info("MongoWriter disconnected from database")
    
    async def ensure_connection(self) -> None:
        """Ensure database connection is active."""
        if not self.database:
            await self.connect()
    
    async def upsert_program(self, program_data: Dict[str, Any]) -> str:
        """
        Upsert a program record.
        
        Args:
            program_data: Program data dictionary
            
        Returns:
            Program ID (ObjectId as string)
        """
        await self.ensure_connection()
        
        try:
            # Validate data using Pydantic model
            program = Program(**program_data)
            
            # Create composite key for upsert
            filter_key = {
                "university_name": program.university_name,
                "program_name": program.program_name,
                "department": program.department
            }
            
            # Prepare update document
            update_doc = {
                "$set": {
                    **program.dict(exclude={"id"}),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            }
            
            # Perform upsert
            result = await self.database.programs.update_one(
                filter_key,
                update_doc,
                upsert=True
            )
            
            if result.upserted_id:
                program_id = str(result.upserted_id)
                logger.info(f"Inserted new program: {program.program_name}")
            else:
                # Find the existing document to get its ID
                existing = await self.database.programs.find_one(filter_key)
                program_id = str(existing["_id"])
                logger.info(f"Updated existing program: {program.program_name}")
            
            return program_id
            
        except Exception as e:
            logger.error(f"Failed to upsert program: {e}")
            raise
    
    async def upsert_faculty(self, faculty_data: Dict[str, Any]) -> str:
        """
        Upsert a faculty record.
        
        Args:
            faculty_data: Faculty data dictionary
            
        Returns:
            Faculty ID (ObjectId as string)
        """
        await self.ensure_connection()
        
        try:
            # Validate data using Pydantic model
            faculty = Faculty(**faculty_data)
            
            # Create composite key for upsert
            filter_key = {
                "name": faculty.name,
                "program_id": faculty.program_id
            }
            
            # Prepare update document
            update_doc = {
                "$set": {
                    **faculty.dict(exclude={"id"}),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            }
            
            # Perform upsert
            result = await self.database.faculty.update_one(
                filter_key,
                update_doc,
                upsert=True
            )
            
            if result.upserted_id:
                faculty_id = str(result.upserted_id)
                logger.info(f"Inserted new faculty: {faculty.name}")
            else:
                # Find the existing document to get its ID
                existing = await self.database.faculty.find_one(filter_key)
                faculty_id = str(existing["_id"])
                logger.info(f"Updated existing faculty: {faculty.name}")
            
            return faculty_id
            
        except Exception as e:
            logger.error(f"Failed to upsert faculty: {e}")
            raise
    
    async def upsert_lab_site(self, lab_data: Dict[str, Any]) -> str:
        """
        Upsert a lab site record.
        
        Args:
            lab_data: Lab site data dictionary
            
        Returns:
            Lab site ID (ObjectId as string)
        """
        await self.ensure_connection()
        
        try:
            # Validate data using Pydantic model
            lab_site = LabSite(**lab_data)
            
            # Create composite key for upsert
            filter_key = {
                "faculty_id": lab_site.faculty_id,
                "lab_url": lab_site.lab_url
            }
            
            # Prepare update document
            update_doc = {
                "$set": {
                    **lab_site.dict(exclude={"id"}),
                    "updated_at": datetime.utcnow()
                },
                "$setOnInsert": {
                    "created_at": datetime.utcnow()
                }
            }
            
            # Perform upsert
            result = await self.database.lab_sites.update_one(
                filter_key,
                update_doc,
                upsert=True
            )
            
            if result.upserted_id:
                lab_id = str(result.upserted_id)
                logger.info(f"Inserted new lab site: {lab_site.lab_name}")
            else:
                # Find the existing document to get its ID
                existing = await self.database.lab_sites.find_one(filter_key)
                lab_id = str(existing["_id"])
                logger.info(f"Updated existing lab site: {lab_site.lab_name}")
            
            return lab_id
            
        except Exception as e:
            logger.error(f"Failed to upsert lab site: {e}")
            raise
    
    async def create_scrape_job(self, job_data: Dict[str, Any]) -> str:
        """
        Create a new scrape job record.
        
        Args:
            job_data: Scrape job data dictionary
            
        Returns:
            Scrape job ID (ObjectId as string)
        """
        await self.ensure_connection()
        
        try:
            # Validate data using Pydantic model
            scrape_job = ScrapeJob(**job_data)
            
            # Insert the job
            result = await self.database.scrape_jobs.insert_one(
                scrape_job.dict(exclude={"id"})
            )
            
            job_id = str(result.inserted_id)
            logger.info(f"Created scrape job: {scrape_job.job_name}")
            
            return job_id
            
        except Exception as e:
            logger.error(f"Failed to create scrape job: {e}")
            raise
    
    async def update_scrape_job(self, job_id: str, updates: Dict[str, Any]) -> None:
        """
        Update an existing scrape job.
        
        Args:
            job_id: Job ID to update
            updates: Update data dictionary
        """
        await self.ensure_connection()
        
        try:
            # Add timestamp to updates
            updates["updated_at"] = datetime.utcnow()
            
            # Update the job
            result = await self.database.scrape_jobs.update_one(
                {"_id": ObjectId(job_id)},
                {"$set": updates}
            )
            
            if result.modified_count > 0:
                logger.info(f"Updated scrape job: {job_id}")
            else:
                logger.warning(f"No scrape job found with ID: {job_id}")
                
        except Exception as e:
            logger.error(f"Failed to update scrape job {job_id}: {e}")
            raise
    
    async def bulk_upsert_faculty(self, faculty_list: List[Dict[str, Any]], 
                                 program_id: str) -> List[str]:
        """
        Bulk upsert faculty records for better performance.
        
        Args:
            faculty_list: List of faculty data dictionaries
            program_id: Program ID to associate with faculty
            
        Returns:
            List of faculty IDs
        """
        await self.ensure_connection()
        
        faculty_ids = []
        
        try:
            # Process each faculty member
            for faculty_data in faculty_list:
                faculty_data["program_id"] = program_id
                faculty_id = await self.upsert_faculty(faculty_data)
                faculty_ids.append(faculty_id)
            
            logger.info(f"Bulk upserted {len(faculty_ids)} faculty records")
            return faculty_ids
            
        except Exception as e:
            logger.error(f"Failed to bulk upsert faculty: {e}")
            raise
    
    async def get_program_by_name(self, university_name: str, 
                                 program_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a program by university and program name.
        
        Args:
            university_name: University name
            program_name: Program name
            
        Returns:
            Program document or None
        """
        await self.ensure_connection()
        
        try:
            program = await self.database.programs.find_one({
                "university_name": university_name,
                "program_name": program_name
            })
            
            if program:
                program["id"] = str(program["_id"])
                
            return program
            
        except Exception as e:
            logger.error(f"Failed to get program: {e}")
            raise
    
    async def get_faculty_by_program(self, program_id: str) -> List[Dict[str, Any]]:
        """
        Get all faculty for a specific program.
        
        Args:
            program_id: Program ID
            
        Returns:
            List of faculty documents
        """
        await self.ensure_connection()
        
        try:
            cursor = self.database.faculty.find({"program_id": program_id})
            faculty_list = []
            
            async for faculty in cursor:
                faculty["id"] = str(faculty["_id"])
                faculty_list.append(faculty)
            
            return faculty_list
            
        except Exception as e:
            logger.error(f"Failed to get faculty for program {program_id}: {e}")
            raise
    
    async def get_lab_sites_by_faculty(self, faculty_id: str) -> List[Dict[str, Any]]:
        """
        Get all lab sites for a specific faculty member.
        
        Args:
            faculty_id: Faculty ID
            
        Returns:
            List of lab site documents
        """
        await self.ensure_connection()
        
        try:
            cursor = self.database.lab_sites.find({"faculty_id": faculty_id})
            lab_sites = []
            
            async for lab_site in cursor:
                lab_site["id"] = str(lab_site["_id"])
                lab_sites.append(lab_site)
            
            return lab_sites
            
        except Exception as e:
            logger.error(f"Failed to get lab sites for faculty {faculty_id}: {e}")
            raise
    
    async def get_scraping_statistics(self, university_name: str) -> Dict[str, Any]:
        """
        Get scraping statistics for a university.
        
        Args:
            university_name: University name
            
        Returns:
            Statistics dictionary
        """
        await self.ensure_connection()
        
        try:
            # Count programs
            program_count = await self.database.programs.count_documents({
                "university_name": university_name
            })
            
            # Count faculty
            faculty_count = 0
            faculty_with_email = 0
            faculty_with_website = 0
            faculty_with_lab = 0
            
            # Get program IDs for this university
            programs = await self.database.programs.find(
                {"university_name": university_name}, 
                {"_id": 1}
            ).to_list(None)
            
            program_ids = [str(p["_id"]) for p in programs]
            
            if program_ids:
                # Faculty statistics
                faculty_cursor = self.database.faculty.find(
                    {"program_id": {"$in": program_ids}}
                )
                
                async for faculty in faculty_cursor:
                    faculty_count += 1
                    if faculty.get("email"):
                        faculty_with_email += 1
                    if faculty.get("personal_website"):
                        faculty_with_website += 1
                    if faculty.get("lab_name"):
                        faculty_with_lab += 1
            
            # Count lab sites
            lab_sites_count = await self.database.lab_sites.count_documents({
                "program_id": {"$in": program_ids}
            }) if program_ids else 0
            
            return {
                "university_name": university_name,
                "programs": program_count,
                "faculty": faculty_count,
                "faculty_with_email": faculty_with_email,
                "faculty_with_personal_website": faculty_with_website,
                "faculty_with_lab": faculty_with_lab,
                "lab_sites": lab_sites_count,
                "email_capture_rate": (faculty_with_email / faculty_count * 100) if faculty_count > 0 else 0,
                "website_detection_rate": (faculty_with_website / faculty_count * 100) if faculty_count > 0 else 0,
                "lab_detection_rate": (faculty_with_lab / faculty_count * 100) if faculty_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Failed to get scraping statistics: {e}")
            raise 