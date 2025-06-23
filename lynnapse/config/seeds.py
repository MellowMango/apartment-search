"""
YAML seed loader for university configurations.
"""

import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, HttpUrl


logger = logging.getLogger(__name__)


class ProgramConfig(BaseModel):
    """Configuration for a university program."""
    name: str
    department: str
    college: str
    program_url: str
    faculty_directory_url: Optional[str] = None
    program_type: str = "graduate"  # undergraduate, graduate, phd
    selectors: Optional[Dict[str, str]] = None  # CSS selectors for scraping


class UniversityConfig(BaseModel):
    """Configuration for a university."""
    name: str
    base_url: str
    programs: List[ProgramConfig]
    
    # Scraping configuration
    scraping_config: Dict[str, Any] = Field(default_factory=dict)
    
    # Rate limiting
    rate_limit_delay: float = 1.0
    max_concurrent_requests: int = 3
    
    # Retry configuration
    max_retries: int = 3
    retry_delay: float = 5.0


class SeedLoader:
    """Loader for university configuration seeds."""
    
    def __init__(self, seeds_directory: str = "seeds"):
        """Initialize the seed loader."""
        self.seeds_directory = Path(seeds_directory)
        self.universities: Dict[str, UniversityConfig] = {}
    
    def load_all_seeds(self) -> Dict[str, UniversityConfig]:
        """Load all university configuration seeds."""
        if not self.seeds_directory.exists():
            logger.warning(f"Seeds directory not found: {self.seeds_directory}")
            return {}
        
        self.universities = {}
        
        for yaml_file in self.seeds_directory.glob("*.yml"):
            try:
                university_config = self.load_seed_file(yaml_file)
                if university_config:
                    self.universities[university_config.name] = university_config
                    logger.info(f"Loaded configuration for {university_config.name}")
            except Exception as e:
                logger.error(f"Error loading seed file {yaml_file}: {e}")
        
        for yaml_file in self.seeds_directory.glob("*.yaml"):
            try:
                university_config = self.load_seed_file(yaml_file)
                if university_config:
                    self.universities[university_config.name] = university_config
                    logger.info(f"Loaded configuration for {university_config.name}")
            except Exception as e:
                logger.error(f"Error loading seed file {yaml_file}: {e}")
        
        logger.info(f"Loaded {len(self.universities)} university configurations")
        return self.universities
    
    def load_seed_file(self, file_path: Path) -> Optional[UniversityConfig]:
        """Load a single seed file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
            
            # Validate and create university config
            university_config = UniversityConfig(**config_data)
            return university_config
            
        except yaml.YAMLError as e:
            logger.error(f"YAML parsing error in {file_path}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading seed file {file_path}: {e}")
            return None
    
    def get_university_config(self, university_name: str) -> Optional[UniversityConfig]:
        """Get configuration for a specific university."""
        return self.universities.get(university_name)
    
    def get_all_programs(self) -> List[tuple[str, ProgramConfig]]:
        """Get all programs from all universities."""
        programs = []
        for university_name, university_config in self.universities.items():
            for program in university_config.programs:
                programs.append((university_name, program))
        return programs
    
    def create_example_seed(self, output_path: str = "seeds/university_of_arizona.yml") -> None:
        """Create an example seed file."""
        example_config = {
            "name": "University of Arizona",
            "base_url": "https://arizona.edu",
            "programs": [
                {
                    "name": "Psychology",
                    "department": "Psychology",
                    "college": "College of Science",
                    "program_url": "https://psychology.arizona.edu/graduate",
                    "faculty_directory_url": "https://psychology.arizona.edu/people/faculty",
                    "program_type": "graduate",
                    "selectors": {
                        "faculty_links": ".faculty-list a, .people-list a",
                        "faculty_name": "h1, .name, .faculty-name",
                        "faculty_title": ".title, .position",
                        "faculty_email": "a[href^='mailto:']",
                        "research_interests": ".research-interests, .interests"
                    }
                },
                {
                    "name": "Computer Science",
                    "department": "Computer Science",
                    "college": "College of Science",
                    "program_url": "https://cs.arizona.edu/graduate",
                    "faculty_directory_url": "https://cs.arizona.edu/people/faculty",
                    "program_type": "graduate"
                }
            ],
            "scraping_config": {
                "user_agent": "Mozilla/5.0 (compatible; LynnapseBot/1.0)",
                "wait_for_selector": ".content, .main",
                "timeout": 30
            },
            "rate_limit_delay": 2.0,
            "max_concurrent_requests": 2,
            "max_retries": 3,
            "retry_delay": 5.0
        }
        
        # Ensure directory exists
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write the example seed
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(example_config, f, default_flow_style=False, indent=2)
        
        logger.info(f"Created example seed file: {output_path}")


# Global seed loader instance
_seed_loader: Optional[SeedLoader] = None


def get_seed_loader(seeds_directory: str = "seeds") -> SeedLoader:
    """Get the global seed loader instance."""
    global _seed_loader
    if _seed_loader is None:
        _seed_loader = SeedLoader(seeds_directory)
        _seed_loader.load_all_seeds()
    return _seed_loader 