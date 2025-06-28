"""
Unit tests for WebsiteValidator component.

Tests comprehensive link categorization and quality assessment system
with social media detection and academic relevance scoring.
"""

import pytest
from unittest.mock import patch, AsyncMock
from lynnapse.core.website_validator import (
    WebsiteValidator, LinkType, validate_faculty_websites,
    identify_secondary_scraping_candidates
)


class TestWebsiteValidator:
    """Test cases for WebsiteValidator link categorization."""
    
    def test_social_media_detection(self, website_validator):
        """Test detection of social media platforms."""
        # Test major social media platforms
        social_urls = [
            "https://facebook.com/user",
            "https://twitter.com/user",
            "https://x.com/user",
            "https://linkedin.com/in/user",
            "https://instagram.com/user",
            "https://youtube.com/user",
            "https://tiktok.com/@user",
            "https://medium.com/@user",
            "https://github.io/user"
        ]
        
        for url in social_urls:
            link_type = website_validator._classify_link_type(url)
            assert link_type == LinkType.SOCIAL_MEDIA, f"Failed to detect {url} as social media"
    
    def test_academic_profile_detection(self, website_validator):
        """Test detection of academic profile platforms."""
        academic_urls = [
            "https://scholar.google.com/citations?user=abc123",
            "https://researchgate.net/profile/John_Smith",
            "https://academia.edu/JohnSmith",
            "https://orcid.org/0000-0000-0000-0000"
        ]
        
        for url in academic_urls:
            link_type = website_validator._classify_link_type(url)
            assert link_type in [LinkType.GOOGLE_SCHOLAR, LinkType.ACADEMIC_PROFILE], f"Failed to detect {url} as academic"
    
    def test_university_profile_detection(self, website_validator):
        """Test detection of university profile pages."""
        university_urls = [
            "https://psychology.stanford.edu/faculty/john-smith",
            "https://www.cmu.edu/dietrich/psychology/directory/john-smith",
            "https://university.edu/faculty/profiles/john-smith",
            "https://college.edu/people/john-smith"
        ]
        
        for url in university_urls:
            link_type = website_validator._classify_link_type(url)
            assert link_type == LinkType.UNIVERSITY_PROFILE, f"Failed to detect {url} as university profile"
    
    def test_personal_website_detection(self, website_validator):
        """Test detection of personal academic websites."""
        personal_urls = [
            "https://university.edu/~jsmith",
            "https://psychology.edu/faculty/jsmith",
            "https://personal.stanford.edu/john-smith",
            "https://www.johnsmith.org"
        ]
        
        for url in personal_urls:
            link_type = website_validator._classify_link_type(url)
            assert link_type in [LinkType.PERSONAL_WEBSITE, LinkType.UNIVERSITY_PROFILE], f"Failed to detect {url} as personal/academic"
    
    def test_lab_website_detection(self, website_validator):
        """Test detection of research lab websites."""
        lab_urls = [
            "https://coglab.stanford.edu",
            "https://psychology.university.edu/research/memory-lab",
            "https://neurolab.mit.edu",
            "https://lab.university.edu/cognitive-science"
        ]
        
        for url in lab_urls:
            link_type = website_validator._classify_link_type(url)
            assert link_type == LinkType.LAB_WEBSITE, f"Failed to detect {url} as lab website"
    
    def test_publication_detection(self, website_validator):
        """Test detection of publication links."""
        publication_urls = [
            "https://doi.org/10.1038/nature12345",
            "https://pubmed.ncbi.nlm.nih.gov/12345678",
            "https://arxiv.org/abs/1234.5678",
            "https://psycnet.apa.org/record/2023-12345-001"
        ]
        
        for url in publication_urls:
            link_type = website_validator._classify_link_type(url)
            assert link_type == LinkType.PUBLICATION, f"Failed to detect {url} as publication"
    
    @pytest.mark.asyncio
    async def test_link_accessibility_check(self, website_validator, mock_aiohttp):
        """Test link accessibility validation."""
        # Mock successful response
        mock_aiohttp.get("https://test.edu/faculty", status=200, headers={"Content-Type": "text/html"})
        
        is_accessible, status_code, response_time = await website_validator._check_link_accessibility("https://test.edu/faculty")
        
        assert is_accessible == True
        assert status_code == 200
        assert response_time >= 0
    
    @pytest.mark.asyncio
    async def test_link_accessibility_failure(self, website_validator, mock_aiohttp):
        """Test handling of inaccessible links."""
        # Mock failed response
        mock_aiohttp.get("https://broken.edu/faculty", status=404)
        
        is_accessible, status_code, response_time = await website_validator._check_link_accessibility("https://broken.edu/faculty")
        
        assert is_accessible == False
        assert status_code == 404
    
    def test_quality_scoring_university_profile(self, website_validator):
        """Test quality scoring for university profiles."""
        score = website_validator._calculate_quality_score(
            LinkType.UNIVERSITY_PROFILE,
            "https://psychology.stanford.edu/faculty/john-smith",
            is_accessible=True,
            status_code=200,
            response_time=0.5
        )
        
        assert score >= 0.8  # University profiles should score highly
        assert score <= 1.0  # Should not exceed maximum
    
    def test_quality_scoring_google_scholar(self, website_validator):
        """Test quality scoring for Google Scholar profiles."""
        score = website_validator._calculate_quality_score(
            LinkType.GOOGLE_SCHOLAR,
            "https://scholar.google.com/citations?user=abc123",
            is_accessible=True,
            status_code=200,
            response_time=0.3
        )
        
        assert score >= 0.9  # Google Scholar should score very highly
    
    def test_quality_scoring_social_media(self, website_validator):
        """Test quality scoring for social media links."""
        score = website_validator._calculate_quality_score(
            LinkType.SOCIAL_MEDIA,
            "https://facebook.com/user",
            is_accessible=True,
            status_code=200,
            response_time=0.4
        )
        
        assert score >= 0.8  # Social media detection should be confident
        assert score < 0.95   # But lower than academic sources
    
    def test_quality_scoring_broken_link(self, website_validator):
        """Test quality scoring for broken links."""
        score = website_validator._calculate_quality_score(
            LinkType.INVALID,
            "https://broken.edu/faculty",
            is_accessible=False,
            status_code=404,
            response_time=10.0
        )
        
        assert score <= 0.3  # Broken links should score poorly
    
    @pytest.mark.asyncio
    async def test_validate_single_link(self, website_validator, mock_aiohttp):
        """Test validation of a single link."""
        # Mock Google Scholar response
        mock_aiohttp.get("https://scholar.google.com/citations?user=abc123", status=200)
        
        validation = await website_validator.validate_link("https://scholar.google.com/citations?user=abc123")
        
        assert validation["type"] == "google_scholar"
        assert validation["is_accessible"] == True
        assert validation["confidence"] >= 0.9
        assert "title" in validation
    
    @pytest.mark.asyncio
    async def test_validate_faculty_websites_integration(self, sample_faculty_data, mock_aiohttp):
        """Test complete faculty website validation."""
        # Mock all responses
        mock_aiohttp.get("https://test.edu/faculty/john-smith", status=200)
        mock_aiohttp.get("https://scholar.google.com/citations?user=abc123", status=200)
        mock_aiohttp.get("https://linkedin.com/in/janedoe", status=200)
        mock_aiohttp.get("https://coglab.test.edu", status=200)
        
        validated_faculty, report = await validate_faculty_websites(sample_faculty_data)
        
        # Should validate all faculty
        assert len(validated_faculty) == len(sample_faculty_data)
        
        # Should add validation metadata
        for faculty in validated_faculty:
            if faculty.get("profile_url"):
                assert f"profile_url_validation" in faculty
            if faculty.get("personal_website"):
                assert f"personal_website_validation" in faculty
            if faculty.get("lab_website"):
                assert f"lab_website_validation" in faculty
        
        # Should generate report
        assert "total_links_validated" in report
        assert "link_types_found" in report
        assert "accessibility_stats" in report
    
    def test_identify_secondary_scraping_candidates(self, sample_faculty_data):
        """Test identification of faculty needing secondary scraping."""
        # Add validation data to simulate social media links
        faculty_with_social = sample_faculty_data.copy()
        faculty_with_social[1]["profile_url_validation"] = {
            "type": "social_media",
            "is_accessible": True,
            "confidence": 0.95
        }
        
        candidates, good_links = identify_secondary_scraping_candidates(faculty_with_social)
        
        # Should identify faculty with social media links
        assert len(candidates) >= 1
        assert any(faculty.get("needs_secondary_scraping") for faculty in candidates)
        
        # Should preserve faculty with good links
        assert len(good_links) >= 2
    
    def test_social_media_domain_coverage(self, website_validator):
        """Test coverage of social media domains."""
        # Test international platforms
        international_urls = [
            "https://weibo.com/user",      # Chinese
            "https://vk.com/user",         # Russian
            "https://ok.ru/user",          # Russian
            "https://line.me/user"         # Asian
        ]
        
        for url in international_urls:
            link_type = website_validator._classify_link_type(url)
            assert link_type == LinkType.SOCIAL_MEDIA, f"Failed to detect international platform {url}"
    
    def test_edge_cases_link_classification(self, website_validator):
        """Test edge cases in link classification."""
        # Empty URL
        link_type = website_validator._classify_link_type("")
        assert link_type == LinkType.INVALID
        
        # None URL
        link_type = website_validator._classify_link_type(None)
        assert link_type == LinkType.INVALID
        
        # Malformed URL
        link_type = website_validator._classify_link_type("not-a-url")
        assert link_type == LinkType.INVALID
        
        # Very long URL
        long_url = "https://university.edu/" + "a" * 1000
        link_type = website_validator._classify_link_type(long_url)
        assert link_type in [LinkType.UNIVERSITY_PROFILE, LinkType.UNKNOWN]  # Should handle gracefully
    
    def test_domain_authority_scoring(self, website_validator):
        """Test domain authority bonus scoring."""
        # .edu domains should get bonus
        edu_score = website_validator._calculate_domain_authority_bonus("https://stanford.edu/faculty")
        org_score = website_validator._calculate_domain_authority_bonus("https://example.org/faculty")
        com_score = website_validator._calculate_domain_authority_bonus("https://example.com/faculty")
        
        assert edu_score > org_score
        assert edu_score > com_score
        assert edu_score >= 0.1  # Should get measurable bonus
    
    def test_response_time_penalty(self, website_validator):
        """Test response time impact on quality scoring."""
        fast_score = website_validator._calculate_quality_score(
            LinkType.UNIVERSITY_PROFILE, "https://test.edu", True, 200, 0.1
        )
        
        slow_score = website_validator._calculate_quality_score(
            LinkType.UNIVERSITY_PROFILE, "https://test.edu", True, 200, 5.0
        )
        
        assert fast_score > slow_score  # Faster response should score better
    
    @pytest.mark.asyncio
    async def test_concurrent_validation(self, sample_faculty_data, mock_aiohttp):
        """Test concurrent link validation performance."""
        # Mock responses for all links
        mock_aiohttp.get("https://test.edu/faculty/john-smith", status=200)
        mock_aiohttp.get("https://scholar.google.com/citations?user=abc123", status=200)
        mock_aiohttp.get("https://linkedin.com/in/janedoe", status=200)
        mock_aiohttp.get("https://coglab.test.edu", status=200)
        
        # Test with performance monitoring
        import time
        start_time = time.time()
        
        validated_faculty, report = await validate_faculty_websites(
            sample_faculty_data, 
            max_concurrent=5
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should complete quickly with concurrent processing
        assert elapsed < 5.0  # Should finish in under 5 seconds
        assert len(validated_faculty) == len(sample_faculty_data)
    
    def test_link_type_enum_completeness(self):
        """Test that all expected link types are defined."""
        expected_types = {
            "PERSONAL_WEBSITE", "GOOGLE_SCHOLAR", "UNIVERSITY_PROFILE",
            "ACADEMIC_PROFILE", "LAB_WEBSITE", "SOCIAL_MEDIA", 
            "PUBLICATION", "INVALID", "UNKNOWN"
        }
        
        actual_types = {link_type.name for link_type in LinkType}
        
        assert expected_types.issubset(actual_types), f"Missing link types: {expected_types - actual_types}"
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self, website_validator, mock_aiohttp):
        """Test handling of validation errors."""
        # Mock timeout/connection error
        mock_aiohttp.get("https://timeout.edu/faculty", exception=Exception("Connection timeout"))
        
        validation = await website_validator.validate_link("https://timeout.edu/faculty")
        
        # Should handle errors gracefully
        assert validation["type"] == "invalid"
        assert validation["is_accessible"] == False
        assert "error" in validation
    
    def test_academic_relevance_assessment(self, website_validator):
        """Test academic relevance scoring."""
        # Academic URLs should score higher
        academic_relevance = website_validator._assess_academic_relevance("https://psychology.stanford.edu/faculty/john-smith")
        social_relevance = website_validator._assess_academic_relevance("https://facebook.com/user")
        random_relevance = website_validator._assess_academic_relevance("https://randomsite.com")
        
        assert academic_relevance > social_relevance
        assert academic_relevance > random_relevance
        assert academic_relevance >= 0.8  # Should be highly relevant
    
    def test_performance_benchmarks(self, website_validator, performance_monitor):
        """Test performance of link classification."""
        performance_monitor.start()
        
        # Classify many links quickly
        test_urls = [
            "https://scholar.google.com/citations?user=abc123",
            "https://facebook.com/user",
            "https://university.edu/faculty/john-smith",
            "https://twitter.com/user",
            "https://coglab.stanford.edu"
        ] * 20  # 100 total links
        
        for url in test_urls:
            website_validator._classify_link_type(url)
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Should be very fast for classification
        assert results["elapsed_time_seconds"] < 0.5  # Under 0.5 seconds for 100 classifications
        assert results["memory_efficient"] 