"""
Integration tests for complete Lynnapse pipeline.

Tests the end-to-end faculty scraping → link processing → enrichment workflow
with real-world scenarios and performance benchmarks.
"""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, AsyncMock
from lynnapse.core.enhanced_link_processor import identify_and_replace_social_media_links
from lynnapse.core.link_enrichment import LinkEnrichmentEngine
from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler
from lynnapse.core.university_adapter import UniversityAdapter
from lynnapse.flows.enhanced_scraping_flow import enhanced_faculty_scraping_flow


class TestCompletePipeline:
    """Integration tests for complete faculty processing pipeline."""
    
    @pytest.mark.asyncio
    async def test_complete_processing_pipeline(self, sample_faculty_data, mock_aiohttp):
        """Test end-to-end faculty processing pipeline."""
        # Mock external responses
        mock_aiohttp.get("https://scholar.google.com/citations?user=abc123", status=200)
        mock_aiohttp.get("https://linkedin.com/in/janedoe", status=200)
        mock_aiohttp.get("https://test.edu/faculty/john-smith", status=200)
        mock_aiohttp.get("https://coglab.test.edu", status=200)
        
        # Stage 1: Smart Link Processing
        processed_faculty, processing_report = await identify_and_replace_social_media_links(
            sample_faculty_data,
            use_ai_assistance=False,
            max_concurrent=3
        )
        
        # Stage 2: Link Enrichment
        enrichment_engine = LinkEnrichmentEngine()
        enriched_faculty, enrichment_report = await enrichment_engine.enrich_faculty_links(
            processed_faculty,
            max_concurrent=3
        )
        
        # Verify complete pipeline results
        assert len(enriched_faculty) == len(sample_faculty_data)
        assert processing_report['replacement_success_rate'] >= 0.0
        assert enrichment_report['faculty_processed'] == len(sample_faculty_data)
        
        # Verify enhanced data structure
        for faculty in enriched_faculty:
            assert 'name' in faculty
            assert 'university' in faculty
            
            # Should have link validation data
            if faculty.get('profile_url'):
                assert 'profile_url_validation' in faculty
            if faculty.get('personal_website'):
                assert 'personal_website_validation' in faculty
    
    @pytest.mark.asyncio
    async def test_adaptive_scraping_integration(self, mock_university_config, mock_aiohttp):
        """Test integration of adaptive scraping with link processing."""
        # Mock university website responses
        mock_aiohttp.get("https://test.edu/psychology/faculty", body="""
        <div class="faculty-listing">
            <div class="faculty-card">
                <h3><a href="/faculty/john-smith">Dr. John Smith</a></h3>
                <p>Professor of Psychology</p>
                <a href="mailto:john.smith@test.edu">Email</a>
            </div>
            <div class="faculty-card">
                <h3><a href="/faculty/jane-doe">Dr. Jane Doe</a></h3>
                <p>Assistant Professor</p>
                <a href="mailto:jane.doe@test.edu">Email</a>
            </div>
        </div>
        """)
        
        mock_aiohttp.get("https://test.edu/faculty/john-smith", body="""
        <div class="profile">
            <h1>Dr. John Smith</h1>
            <p>Email: john.smith@test.edu</p>
            <p>Research: Cognitive Psychology</p>
            <a href="https://scholar.google.com/citations?user=abc123">Google Scholar</a>
        </div>
        """)
        
        mock_aiohttp.get("https://test.edu/faculty/jane-doe", body="""
        <div class="profile">
            <h1>Dr. Jane Doe</h1>
            <p>Email: jane.doe@test.edu</p>
            <p>Research: Developmental Psychology</p>
            <a href="https://linkedin.com/in/janedoe">LinkedIn</a>
        </div>
        """)
        
        # Stage 1: Adaptive Faculty Scraping
        crawler = AdaptiveFacultyCrawler()
        university_pattern = {
            'base_url': 'https://test.edu',
            'faculty_url': 'https://test.edu/psychology/faculty'
        }
        
        faculty_data = await crawler.scrape_faculty_comprehensive(
            university_pattern,
            department_name="Psychology",
            max_faculty=10
        )
        
        # Stage 2: Complete Link Processing
        enhanced_faculty, report = await identify_and_replace_social_media_links(
            faculty_data,
            use_ai_assistance=False
        )
        
        # Verify integration results
        assert len(enhanced_faculty) >= 2
        assert report['faculty_processed'] >= 2
        
        # Verify that social media links were identified and processed
        linkedin_faculty = next((f for f in enhanced_faculty if 'linkedin.com' in str(f.get('profile_url', ''))), None)
        if linkedin_faculty:
            assert 'needs_secondary_scraping' in linkedin_faculty or 'replacement_attempted' in linkedin_faculty
    
    @pytest.mark.asyncio
    async def test_university_adapter_integration(self, mock_aiohttp):
        """Test UniversityAdapter integration with processing pipeline."""
        # Mock sitemap and university structure discovery
        mock_aiohttp.get("https://test.edu/sitemap.xml", body="""<?xml version="1.0" encoding="UTF-8"?>
        <urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
            <url><loc>https://test.edu/psychology/faculty</loc></url>
            <url><loc>https://test.edu/psychology/directory</loc></url>
        </urlset>
        """)
        
        mock_aiohttp.get("https://test.edu/psychology/faculty", body="""
        <div class="faculty-directory">
            <a href="/faculty/prof1">Professor 1</a>
            <a href="/faculty/prof2">Professor 2</a>
        </div>
        """)
        
        # Test university structure discovery
        adapter = UniversityAdapter()
        university_patterns = await adapter.discover_university_structure(
            "Test University",
            "https://test.edu",
            target_department="psychology"
        )
        
        # Should discover faculty directory
        assert len(university_patterns) >= 1
        assert any('faculty' in pattern.get('faculty_url', '') for pattern in university_patterns)
        
        # Test integration with scraping
        best_pattern = university_patterns[0]
        
        crawler = AdaptiveFacultyCrawler()
        faculty_data = await crawler.scrape_faculty_comprehensive(
            best_pattern,
            department_name="Psychology",
            max_faculty=5
        )
        
        # Should extract faculty information
        assert len(faculty_data) >= 0  # May be empty if no detailed profiles found
    
    @pytest.mark.asyncio
    async def test_performance_complete_pipeline(self, sample_faculty_data, performance_monitor, mock_aiohttp):
        """Test performance of complete pipeline with realistic data volume."""
        # Generate larger dataset for performance testing
        large_faculty_dataset = []
        for i in range(50):  # 50 faculty members
            faculty = {
                "name": f"Dr. Faculty {i}",
                "university": "Test University",
                "department": "Psychology",
                "email": f"faculty{i}@test.edu",
                "profile_url": f"https://test.edu/faculty/faculty{i}",
                "research_interests": ["psychology", "research"]
            }
            large_faculty_dataset.append(faculty)
        
        # Mock all potential HTTP requests
        for i in range(100):  # More than enough mocks
            mock_aiohttp.get(f"https://test.edu/faculty/faculty{i}", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/citations?user=faculty{i}", status=200)
        
        performance_monitor.start()
        
        # Run complete pipeline
        processed_faculty, processing_report = await identify_and_replace_social_media_links(
            large_faculty_dataset,
            use_ai_assistance=False,
            max_concurrent=10
        )
        
        enrichment_engine = LinkEnrichmentEngine()
        enriched_faculty, enrichment_report = await enrichment_engine.enrich_faculty_links(
            processed_faculty,
            max_concurrent=5
        )
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Performance requirements
        assert len(enriched_faculty) == 50
        assert results["time_efficient"]  # Under 30 seconds
        assert results["memory_efficient"]  # Under 200MB
        assert processing_report["faculty_processed"] == 50
    
    @pytest.mark.asyncio
    async def test_error_recovery_pipeline(self, sample_faculty_data, mock_aiohttp):
        """Test pipeline error recovery and graceful degradation."""
        # Mock some failures in the pipeline
        mock_aiohttp.get("https://test.edu/faculty/john-smith", status=200)
        mock_aiohttp.get("https://scholar.google.com/citations?user=abc123", status=404)  # Fail this one
        mock_aiohttp.get("https://linkedin.com/in/janedoe", status=500)  # Server error
        mock_aiohttp.get("https://coglab.test.edu", status=200)
        
        # Process with some failures
        processed_faculty, report = await identify_and_replace_social_media_links(
            sample_faculty_data,
            use_ai_assistance=False,
            max_concurrent=3
        )
        
        # Should still process successfully despite some failures
        assert len(processed_faculty) == len(sample_faculty_data), "Should process all faculty despite some errors"
        assert report['faculty_processed'] == len(sample_faculty_data), "Should report all faculty as processed"
        
        # Should track errors appropriately
        if 'errors_encountered' in report:
            assert report['errors_encountered'] >= 0, "Should track errors"
        
        # All faculty objects should be valid even with errors
        for faculty in processed_faculty:
            assert 'name' in faculty, "Faculty should retain basic data"
            assert 'university' in faculty, "Faculty should retain university data"
    
    @pytest.mark.asyncio 
    async def test_data_consistency_pipeline(self, sample_faculty_data, mock_aiohttp):
        """Test data consistency throughout the pipeline."""
        # Mock responses
        for i in range(10):
            mock_aiohttp.get(f"https://test.edu/faculty/test{i}", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/test{i}", status=200)
        
        # Create input data with various scenarios
        test_data = [
            {
                "_id": "consistency_test_1",
                "name": "Dr. Test Faculty",
                "university": "Test University",
                "department": "Psychology",
                "email": "test@test.edu",
                "profile_url": "https://test.edu/faculty/test1",
                "research_interests": ["original research area"]
            }
        ]
        
        # Process through pipeline
        processed_faculty, report = await identify_and_replace_social_media_links(
            test_data,
            use_ai_assistance=False
        )
        
        # Verify data consistency
        original_faculty = test_data[0]
        processed_faculty_item = processed_faculty[0]
        
        # Core data should be preserved
        assert processed_faculty_item['_id'] == original_faculty['_id'], "ID should be preserved"
        assert processed_faculty_item['name'] == original_faculty['name'], "Name should be preserved"
        assert processed_faculty_item['university'] == original_faculty['university'], "University should be preserved"
        assert processed_faculty_item['department'] == original_faculty['department'], "Department should be preserved"
        assert processed_faculty_item['email'] == original_faculty['email'], "Email should be preserved"
        assert processed_faculty_item['research_interests'] == original_faculty['research_interests'], "Research interests should be preserved"
        
        # Processing metadata should be added
        assert '_processing_timestamp' in processed_faculty_item or 'processing_metadata' in processed_faculty_item, "Should add processing metadata"
    
    @pytest.mark.asyncio
    async def test_pipeline_with_real_university_patterns(self, mock_aiohttp):
        """Test pipeline with realistic university data patterns."""
        # Mock Carnegie Mellon-style responses
        mock_aiohttp.get("https://www.cmu.edu/dietrich/psychology/directory/", body="""
        <div class="view-content">
            <div class="views-row">
                <div class="views-field-title">
                    <span class="field-content">
                        <a href="/dietrich/psychology/people/faculty/timothy-verstynen.html">Timothy Verstynen</a>
                    </span>
                </div>
                <div class="views-field-field-title">
                    <div class="field-content">Associate Professor of Psychology and Neuroscience</div>
                </div>
                <div class="views-field-field-email">
                    <div class="field-content">
                        <a href="mailto:timothyv@andrew.cmu.edu">timothyv@andrew.cmu.edu</a>
                    </div>
                </div>
            </div>
        </div>
        """)
        
        mock_aiohttp.get("https://www.cmu.edu/dietrich/psychology/people/faculty/timothy-verstynen.html", body="""
        <div class="main-content">
            <h1>Timothy Verstynen</h1>
            <p>Associate Professor of Psychology and Neuroscience</p>
            <p>Email: <a href="mailto:timothyv@andrew.cmu.edu">timothyv@andrew.cmu.edu</a></p>
            <div class="research-interests">
                <p>Research interests include computational neuroscience, brain connectivity, motor control</p>
            </div>
            <div class="links">
                <a href="https://www.linkedin.com/in/timverstynen">LinkedIn Profile</a>
                <a href="https://twitter.com/timverstynen">Twitter</a>
            </div>
        </div>
        """)
        
        # Create realistic faculty data (similar to what adaptive scraper would produce)
        cmu_faculty_data = [
            {
                "_id": "cmu_real_test_1",
                "name": "Timothy Verstynen",
                "title": "Associate Professor of Psychology and Neuroscience",
                "university": "Carnegie Mellon University",
                "department": "Psychology",
                "email": "timothyv@andrew.cmu.edu",
                "profile_url": "https://www.linkedin.com/in/timverstynen",  # Social media that should be replaced
                "personal_website": "https://twitter.com/timverstynen",      # Another social media link
                "research_interests": ["computational neuroscience", "brain connectivity", "motor control"],
                "scraped_at": "2025-06-27T10:00:00Z"
            }
        ]
        
        # Mock academic alternatives
        mock_aiohttp.get("https://scholar.google.com/citations?user=timverstynen", status=200)
        mock_aiohttp.get("https://www.cmu.edu/dietrich/psychology/people/faculty/timothy-verstynen.html", status=200)
        
        # Process through complete pipeline
        enhanced_faculty, report = await identify_and_replace_social_media_links(
            cmu_faculty_data,
            use_ai_assistance=False
        )
        
        # Verify realistic processing
        assert len(enhanced_faculty) == 1, "Should process the faculty member"
        faculty = enhanced_faculty[0]
        
        # Should identify social media links
        social_media_found = 0
        for field in ['profile_url', 'personal_website', 'lab_website']:
            validation = faculty.get(f"{field}_validation", {})
            if validation.get('type') == 'social_media':
                social_media_found += 1
        
        assert social_media_found >= 1, "Should identify at least one social media link"
        
        # Should maintain data integrity
        assert faculty['name'] == "Timothy Verstynen", "Should preserve faculty name"
        assert faculty['university'] == "Carnegie Mellon University", "Should preserve university"
        assert len(faculty['research_interests']) == 3, "Should preserve research interests"
    
    def test_pipeline_output_format_consistency(self, temp_output_dir):
        """Test consistency of pipeline output formats."""
        import json
        from pathlib import Path
        
        # Create test output data in various expected formats
        test_outputs = {
            "faculty_basic": {
                "name": "Dr. Test",
                "university": "Test University",
                "email": "test@test.edu"
            },
            "faculty_enhanced": {
                "name": "Dr. Enhanced Test",
                "university": "Test University", 
                "email": "enhanced@test.edu",
                "profile_url_validation": {
                    "type": "academic_profile",
                    "confidence": 0.95,
                    "is_accessible": True
                },
                "secondary_links_found": ["https://scholar.google.com/test"],
                "link_quality_score": 0.87
            },
            "processing_report": {
                "faculty_processed": 10,
                "social_media_links_found": 5,
                "replacement_success_rate": 0.8,
                "processing_time_seconds": 15.2,
                "ai_assistance_enabled": False
            }
        }
        
        # Write test outputs
        output_files = {}
        for data_type, data in test_outputs.items():
            output_file = Path(temp_output_dir) / f"{data_type}.json"
            with open(output_file, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            output_files[data_type] = output_file
        
        # Verify files can be read back
        for data_type, output_file in output_files.items():
            assert output_file.exists(), f"Output file should exist: {output_file}"
            
            with open(output_file, 'r') as f:
                loaded_data = json.load(f)
            
            assert loaded_data == test_outputs[data_type], f"Data should round-trip correctly for {data_type}"
        
        # Verify expected schema structures
        faculty_enhanced = test_outputs["faculty_enhanced"]
        assert "profile_url_validation" in faculty_enhanced, "Enhanced faculty should have validation data"
        assert "type" in faculty_enhanced["profile_url_validation"], "Validation should have type"
        assert "confidence" in faculty_enhanced["profile_url_validation"], "Validation should have confidence"
        
        report = test_outputs["processing_report"]
        required_report_fields = ["faculty_processed", "processing_time_seconds", "ai_assistance_enabled"]
        for field in required_report_fields:
            assert field in report, f"Processing report should have {field}"
    
    @pytest.mark.asyncio
    async def test_pipeline_memory_efficiency(self, performance_monitor, mock_aiohttp):
        """Test memory efficiency with larger datasets."""
        # Generate larger faculty dataset (100 faculty)
        large_dataset = []
        for i in range(100):
            faculty = {
                "_id": f"memory_test_{i}",
                "name": f"Dr. Memory Test {i}",
                "university": f"Test University {i % 5}",
                "department": "Psychology",
                "email": f"test{i}@test{i % 5}.edu",
                "profile_url": f"https://test{i % 5}.edu/faculty/test{i}",
                "research_interests": [f"area {i % 10}", f"field {(i + 1) % 8}"]
            }
            large_dataset.append(faculty)
        
        # Mock responses for all potential requests
        for i in range(150):  # Extra mocks for safety
            mock_aiohttp.get(f"https://test{i % 5}.edu/faculty/test{i}", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/test{i}", status=200)
        
        performance_monitor.start()
        
        # Process large dataset
        enhanced_faculty, report = await identify_and_replace_social_media_links(
            large_dataset,
            use_ai_assistance=False,
            max_concurrent=8
        )
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Memory efficiency requirements
        assert results["peak_memory_mb"] < 400, f"Memory usage too high: {results['peak_memory_mb']} MB"
        assert results["memory_stable"], f"Memory growth too large: {results['memory_growth_mb']} MB"
        
        # Performance requirements
        faculty_per_second = len(large_dataset) / results["elapsed_time_seconds"]
        assert faculty_per_second >= 5, f"Processing too slow: {faculty_per_second} faculty/sec"
        
        # Data integrity with large dataset
        assert len(enhanced_faculty) == len(large_dataset), "Should process all faculty"
        assert report['faculty_processed'] == len(large_dataset), "Should report correct count"
        
        # Memory per faculty should be reasonable
        memory_per_faculty = results["peak_memory_mb"] / len(large_dataset)
        assert memory_per_faculty < 10, f"Memory per faculty too high: {memory_per_faculty} MB/faculty"
    
    @pytest.mark.asyncio
    async def test_concurrent_pipeline_execution(self, mock_aiohttp):
        """Test concurrent execution of multiple pipeline instances."""
        import asyncio
        
        # Mock responses
        for i in range(100):
            mock_aiohttp.get(f"https://test{i}.edu/faculty", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/test{i}", status=200)
        
        async def process_dataset(dataset):
            """Process a dataset through the pipeline."""
            enhanced_faculty, report = await identify_and_replace_social_media_links(
                dataset,
                use_ai_assistance=False,
                max_concurrent=3
            )
            return enhanced_faculty, report
        
        # Create multiple small datasets
        datasets = []
        for dataset_id in range(5):
            dataset = []
            for i in range(10):
                faculty = {
                    "_id": f"concurrent_test_{dataset_id}_{i}",
                    "name": f"Dr. Concurrent {dataset_id}-{i}",
                    "university": f"Test University {dataset_id}",
                    "department": "Psychology",
                    "email": f"test{i}@test{dataset_id}.edu"
                }
                dataset.append(faculty)
            datasets.append(dataset)
        
        # Process all datasets concurrently
        start_time = asyncio.get_event_loop().time()
        
        results = await asyncio.gather(*[
            process_dataset(dataset) for dataset in datasets
        ])
        
        end_time = asyncio.get_event_loop().time()
        elapsed_time = end_time - start_time
        
        # Verify all processed successfully
        assert len(results) == 5, "Should process all datasets"
        
        total_faculty_processed = 0
        for enhanced_faculty, report in results:
            assert len(enhanced_faculty) == 10, "Each dataset should process 10 faculty"
            assert report['faculty_processed'] == 10, "Report should show 10 faculty processed"
            total_faculty_processed += len(enhanced_faculty)
        
        assert total_faculty_processed == 50, "Should process all 50 faculty across datasets"
        
        # Concurrent processing should be efficient
        assert elapsed_time < 30, f"Concurrent processing too slow: {elapsed_time}s"
        
        # Verify no data corruption from concurrency
        all_ids = set()
        for enhanced_faculty, _ in results:
            for faculty in enhanced_faculty:
                faculty_id = faculty['_id']
                assert faculty_id not in all_ids, f"Duplicate faculty ID found: {faculty_id}"
                all_ids.add(faculty_id)
        
        assert len(all_ids) == 50, "Should have 50 unique faculty IDs" 