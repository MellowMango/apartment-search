"""
University Database Module

Provides comprehensive university and department data for the Lynnapse scraper.
Combines multiple data sources including the College Scorecard API and curated datasets.
"""

import json
import asyncio
import aiohttp
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import re

logger = logging.getLogger(__name__)

@dataclass
class University:
    """Represents a university with its basic information."""
    id: str
    name: str
    city: str
    state: str
    state_code: str
    website: str
    type: str  # public, private-nonprofit, private-for-profit
    size: Optional[int] = None
    region: Optional[str] = None
    
    def __str__(self):
        return f"{self.name} ({self.city}, {self.state_code})"

@dataclass
class Department:
    """Represents an academic department."""
    name: str
    category: str
    common_variations: List[str]
    
class UniversityDatabase:
    """
    Manages university and department data from multiple sources.
    Provides search, filter, and selection functionality.
    """
    
    def __init__(self, college_scorecard_api_key: Optional[str] = None):
        self.api_key = college_scorecard_api_key
        self.universities: List[University] = []
        self.departments: List[Department] = []
        self._load_departments()
    
    def _load_departments(self):
        """Load common academic departments."""
        # Common academic departments with variations
        dept_data = [
            {
                "name": "Psychology", 
                "category": "Social Sciences",
                "variations": ["psychology", "psychological sciences", "psych"]
            },
            {
                "name": "Computer Science", 
                "category": "STEM",
                "variations": ["computer science", "cs", "computing", "informatics"]
            },
            {
                "name": "Biology", 
                "category": "STEM",
                "variations": ["biology", "biological sciences", "life sciences", "bio"]
            },
            {
                "name": "Chemistry", 
                "category": "STEM", 
                "variations": ["chemistry", "chemical sciences", "chem"]
            },
            {
                "name": "Physics", 
                "category": "STEM",
                "variations": ["physics", "physical sciences"]
            },
            {
                "name": "Mathematics", 
                "category": "STEM",
                "variations": ["mathematics", "math", "mathematical sciences"]
            },
            {
                "name": "Engineering", 
                "category": "STEM",
                "variations": ["engineering", "engineering sciences"]
            },
            {
                "name": "English", 
                "category": "Liberal Arts",
                "variations": ["english", "english literature", "literature"]
            },
            {
                "name": "History", 
                "category": "Liberal Arts",
                "variations": ["history", "historical studies"]
            },
            {
                "name": "Political Science", 
                "category": "Social Sciences",
                "variations": ["political science", "politics", "government"]
            },
            {
                "name": "Economics", 
                "category": "Social Sciences",
                "variations": ["economics", "economic sciences", "econ"]
            },
            {
                "name": "Sociology", 
                "category": "Social Sciences",
                "variations": ["sociology", "social sciences"]
            },
            {
                "name": "Anthropology", 
                "category": "Social Sciences",
                "variations": ["anthropology", "anthropological sciences"]
            },
            {
                "name": "Philosophy", 
                "category": "Liberal Arts",
                "variations": ["philosophy", "philosophical studies"]
            },
            {
                "name": "Art", 
                "category": "Fine Arts",
                "variations": ["art", "fine arts", "visual arts", "studio art"]
            },
            {
                "name": "Music", 
                "category": "Fine Arts",
                "variations": ["music", "musical studies", "music theory"]
            },
            {
                "name": "Business", 
                "category": "Business",
                "variations": ["business", "business administration", "management"]
            },
            {
                "name": "Education", 
                "category": "Education",
                "variations": ["education", "educational studies", "teaching"]
            },
            {
                "name": "Medicine", 
                "category": "Health Sciences",
                "variations": ["medicine", "medical sciences", "pre-med"]
            },
            {
                "name": "Nursing", 
                "category": "Health Sciences",
                "variations": ["nursing", "nursing sciences"]
            }
        ]
        
        self.departments = [
            Department(
                name=dept["name"],
                category=dept["category"],
                common_variations=dept["variations"]
            )
            for dept in dept_data
        ]
    
    async def load_universities_from_api(self, limit: int = 5000) -> bool:
        """
        Load universities from the College Scorecard API.
        Returns True if successful, False otherwise.
        """
        if not self.api_key:
            logger.warning("No College Scorecard API key provided")
            return False
        
        try:
            async with aiohttp.ClientSession() as session:
                # Get universities with basic info
                url = "https://api.data.gov/ed/collegescorecard/v1/schools"
                params = {
                    "api_key": self.api_key,
                    "fields": "id,school.name,school.city,school.state,school.state_fips,school.school_url,school.ownership",
                    "school.degrees_awarded.predominant": "2,3,4",  # Associate, Bachelor's, Graduate
                    "per_page": 100,
                    "page": 0
                }
                
                universities = []
                total_loaded = 0
                
                while total_loaded < limit:
                    async with session.get(url, params=params) as response:
                        if response.status != 200:
                            logger.error(f"API request failed: {response.status}")
                            break
                        
                        data = await response.json()
                        results = data.get("results", [])
                        
                        if not results:
                            break
                        
                        for result in results:
                            school = result.get("school", {})
                            if school.get("name") and school.get("state"):
                                university = University(
                                    id=str(result.get("id", "")),
                                    name=school.get("name", ""),
                                    city=school.get("city", ""),
                                    state=self._get_state_name(school.get("state_fips")),
                                    state_code=school.get("state", ""),
                                    website=school.get("school_url", ""),
                                    type=self._get_ownership_type(school.get("ownership"))
                                )
                                universities.append(university)
                                total_loaded += 1
                                
                                if total_loaded >= limit:
                                    break
                        
                        # Next page
                        params["page"] += 1
                        if params["page"] > 50:  # Safety limit
                            break
                
                self.universities = universities
                logger.info(f"Loaded {len(self.universities)} universities from College Scorecard API")
                return True
                
        except Exception as e:
            logger.error(f"Failed to load universities from API: {e}")
            return False
    
    def load_universities_from_backup(self) -> bool:
        """Load universities from backup static data."""
        # Fallback list of major US universities
        backup_universities = [
            ("Stanford University", "Stanford", "California", "CA", "https://www.stanford.edu", "private-nonprofit"),
            ("Harvard University", "Cambridge", "Massachusetts", "MA", "https://www.harvard.edu", "private-nonprofit"),
            ("MIT", "Cambridge", "Massachusetts", "MA", "https://web.mit.edu", "private-nonprofit"),
            ("University of California, Berkeley", "Berkeley", "California", "CA", "https://www.berkeley.edu", "public"),
            ("University of California, Los Angeles", "Los Angeles", "California", "CA", "https://www.ucla.edu", "public"),
            ("Yale University", "New Haven", "Connecticut", "CT", "https://www.yale.edu", "private-nonprofit"),
            ("Princeton University", "Princeton", "New Jersey", "NJ", "https://www.princeton.edu", "private-nonprofit"),
            ("University of Chicago", "Chicago", "Illinois", "IL", "https://www.uchicago.edu", "private-nonprofit"),
            ("Columbia University", "New York", "New York", "NY", "https://www.columbia.edu", "private-nonprofit"),
            ("University of Pennsylvania", "Philadelphia", "Pennsylvania", "PA", "https://www.upenn.edu", "private-nonprofit"),
            ("University of Michigan", "Ann Arbor", "Michigan", "MI", "https://umich.edu", "public"),
            ("University of Washington", "Seattle", "Washington", "WA", "https://www.washington.edu", "public"),
            ("University of Wisconsin-Madison", "Madison", "Wisconsin", "WI", "https://www.wisc.edu", "public"),
            ("University of Texas at Austin", "Austin", "Texas", "TX", "https://www.utexas.edu", "public"),
            ("Georgia Institute of Technology", "Atlanta", "Georgia", "GA", "https://www.gatech.edu", "public"),
            ("Carnegie Mellon University", "Pittsburgh", "Pennsylvania", "PA", "https://www.cmu.edu", "private-nonprofit"),
            ("Northwestern University", "Evanston", "Illinois", "IL", "https://www.northwestern.edu", "private-nonprofit"),
            ("Duke University", "Durham", "North Carolina", "NC", "https://duke.edu", "private-nonprofit"),
            ("Cornell University", "Ithaca", "New York", "NY", "https://www.cornell.edu", "private-nonprofit"),
            ("University of Southern California", "Los Angeles", "California", "CA", "https://www.usc.edu", "private-nonprofit"),
            ("Arizona State University", "Tempe", "Arizona", "AZ", "https://www.asu.edu", "public"),
            ("University of Arizona", "Tucson", "Arizona", "AZ", "https://www.arizona.edu", "public"),
            ("Ohio State University", "Columbus", "Ohio", "OH", "https://www.osu.edu", "public"),
            ("Pennsylvania State University", "University Park", "Pennsylvania", "PA", "https://www.psu.edu", "public"),
            ("University of Florida", "Gainesville", "Florida", "FL", "https://www.ufl.edu", "public"),
        ]
        
        self.universities = [
            University(
                id=str(i),
                name=name,
                city=city,
                state=state,
                state_code=state_code,
                website=website,
                type=uni_type
            )
            for i, (name, city, state, state_code, website, uni_type) in enumerate(backup_universities)
        ]
        
        logger.info(f"Loaded {len(self.universities)} universities from backup data")
        return True
    
    def search_universities(self, query: str, state: str = None, limit: int = 20) -> List[University]:
        """Search universities by name, with optional state filter."""
        if not self.universities:
            return []
        
        # If no query provided, return all universities (for dropdown population)
        if not query.strip():
            results = self.universities
        else:
            query_lower = query.lower()
            results = []
            
            for university in self.universities:
                # Match by name
                if query_lower in university.name.lower():
                    if state is None or university.state_code.lower() == state.lower():
                        results.append(university)
                
                if len(results) >= limit:
                    break
        
        # Apply state filter if specified
        if state:
            results = [uni for uni in results if uni.state_code.lower() == state.lower()]
        
        # Apply limit
        return results[:limit]
    
    def get_universities_by_state(self, state_code: str) -> List[University]:
        """Get all universities in a specific state."""
        return [
            uni for uni in self.universities 
            if uni.state_code.lower() == state_code.lower()
        ]
    
    def get_states(self) -> List[Tuple[str, str]]:
        """Get list of states with universities (state_code, state_name)."""
        states = {}
        for uni in self.universities:
            if uni.state_code and uni.state:
                states[uni.state_code] = uni.state
        
        return sorted([(code, name) for code, name in states.items()])
    
    def search_departments(self, query: str, limit: int = 10) -> List[Department]:
        """Search departments by name or variation."""
        if not query:
            return self.departments[:limit]
        
        query_lower = query.lower()
        results = []
        
        for dept in self.departments:
            # Check name match
            if query_lower in dept.name.lower():
                results.append(dept)
            # Check variations match
            elif any(query_lower in var.lower() for var in dept.common_variations):
                results.append(dept)
            
            if len(results) >= limit:
                break
        
        return results
    
    def get_departments_by_category(self, category: str) -> List[Department]:
        """Get departments by category."""
        return [dept for dept in self.departments if dept.category == category]
    
    def get_department_categories(self) -> List[str]:
        """Get list of department categories."""
        categories = set(dept.category for dept in self.departments)
        return sorted(list(categories))
    
    def _get_state_name(self, state_fips: Optional[str]) -> str:
        """Convert FIPS code to state name."""
        # Simplified mapping - in practice you'd want a complete FIPS to state mapping
        fips_to_state = {
            "01": "Alabama", "02": "Alaska", "04": "Arizona", "05": "Arkansas",
            "06": "California", "08": "Colorado", "09": "Connecticut", "10": "Delaware",
            "11": "District of Columbia", "12": "Florida", "13": "Georgia", "15": "Hawaii",
            "16": "Idaho", "17": "Illinois", "18": "Indiana", "19": "Iowa",
            "20": "Kansas", "21": "Kentucky", "22": "Louisiana", "23": "Maine",
            "24": "Maryland", "25": "Massachusetts", "26": "Michigan", "27": "Minnesota",
            "28": "Mississippi", "29": "Missouri", "30": "Montana", "31": "Nebraska",
            "32": "Nevada", "33": "New Hampshire", "34": "New Jersey", "35": "New Mexico",
            "36": "New York", "37": "North Carolina", "38": "North Dakota", "39": "Ohio",
            "40": "Oklahoma", "41": "Oregon", "42": "Pennsylvania", "44": "Rhode Island",
            "45": "South Carolina", "46": "South Dakota", "47": "Tennessee", "48": "Texas",
            "49": "Utah", "50": "Vermont", "51": "Virginia", "53": "Washington",
            "54": "West Virginia", "55": "Wisconsin", "56": "Wyoming"
        }
        return fips_to_state.get(state_fips, "Unknown")
    
    def _get_ownership_type(self, ownership: Optional[int]) -> str:
        """Convert ownership code to human-readable type."""
        ownership_map = {
            1: "public",
            2: "private-nonprofit", 
            3: "private-for-profit"
        }
        return ownership_map.get(ownership, "unknown")
    
    async def initialize(self, use_api: bool = True) -> bool:
        """Initialize the database with university data."""
        if use_api:
            success = await self.load_universities_from_api()
            if not success:
                logger.info("API failed, falling back to backup data")
                return self.load_universities_from_backup()
            return True
        else:
            return self.load_universities_from_backup()

# Global instance
university_db = UniversityDatabase()

async def get_university_suggestions(query: str, limit: int = 10) -> List[Dict]:
    """Get university suggestions for autocomplete."""
    if not university_db.universities:
        await university_db.initialize(use_api=False)  # Use backup data
    
    results = university_db.search_universities(query, limit=limit)
    return [
        {
            "id": uni.id,
            "name": uni.name,
            "location": f"{uni.city}, {uni.state_code}",
            "type": uni.type,
            "website": uni.website
        }
        for uni in results
    ]

async def get_department_suggestions(query: str, limit: int = 10) -> List[Dict]:
    """Get department suggestions for autocomplete."""
    results = university_db.search_departments(query, limit=limit)
    return [
        {
            "name": dept.name,
            "category": dept.category,
            "variations": dept.common_variations
        }
        for dept in results
    ] 