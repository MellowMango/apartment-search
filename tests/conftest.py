"""
PyTest configuration and shared fixtures for Lynnapse test suite.

This module provides common fixtures, test utilities, and configuration
for comprehensive testing of the Lynnapse faculty scraping system.
"""

import pytest
import asyncio
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from unittest.mock import AsyncMock, MagicMock, patch
import aiohttp
from aioresponses import aioresponses

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from lynnapse.core.link_heuristics import LinkHeuristics
from lynnapse.core.lab_classifier import LabNameClassifier
from lynnapse.core.website_validator import WebsiteValidator
from lynnapse.core.smart_link_replacer import SmartLinkReplacer
from lynnapse.core.enhanced_link_processor import EnhancedLinkProcessor
from lynnapse.core.link_enrichment import LinkEnrichmentEngine
from lynnapse.core.university_adapter import UniversityAdapter
from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler

# Configure asyncio for testing
@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# Test data fixtures
@pytest.fixture
def sample_faculty_data():
    """Sample faculty data for testing."""
    return [
        {
            "_id": "test_faculty_1",
            "name": "Dr. John Smith",
            "title": "Professor of Psychology", 
            "university": "Test University",
            "department": "Psychology",
            "email": "john.smith@test.edu",
            "profile_url": "https://test.edu/faculty/john-smith",
            "personal_website": "https://scholar.google.com/citations?user=abc123",
            "research_interests": ["cognitive psychology", "memory", "attention"],
            "scraped_at": "2025-06-27T10:00:00Z"
        },
        {
            "_id": "test_faculty_2", 
            "name": "Dr. Jane Doe",
            "title": "Assistant Professor",
            "university": "Test University",
            "department": "Psychology",
            "email": "jane.doe@test.edu",
            "profile_url": "https://linkedin.com/in/janedoe",  # Social media
            "research_interests": ["developmental psychology", "language"],
            "scraped_at": "2025-06-27T10:00:00Z"
        },
        {
            "_id": "test_faculty_3",
            "name": "Dr. Robert Wilson", 
            "title": "Associate Professor",
            "university": "Test University",
            "department": "Psychology",
            "email": "robert.wilson@test.edu",
            "profile_url": "https://test.edu/faculty/robert-wilson",
            "lab_website": "https://coglab.test.edu",
            "research_interests": ["neuroscience", "brain imaging"],
            "scraped_at": "2025-06-27T10:00:00Z"
        }
    ]

@pytest.fixture
def sample_html_content():
    """Sample HTML content for testing scrapers."""
    return {
        "faculty_directory": """
        <div class="faculty-listing">
            <div class="faculty-card">
                <h3><a href="/faculty/john-smith">Dr. John Smith</a></h3>
                <p>Professor of Psychology</p>
                <p>Email: john.smith@test.edu</p>
                <p>Research: Cognitive Psychology</p>
            </div>
            <div class="faculty-card">
                <h3><a href="/faculty/jane-doe">Dr. Jane Doe</a></h3>
                <p>Assistant Professor</p>
                <p>Email: jane.doe@test.edu</p>
                <p>Research: Developmental Psychology</p>
            </div>
        </div>
        """,
        "faculty_profile": """
        <div class="profile">
            <h1>Dr. John Smith</h1>
            <p>Professor of Psychology</p>
            <p>Email: <a href="mailto:john.smith@test.edu">john.smith@test.edu</a></p>
            <p>Office: Room 123, Psychology Building</p>
            <p>Phone: (555) 123-4567</p>
            <div class="research-interests">
                <h3>Research Interests</h3>
                <ul>
                    <li>Cognitive Psychology</li>
                    <li>Memory and Attention</li>
                    <li>Decision Making</li>
                </ul>
            </div>
            <div class="biography">
                <h3>Biography</h3>
                <p>Dr. Smith conducts research in the Cognitive Neuroscience Laboratory,
                   focusing on memory processes and attention mechanisms.</p>
            </div>
            <div class="links">
                <a href="https://scholar.google.com/citations?user=abc123">Google Scholar</a>
                <a href="https://coglab.test.edu">Research Lab</a>
                <a href="https://test.edu/~jsmith">Personal Page</a>
            </div>
        </div>
        """,
        "lab_website": """
        <div class="lab-site">
            <h1>Cognitive Neuroscience Laboratory</h1>
            <p>Director: Dr. John Smith</p>
            <div class="research">
                <h2>Research Areas</h2>
                <ul>
                    <li>Memory and Learning</li>
                    <li>Attention and Perception</li>
                    <li>Neural Networks</li>
                </ul>
            </div>
            <div class="equipment">
                <h2>Equipment</h2>
                <ul>
                    <li>fMRI Scanner</li>
                    <li>EEG System</li>
                    <li>Eye Tracker</li>
                </ul>
            </div>
            <div class="team">
                <h2>Lab Members</h2>
                <ul>
                    <li>Dr. John Smith (Director)</li>
                    <li>Alice Johnson (PhD Student)</li>
                    <li>Bob Chen (Research Assistant)</li>
                </ul>
            </div>
        </div>
        """
    }

@pytest.fixture
def mock_university_config():
    """Mock university configuration for testing."""
    return {
        "name": "Test University",
        "base_url": "https://test.edu",
        "departments": {
            "psychology": {
                "name": "Psychology",
                "url": "https://test.edu/psychology",
                "faculty_url": "https://test.edu/psychology/faculty"
            }
        }
    }

# Component fixtures
@pytest.fixture
def link_heuristics():
    """LinkHeuristics instance for testing."""
    return LinkHeuristics()

@pytest.fixture
def lab_classifier():
    """LabNameClassifier instance for testing."""
    classifier = LabNameClassifier()
    # Add some basic training data for testing
    training_sentences = [
        "Cognitive Neuroscience Laboratory",
        "Advanced Research Center", 
        "Machine Learning Lab",
        "The professor teaches courses",
        "Office hours are available",
        "Contact information below"
    ]
    training_labels = [True, True, True, False, False, False]
    classifier.train(training_sentences, training_labels)
    return classifier

@pytest.fixture
def website_validator():
    """WebsiteValidator instance for testing."""
    return WebsiteValidator()

@pytest.fixture
def smart_link_replacer():
    """SmartLinkReplacer instance for testing."""
    return SmartLinkReplacer(enable_ai_assistance=False)

@pytest.fixture
def enhanced_link_processor():
    """EnhancedLinkProcessor instance for testing."""
    return EnhancedLinkProcessor()

@pytest.fixture
def link_enrichment_engine():
    """LinkEnrichmentEngine instance for testing."""
    return LinkEnrichmentEngine()

@pytest.fixture
def university_adapter():
    """UniversityAdapter instance for testing."""
    return UniversityAdapter()

@pytest.fixture
def adaptive_faculty_crawler():
    """AdaptiveFacultyCrawler instance for testing."""
    return AdaptiveFacultyCrawler()

# Mock external services
@pytest.fixture
def mock_aiohttp():
    """Mock aiohttp responses for external API calls."""
    with aioresponses() as mock:
        # Mock Google Scholar responses
        mock.get(
            "https://scholar.google.com/citations?user=abc123",
            payload={"status": "success"},
            headers={"Content-Type": "text/html"}
        )
        
        # Mock university website responses  
        mock.get(
            "https://test.edu/faculty/john-smith",
            payload={"status": "success"},
            headers={"Content-Type": "text/html"}
        )
        
        # Mock Bing Search API
        mock.get(
            "https://api.bing.microsoft.com/v7.0/search",
            payload={
                "webPages": {
                    "value": [
                        {"url": "https://scholar.google.com/citations?user=test", "name": "Test Scholar"},
                        {"url": "https://test.edu/~faculty", "name": "Faculty Page"}
                    ]
                }
            }
        )
        
        yield mock

@pytest.fixture
def mock_openai_api():
    """Mock OpenAI API responses for AI-assisted testing."""
    with patch('openai.ChatCompletion.acreate') as mock_create:
        mock_create.return_value = AsyncMock()
        mock_create.return_value.choices = [
            MagicMock(message=MagicMock(content=json.dumps({
                "academic_urls": [
                    {
                        "url": "https://scholar.google.com/citations?user=test123", 
                        "type": "google_scholar",
                        "confidence": 0.95,
                        "reason": "Official Google Scholar profile"
                    }
                ],
                "search_queries": [
                    "Dr. John Smith cognitive psychology Test University",
                    "John Smith faculty psychology scholar"
                ]
            })))
        ]
        yield mock_create

@pytest.fixture
def temp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)

@pytest.fixture
def mock_cache():
    """Mock cache implementation for testing."""
    cache_store = {}
    
    class MockCache:
        async def get(self, key: str) -> Optional[str]:
            return cache_store.get(key)
        
        async def setex(self, key: str, ttl: int, value: str) -> None:
            cache_store[key] = value
        
        async def delete(self, key: str) -> None:
            cache_store.pop(key, None)
        
        def clear(self):
            cache_store.clear()
    
    return MockCache()

# Performance monitoring enhancements
@pytest.fixture
def performance_monitor():
    """Enhanced performance monitoring for comprehensive testing."""
    class PerformanceMonitor:
        def __init__(self):
            self.start_time = None
            self.end_time = None
            self.peak_memory = 0
            self.start_memory = 0
            self.memory_samples = []
            self._monitoring = False
            
        def start(self):
            """Start performance monitoring."""
            import time
            import psutil
            
            self.start_time = time.time()
            process = psutil.Process()
            self.start_memory = process.memory_info().rss / 1024 / 1024  # MB
            self.peak_memory = self.start_memory
            self.memory_samples = [self.start_memory]
            self._monitoring = True
        
        def stop(self):
            """Stop performance monitoring."""
            import time
            self.end_time = time.time()
            self._monitoring = False
        
        def _monitor_memory(self):
            """Monitor memory usage during operation."""
            if not self._monitoring:
                return
                
            try:
                import psutil
                process = psutil.Process()
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                self.memory_samples.append(current_memory)
                self.peak_memory = max(self.peak_memory, current_memory)
            except Exception:
                pass
                
        @property
        def elapsed_time(self):
            if self.start_time and self.end_time:
                return self.end_time - self.start_time
            return 0
            
        def get_results(self):
            """Get comprehensive performance results."""
            elapsed = self.elapsed_time
            return {
                "elapsed_time_seconds": elapsed,
                "start_memory_mb": self.start_memory,
                "peak_memory_mb": self.peak_memory,
                "memory_growth_mb": self.peak_memory - self.start_memory,
                "average_memory_mb": sum(self.memory_samples) / len(self.memory_samples) if self.memory_samples else 0,
                "time_efficient": elapsed < 30.0,  # Under 30 seconds
                "memory_efficient": self.peak_memory < 200.0,  # Under 200MB
                "memory_stable": (self.peak_memory - self.start_memory) < 50.0  # Less than 50MB growth
            }
    
    return PerformanceMonitor()

# Additional test fixtures for comprehensive testing
@pytest.fixture
def large_faculty_dataset():
    """Large faculty dataset for performance testing."""
    dataset = []
    for i in range(100):
        faculty = {
            "_id": f"perf_test_faculty_{i}",
            "name": f"Dr. Performance Test {i}",
            "title": f"Professor of Test Science {i % 5}",
            "university": f"Test University {i % 10}",
            "department": f"Test Department {i % 3}",
            "email": f"test{i}@test{i % 10}.edu",
            "profile_url": f"https://test{i % 10}.edu/faculty/test{i}",
            "personal_website": f"https://scholar.google.com/citations?user=test{i}" if i % 3 == 0 else None,
            "lab_website": f"https://lab{i % 5}.test.edu" if i % 4 == 0 else None,
            "research_interests": [f"research area {i % 10}", f"field {i % 7}"],
            "scraped_at": "2025-06-27T10:00:00Z"
        }
        # Add some social media links for testing
        if i % 5 == 0:
            faculty["profile_url"] = f"https://linkedin.com/in/test{i}"
        elif i % 5 == 1:
            faculty["personal_website"] = f"https://twitter.com/test{i}"
        
        dataset.append(faculty)
    
    return dataset

@pytest.fixture
def production_test_config():
    """Production-like configuration for testing."""
    return {
        "max_concurrent_requests": 5,
        "request_timeout_seconds": 15,
        "retry_attempts": 2,
        "memory_limit_mb": 300,
        "enable_ai_assistance": False,
        "enable_structured_logging": True,
        "health_check_enabled": True,
        "metrics_collection_enabled": True
    }

# Test environment configuration
@pytest.fixture(autouse=True)
def test_environment(monkeypatch):
    """Set up comprehensive test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("MONGODB_URL", "mongodb://localhost:27017/lynnapse_test")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("MAX_CONCURRENT_REQUESTS", "3")  # Lower for testing
    monkeypatch.setenv("REQUEST_TIMEOUT", "10")         # Faster for testing
    monkeypatch.setenv("REQUEST_DELAY", "0.1")          # Faster for testing
    monkeypatch.setenv("RETRY_ATTEMPTS", "2")           # Fewer retries for testing
    monkeypatch.setenv("MEMORY_LIMIT_MB", "200")        # Lower for testing
    monkeypatch.setenv("BATCH_SIZE", "10")              # Smaller batches for testing
    monkeypatch.setenv("AI_COST_LIMIT", "1.0")          # Lower cost limit for testing

# Auto-cleanup for test files
@pytest.fixture(autouse=True)
def cleanup_temp_files():
    """Clean up temporary files created during testing."""
    temp_files = [
        "test_results.json",
        "benchmark_results.json",
        "performance_test_results.json",
        "integration_test_output.json",
        "temp_faculty_data.json"
    ]
    
    yield  # Let tests run
    
    # Cleanup after tests
    import os
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        except Exception:
            pass  # Ignore cleanup errors 