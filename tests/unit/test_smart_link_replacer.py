"""
Unit tests for SmartLinkReplacer component.

Tests AI-enhanced academic link discovery and social media replacement
system with production-ready performance metrics.
"""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
import json
from lynnapse.core.smart_link_replacer import (
    SmartLinkReplacer, smart_replace_social_media_links
)


class TestSmartLinkReplacer:
    """Test cases for SmartLinkReplacer AI-assisted link replacement."""
    
    def test_initialization_without_ai(self):
        """Test initializing SmartLinkReplacer without AI assistance."""
        replacer = SmartLinkReplacer(enable_ai_assistance=False)
        
        assert replacer.enable_ai_assistance == False
        assert replacer.openai_client is None
        assert replacer.session_stats is not None
    
    def test_initialization_with_ai(self):
        """Test initializing SmartLinkReplacer with AI assistance."""
        replacer = SmartLinkReplacer(
            openai_api_key="test-key",
            enable_ai_assistance=True
        )
        
        assert replacer.enable_ai_assistance == True
        assert replacer.openai_client is not None
    
    def test_social_media_identification(self, smart_link_replacer):
        """Test identification of social media links."""
        faculty_with_social = {
            "name": "Dr. John Smith",
            "profile_url": "https://linkedin.com/in/johnsmith",
            "personal_website": "https://twitter.com/johnsmith",
            "lab_website": "https://coglab.stanford.edu"  # Not social media
        }
        
        social_fields = smart_link_replacer._identify_social_media_fields(faculty_with_social)
        
        assert "profile_url" in social_fields
        assert "personal_website" in social_fields
        assert "lab_website" not in social_fields  # Should not identify lab as social media
    
    def test_academic_candidate_generation(self, smart_link_replacer):
        """Test generation of academic URL candidates."""
        faculty_info = {
            "name": "Dr. John Smith",
            "university": "Stanford University",
            "department": "Psychology",
            "research_interests": ["cognitive psychology", "memory"]
        }
        
        candidates = smart_link_replacer._generate_academic_candidates(faculty_info)
        
        # Should generate multiple candidate URLs
        assert len(candidates) >= 10
        
        # Should include Google Scholar patterns
        scholar_candidates = [c for c in candidates if "scholar.google.com" in c]
        assert len(scholar_candidates) >= 1
        
        # Should include university domain patterns
        stanford_candidates = [c for c in candidates if "stanford.edu" in c]
        assert len(stanford_candidates) >= 3
        
        # Should include name variations
        name_variations = [c for c in candidates if "john" in c.lower() and "smith" in c.lower()]
        assert len(name_variations) >= 5
    
    @pytest.mark.asyncio
    async def test_candidate_validation_success(self, smart_link_replacer, mock_aiohttp):
        """Test validation of academic URL candidates."""
        candidates = [
            "https://scholar.google.com/citations?user=test123",
            "https://psychology.stanford.edu/faculty/john-smith",
            "https://broken.edu/faculty/john-smith"
        ]
        
        # Mock responses
        mock_aiohttp.get(candidates[0], status=200, headers={"Content-Type": "text/html"})
        mock_aiohttp.get(candidates[1], status=200, headers={"Content-Type": "text/html"})
        mock_aiohttp.get(candidates[2], status=404)
        
        valid_urls = await smart_link_replacer._validate_candidates(candidates, max_concurrent=3)
        
        # Should find 2 valid URLs
        assert len(valid_urls) == 2
        assert candidates[0] in valid_urls
        assert candidates[1] in valid_urls
        assert candidates[2] not in valid_urls
    
    @pytest.mark.asyncio
    async def test_ai_enhanced_search_mock(self, mock_openai_api):
        """Test AI-enhanced search with mocked OpenAI API."""
        replacer = SmartLinkReplacer(
            openai_api_key="test-key",
            enable_ai_assistance=True
        )
        
        faculty_info = {
            "name": "Dr. John Smith",
            "university": "Stanford University",
            "research_interests": ["cognitive psychology"]
        }
        
        with patch.object(replacer, 'openai_client') as mock_client:
            mock_response = MagicMock()
            mock_response.choices = [
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
                        "Dr. John Smith cognitive psychology Stanford",
                        "John Smith faculty psychology scholar"
                    ]
                })))
            ]
            mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
            
            enhanced_urls = await replacer._ai_enhanced_search(faculty_info)
            
            assert len(enhanced_urls) >= 1
            assert any("scholar.google.com" in url for url in enhanced_urls)
    
    @pytest.mark.asyncio
    async def test_replace_social_media_links_basic(self, smart_link_replacer, mock_aiohttp):
        """Test basic social media link replacement without AI."""
        faculty_data = [
            {
                "name": "Dr. John Smith",
                "university": "Stanford University",
                "department": "Psychology",
                "profile_url": "https://linkedin.com/in/johnsmith",
                "research_interests": ["cognitive psychology"]
            }
        ]
        
        # Mock successful academic URL
        mock_aiohttp.get("https://psychology.stanford.edu/faculty/john-smith", status=200)
        mock_aiohttp.get("https://scholar.google.com/citations", status=200)
        
        enhanced_faculty, report = await smart_link_replacer.replace_social_media_links(faculty_data)
        
        # Should process the faculty member
        assert len(enhanced_faculty) == 1
        assert "replacement_attempted" in enhanced_faculty[0]
        
        # Should generate report
        assert "faculty_processed" in report
        assert "social_media_links_found" in report
        assert "replacement_success_rate" in report
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, mock_openai_api):
        """Test cost tracking for AI-assisted operations."""
        replacer = SmartLinkReplacer(
            openai_api_key="test-key",
            enable_ai_assistance=True
        )
        
        faculty_data = [
            {
                "name": "Dr. John Smith",
                "profile_url": "https://linkedin.com/in/johnsmith",
                "university": "Stanford University"
            }
        ]
        
        with patch.object(replacer, 'openai_client') as mock_client:
            mock_client.chat.completions.create = AsyncMock(return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content='{"academic_urls": [], "search_queries": []}'))]
            ))
            
            enhanced_faculty, report = await replacer.replace_social_media_links(faculty_data)
            
            # Should track AI costs
            assert "ai_assistance_cost" in report
            assert report["ai_assistance_cost"] >= 0
            assert "ai_calls_made" in report
    
    def test_name_variation_generation(self, smart_link_replacer):
        """Test generation of name variations for search."""
        variations = smart_link_replacer._generate_name_variations("Dr. John Robert Smith")
        
        expected_variations = {
            "john-smith", "j-smith", "john.smith", "j.smith",
            "johnsmith", "jsmith", "john_smith", "j_smith"
        }
        
        # Should generate multiple formats
        assert len(variations) >= 6
        
        # Should include expected variations
        for expected in expected_variations:
            assert any(expected in var for var in variations)
    
    def test_university_domain_extraction(self, smart_link_replacer):
        """Test extraction of university domains."""
        test_cases = [
            ("Stanford University", ["stanford.edu"]),
            ("Carnegie Mellon University", ["cmu.edu"]),
            ("University of California, Berkeley", ["berkeley.edu", "ucberkeley.edu"]),
            ("MIT", ["mit.edu"])
        ]
        
        for university_name, expected_domains in test_cases:
            domains = smart_link_replacer._extract_university_domains(university_name)
            
            # Should find at least one expected domain
            assert any(domain in domains for domain in expected_domains), f"Failed for {university_name}"
    
    @pytest.mark.asyncio
    async def test_concurrent_processing(self, smart_link_replacer, mock_aiohttp):
        """Test concurrent processing of multiple faculty members."""
        faculty_data = [
            {
                "name": f"Dr. Faculty {i}",
                "profile_url": f"https://linkedin.com/in/faculty{i}",
                "university": "Test University"
            }
            for i in range(10)
        ]
        
        # Mock responses for all potential academic URLs
        for i in range(20):  # More than enough mocks
            mock_aiohttp.get(f"https://test.edu/faculty/faculty{i}", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/citations?user=faculty{i}", status=200)
        
        import time
        start_time = time.time()
        
        enhanced_faculty, report = await smart_link_replacer.replace_social_media_links(
            faculty_data, max_concurrent=5
        )
        
        end_time = time.time()
        elapsed = end_time - start_time
        
        # Should process all faculty
        assert len(enhanced_faculty) == 10
        
        # Should complete in reasonable time with concurrency
        assert elapsed < 10.0  # Should finish in under 10 seconds
    
    def test_quality_scoring_academic_links(self, smart_link_replacer):
        """Test quality scoring for discovered academic links."""
        # Test high-quality academic links
        google_scholar_score = smart_link_replacer._score_academic_link("https://scholar.google.com/citations?user=abc123")
        university_profile_score = smart_link_replacer._score_academic_link("https://psychology.stanford.edu/faculty/john-smith")
        personal_site_score = smart_link_replacer._score_academic_link("https://stanford.edu/~jsmith")
        
        # Test lower-quality links
        generic_score = smart_link_replacer._score_academic_link("https://example.com/john-smith")
        
        # Quality ranking should be: Google Scholar > University Profile > Personal Site > Generic
        assert google_scholar_score >= university_profile_score
        assert university_profile_score >= personal_site_score
        assert personal_site_score > generic_score
        
        # All academic links should score reasonably high
        assert google_scholar_score >= 0.8
        assert university_profile_score >= 0.7
    
    @pytest.mark.asyncio
    async def test_error_handling_invalid_faculty(self, smart_link_replacer):
        """Test error handling with invalid faculty data."""
        invalid_faculty_data = [
            {},  # Empty faculty
            {"name": ""},  # Empty name
            {"name": None, "profile_url": "https://linkedin.com/in/test"},  # None name
            {"name": "Valid Name"}  # No social media links
        ]
        
        enhanced_faculty, report = await smart_link_replacer.replace_social_media_links(invalid_faculty_data)
        
        # Should handle all entries gracefully
        assert len(enhanced_faculty) == len(invalid_faculty_data)
        
        # Should report processing stats
        assert "faculty_processed" in report
        assert "errors_encountered" in report
    
    @pytest.mark.asyncio
    async def test_ai_assistance_fallback(self, mock_openai_api):
        """Test fallback when AI assistance fails."""
        replacer = SmartLinkReplacer(
            openai_api_key="test-key",
            enable_ai_assistance=True
        )
        
        faculty_data = [
            {
                "name": "Dr. John Smith",
                "profile_url": "https://linkedin.com/in/johnsmith",
                "university": "Stanford University"
            }
        ]
        
        with patch.object(replacer, 'openai_client') as mock_client:
            # Mock AI failure
            mock_client.chat.completions.create = AsyncMock(side_effect=Exception("API Error"))
            
            enhanced_faculty, report = await replacer.replace_social_media_links(faculty_data)
            
            # Should fallback to traditional methods
            assert len(enhanced_faculty) == 1
            assert "ai_assistance_failed" in report
            assert report["ai_assistance_failed"] == True
    
    def test_session_statistics_tracking(self, smart_link_replacer):
        """Test session statistics tracking."""
        # Initial stats should be empty
        stats = smart_link_replacer.get_session_stats()
        assert stats["faculty_processed"] == 0
        assert stats["social_links_found"] == 0
        assert stats["successful_replacements"] == 0
        
        # Update stats manually (simulating processing)
        smart_link_replacer.session_stats["faculty_processed"] = 5
        smart_link_replacer.session_stats["social_links_found"] = 3
        smart_link_replacer.session_stats["successful_replacements"] = 2
        
        updated_stats = smart_link_replacer.get_session_stats()
        assert updated_stats["faculty_processed"] == 5
        assert updated_stats["social_links_found"] == 3
        assert updated_stats["successful_replacements"] == 2
    
    @pytest.mark.asyncio
    async def test_integration_with_website_validator(self, smart_link_replacer, mock_aiohttp):
        """Test integration with WebsiteValidator for link validation."""
        faculty_data = [
            {
                "name": "Dr. John Smith",
                "profile_url": "https://linkedin.com/in/johnsmith",
                "profile_url_validation": {
                    "type": "social_media",
                    "is_accessible": True,
                    "confidence": 0.95
                }
            }
        ]
        
        # Mock academic URL response
        mock_aiohttp.get("https://psychology.stanford.edu/faculty/john-smith", status=200)
        
        enhanced_faculty, report = await smart_link_replacer.replace_social_media_links(faculty_data)
        
        # Should use existing validation data
        assert len(enhanced_faculty) == 1
        assert "profile_url_validation" in enhanced_faculty[0]
    
    def test_research_interest_matching(self, smart_link_replacer):
        """Test matching research interests with potential URLs."""
        faculty_info = {
            "research_interests": ["cognitive psychology", "memory", "neuroscience"]
        }
        
        url_candidates = [
            "https://coglab.stanford.edu",                    # Should match "cognitive"
            "https://neurolab.mit.edu",                      # Should match "neuroscience" 
            "https://memorylab.university.edu",              # Should match "memory"
            "https://chemistry.university.edu"               # Should not match
        ]
        
        scored_candidates = smart_link_replacer._score_candidates_by_research_interests(
            url_candidates, faculty_info
        )
        
        # Should rank URLs by research interest relevance
        cog_score = next(sc for sc in scored_candidates if "coglab" in sc["url"])["score"]
        neuro_score = next(sc for sc in scored_candidates if "neurolab" in sc["url"])["score"]
        memory_score = next(sc for sc in scored_candidates if "memorylab" in sc["url"])["score"]
        chem_score = next(sc for sc in scored_candidates if "chemistry" in sc["url"])["score"]
        
        assert cog_score > chem_score
        assert neuro_score > chem_score
        assert memory_score > chem_score
    
    @pytest.mark.asyncio
    async def test_performance_benchmarks(self, smart_link_replacer, performance_monitor, mock_aiohttp):
        """Test performance benchmarks for link replacement."""
        faculty_data = [
            {
                "name": f"Dr. Faculty {i}",
                "profile_url": "https://linkedin.com/in/test",
                "university": "Test University"
            }
            for i in range(20)  # 20 faculty members
        ]
        
        # Mock responses
        for i in range(50):  # Plenty of mock responses
            mock_aiohttp.get(f"https://test.edu/faculty/test{i}", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/test{i}", status=200)
        
        performance_monitor.start()
        
        enhanced_faculty, report = await smart_link_replacer.replace_social_media_links(faculty_data)
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Should process efficiently
        assert len(enhanced_faculty) == 20
        assert results["time_efficient"]  # Under 30 seconds
        assert results["memory_efficient"]  # Under 200MB
        
        # Should maintain good success rates
        assert report["faculty_processed"] == 20 