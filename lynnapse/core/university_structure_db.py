"""
University Structure Database

This module provides persistent storage for university structure information,
including discovered faculty directory paths and department structures.
"""

import json
import logging
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, asdict
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class UniversityStructure:
    """Complete structure information for a university."""
    university_name: str
    base_url: str
    faculty_directory_paths: List[str]
    department_paths: List[str]
    departments: Dict[str, List[str]]  # department_name -> [faculty_paths]
    discovery_method: str  # 'sitemap', 'navigation', 'llm', etc.
    confidence_score: float
    last_updated: float
    discovery_count: int = 1  # How many times this has been discovered


class UniversityStructureDB:
    """Persistent database for university structure information."""
    
    def __init__(self, db_path: str = "db/university_structures.json"):
        """Initialize the university structure database."""
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # In-memory cache
        self._structures: Dict[str, UniversityStructure] = {}
        self._load_database()
        
        logger.info(f"University structure database initialized: {self.db_path.absolute()}")
        logger.info(f"Loaded {len(self._structures)} university structures")
    
    def _create_key(self, university_name: str, base_url: str = "") -> str:
        """Create a unique key for a university."""
        # Clean university name for key
        clean_name = "".join(c for c in university_name.lower() if c.isalnum() or c in (' ', '-', '_')).strip()
        clean_name = clean_name.replace(' ', '_')
        return clean_name
    
    def _load_database(self) -> None:
        """Load the database from disk."""
        try:
            if self.db_path.exists():
                with open(self.db_path, 'r') as f:
                    data = json.load(f)
                
                for key, structure_data in data.items():
                    try:
                        self._structures[key] = UniversityStructure(**structure_data)
                    except Exception as e:
                        logger.warning(f"Failed to load structure for {key}: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to load university structure database: {e}")
            self._structures = {}
    
    def _save_database(self) -> None:
        """Save the database to disk."""
        try:
            data = {}
            for key, structure in self._structures.items():
                data[key] = asdict(structure)
            
            # Write atomically
            temp_path = self.db_path.with_suffix('.tmp')
            with open(temp_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            temp_path.replace(self.db_path)
            logger.debug(f"Saved {len(self._structures)} structures to database")
            
        except Exception as e:
            logger.error(f"Failed to save university structure database: {e}")
    
    def store_structure(self, 
                       university_name: str,
                       base_url: str,
                       faculty_directory_paths: List[str],
                       department_paths: List[str] = None,
                       departments: Dict[str, List[str]] = None,
                       discovery_method: str = "unknown",
                       confidence_score: float = 0.0) -> None:
        """Store or update university structure information."""
        
        key = self._create_key(university_name, base_url)
        current_time = time.time()
        
        if key in self._structures:
            # Update existing structure
            structure = self._structures[key]
            
            # Merge faculty paths (keep unique)
            all_faculty_paths = list(set(structure.faculty_directory_paths + faculty_directory_paths))
            
            # Merge department paths
            all_dept_paths = department_paths or []
            if structure.department_paths:
                all_dept_paths = list(set(structure.department_paths + all_dept_paths))
            
            # Merge departments
            all_departments = structure.departments.copy()
            if departments:
                for dept_name, paths in departments.items():
                    if dept_name in all_departments:
                        all_departments[dept_name] = list(set(all_departments[dept_name] + paths))
                    else:
                        all_departments[dept_name] = paths
            
            # Update structure
            structure.faculty_directory_paths = all_faculty_paths
            structure.department_paths = all_dept_paths
            structure.departments = all_departments
            structure.discovery_method = discovery_method  # Update to latest method
            structure.confidence_score = max(structure.confidence_score, confidence_score)
            structure.last_updated = current_time
            structure.discovery_count += 1
            
            logger.info(f"Updated structure for {university_name} (discovery #{structure.discovery_count})")
            
        else:
            # Create new structure
            structure = UniversityStructure(
                university_name=university_name,
                base_url=base_url,
                faculty_directory_paths=faculty_directory_paths,
                department_paths=department_paths or [],
                departments=departments or {},
                discovery_method=discovery_method,
                confidence_score=confidence_score,
                last_updated=current_time,
                discovery_count=1
            )
            
            self._structures[key] = structure
            logger.info(f"Stored new structure for {university_name}")
        
        # Save to disk
        self._save_database()
    
    def get_structure(self, university_name: str, base_url: str = "") -> Optional[UniversityStructure]:
        """Get university structure information."""
        key = self._create_key(university_name, base_url)
        return self._structures.get(key)
    
    def get_faculty_paths(self, university_name: str, department_name: str = None) -> List[str]:
        """Get faculty directory paths for a university/department."""
        structure = self.get_structure(university_name)
        if not structure:
            return []
        
        paths = []
        
        # Add general faculty paths
        paths.extend(structure.faculty_directory_paths)
        
        # Add department-specific paths if department is specified
        if department_name:
            dept_key = department_name.lower()
            
            # Look for exact match first
            if dept_key in structure.departments:
                paths.extend(structure.departments[dept_key])
            
            # Look for partial matches
            for dept, dept_paths in structure.departments.items():
                if dept_key in dept or dept in dept_key:
                    paths.extend(dept_paths)
        
        return list(set(paths))  # Remove duplicates
    
    def add_department_paths(self, university_name: str, department_name: str, paths: List[str]) -> None:
        """Add specific paths for a department."""
        structure = self.get_structure(university_name)
        if not structure:
            logger.warning(f"No structure found for {university_name} to add department paths")
            return
        
        dept_key = department_name.lower()
        if dept_key in structure.departments:
            structure.departments[dept_key] = list(set(structure.departments[dept_key] + paths))
        else:
            structure.departments[dept_key] = paths
        
        structure.last_updated = time.time()
        self._save_database()
        
        logger.info(f"Added {len(paths)} paths for {department_name} at {university_name}")
    
    def list_universities(self) -> List[Dict[str, Any]]:
        """List all universities in the database."""
        universities = []
        for structure in self._structures.values():
            universities.append({
                'name': structure.university_name,
                'base_url': structure.base_url,
                'faculty_paths': len(structure.faculty_directory_paths),
                'departments': len(structure.departments),
                'discovery_method': structure.discovery_method,
                'confidence': structure.confidence_score,
                'last_updated': time.strftime('%Y-%m-%d %H:%M:%S', 
                                             time.localtime(structure.last_updated)),
                'discovery_count': structure.discovery_count
            })
        
        return sorted(universities, key=lambda x: x['last_updated'], reverse=True)
        
    def get_departments(self, university_name: str) -> List[str]:
        """Get all known departments for a university."""
        structure = self.get_structure(university_name)
        if not structure:
            return []
        
        return list(structure.departments.keys())
    
    def search_universities(self, query: str) -> List[str]:
        """Search for universities by name."""
        query_lower = query.lower()
        matches = []
        
        for structure in self._structures.values():
            if query_lower in structure.university_name.lower():
                matches.append(structure.university_name)
        
        return sorted(matches)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        total_universities = len(self._structures)
        total_departments = sum(len(s.departments) for s in self._structures.values())
        total_faculty_paths = sum(len(s.faculty_directory_paths) for s in self._structures.values())
        
        discovery_methods = defaultdict(int)
        for structure in self._structures.values():
            discovery_methods[structure.discovery_method] += 1
        
        return {
            'total_universities': total_universities,
            'total_departments': total_departments,
            'total_faculty_paths': total_faculty_paths,
            'discovery_methods': dict(discovery_methods),
            'database_path': str(self.db_path.absolute()),
            'last_update': max((s.last_updated for s in self._structures.values()), default=0)
        }
    
    def cleanup_old_entries(self, max_age_days: int = 30) -> int:
        """Clean up old entries that haven't been updated recently."""
        cutoff_time = time.time() - (max_age_days * 24 * 3600)
        removed_count = 0
        
        keys_to_remove = []
        for key, structure in self._structures.items():
            if structure.last_updated < cutoff_time and structure.discovery_count == 1:
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self._structures[key]
            removed_count += 1
        
        if removed_count > 0:
            self._save_database()
            logger.info(f"Cleaned up {removed_count} old university structures")
        
        return removed_count


# Global instance
_db_instance = None

def get_university_structure_db() -> UniversityStructureDB:
    """Get the global university structure database instance."""
    global _db_instance
    if _db_instance is None:
        _db_instance = UniversityStructureDB()
    return _db_instance 