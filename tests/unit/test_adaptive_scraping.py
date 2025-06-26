"""
Unit tests for adaptive scraping components.

Tests the UniversityAdapter and AdaptiveFacultyCrawler functionality
including pattern discovery, department extraction, and faculty scraping.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from bs4 import BeautifulSoup

from lynnapse.core.university_adapter import UniversityAdapter, UniversityPattern, DepartmentInfo
from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler


class TestUniversityAdapter:
    """Test the UniversityAdapter class."""
    
    @pytest.fixture
    def adapter(self):
        """Create a UniversityAdapter instance for testing."""
        return UniversityAdapter(cache_client={})
    
    def test_initialization(self, adapter):
        """Test adapter initialization."""
        assert adapter.cache_client == {}
        assert adapter.discovered_patterns == {}
        assert adapter.session is not None
    
    def test_create_fallback_pattern(self, adapter):
        """Test fallback pattern creation."""
        result = adapter._create_fallback_pattern("Test University", "https://test.edu")
        
        assert result.university_name == "Test University"
        assert result.base_url == "https://test.edu"
        assert "faculty" in result.faculty_directory_patterns
        assert "people" in result.faculty_directory_patterns
        assert result.confidence_score == 0.3
    
    def test_analyze_page_structure(self, adapter):
        """Test page structure analysis."""
        html_content = """
        <html>
            <body>
                <table>
                    <tr><td>Faculty 1</td></tr>
                    <tr><td>Faculty 2</td></tr>
                </table>
                <div class="grid">
                    <div class="faculty">Dr. Smith</div>
                    <div class="faculty">Dr. Jones</div>
                </div>
                <img src="/faculty/smith.jpg" alt="Dr. Smith">
                <div class="pagination">
                    <a href="?page=2">Next</a>
                </div>
            </body>
        </html>
        """
        
        soup = BeautifulSoup(html_content, 'html.parser')
        analysis = adapter._analyze_page_structure(soup)
        
        assert analysis['has_table'] is True
        assert analysis['has_grid'] is True
        assert analysis['has_images'] is True
        assert analysis['has_pagination'] is True
        assert analysis['faculty_count'] >= 2
    
    @pytest.mark.asyncio
    async def test_close(self, adapter):
        """Test adapter cleanup."""
        await adapter.close()
        # Should not raise any exceptions


class TestAdaptiveFacultyCrawler:
    """Test the AdaptiveFacultyCrawler class."""
    
    @pytest.fixture
    def crawler(self):
        """Create an AdaptiveFacultyCrawler instance for testing."""
        return AdaptiveFacultyCrawler(
            cache_client={},
            enable_lab_discovery=True,
            enable_external_search=False
        )
    
    def test_initialization(self, crawler):
        """Test crawler initialization."""
        assert crawler.university_adapter is not None
        assert crawler.data_cleaner is not None
        assert crawler.enable_lab_discovery is True
        assert crawler.link_heuristics is not None
        assert crawler.lab_classifier is not None
        assert crawler.site_search is None  # External search disabled
        assert crawler.session is not None
        assert isinstance(crawler.stats, dict)
    
    def test_extract_field_success(self, crawler):
        """Test successful field extraction."""
        html_content = """
        <div>
            <h1 class="name">Dr. John Smith</h1>
            <p class="title">Professor</p>
            <a href="mailto:smith@test.edu">smith@test.edu</a>
        </div>
        """
        
        element = BeautifulSoup(html_content, 'html.parser')
        
        # Test name extraction
        name = crawler._extract_field(element, '.name')
        assert name == "Dr. John Smith"
        
        # Test title extraction
        title = crawler._extract_field(element, '.title')
        assert title == "Professor"
        
        # Test email extraction
        email = crawler._extract_field(element, 'a[href^="mailto:"]')
        assert email == "smith@test.edu"
    
    def test_create_empty_result(self, crawler):
        """Test empty result creation."""
        result = crawler._create_empty_result("Test University", "Test error")
        
        assert result['university_name'] == "Test University"
        assert result['base_url'] is None
        assert result['faculty'] == []
        assert result['success'] is False
        assert result['error'] == "Test error"
        assert result['metadata']['total_faculty'] == 0
        assert result['metadata']['lab_discovery_enabled'] is True
    
    @pytest.mark.asyncio
    async def test_close(self, crawler):
        """Test crawler cleanup."""
        await crawler.close()
        # Should not raise any exceptions


if __name__ == "__main__":
    pytest.main([__file__])
