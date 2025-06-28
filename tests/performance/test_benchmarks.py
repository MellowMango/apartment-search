"""
Performance benchmarks for Lynnapse components.

Tests processing speed, memory usage, and scalability for production readiness.
"""

import pytest
import asyncio
import time
import json
from typing import List, Dict
from lynnapse.core.enhanced_link_processor import identify_and_replace_social_media_links
from lynnapse.core.website_validator import validate_faculty_websites
from lynnapse.core.smart_link_replacer import SmartLinkReplacer
from lynnapse.core.link_heuristics import LinkHeuristics
from lynnapse.core.adaptive_faculty_crawler import AdaptiveFacultyCrawler


class TestPerformanceBenchmarks:
    """Performance benchmarks for production deployment."""
    
    @pytest.mark.asyncio
    async def test_link_processing_speed_benchmark(self, performance_monitor, mock_aiohttp):
        """Benchmark link processing speed with various dataset sizes."""
        benchmark_results = {}
        
        # Test different dataset sizes
        dataset_sizes = [10, 25, 50, 100, 200]
        
        for size in dataset_sizes:
            # Generate test dataset
            faculty_data = []
            for i in range(size):
                faculty = {
                    "name": f"Dr. Faculty {i}",
                    "university": "Test University",
                    "profile_url": f"https://test.edu/faculty{i}",
                    "personal_website": f"https://scholar.google.com/citations?user=faculty{i}",
                    "research_interests": ["psychology", "research"]
                }
                faculty_data.append(faculty)
            
            # Mock responses
            for i in range(size + 50):  # Extra mocks for safety
                mock_aiohttp.get(f"https://test.edu/faculty{i}", status=200)
                mock_aiohttp.get(f"https://scholar.google.com/citations?user=faculty{i}", status=200)
            
            performance_monitor.start()
            
            # Process the dataset
            enhanced_faculty, report = await identify_and_replace_social_media_links(
                faculty_data,
                use_ai_assistance=False,
                max_concurrent=10
            )
            
            performance_monitor.stop()
            results = performance_monitor.get_results()
            
            # Record benchmark results
            benchmark_results[size] = {
                "elapsed_time": results["elapsed_time_seconds"],
                "peak_memory_mb": results["peak_memory_mb"],
                "faculty_per_second": size / results["elapsed_time_seconds"] if results["elapsed_time_seconds"] > 0 else 0,
                "memory_per_faculty": results["peak_memory_mb"] / size,
                "processing_success": len(enhanced_faculty) == size
            }
            
            # Clear for next iteration
            performance_monitor.peak_memory = 0
        
        # Verify performance requirements
        for size, metrics in benchmark_results.items():
            # Processing speed requirements
            assert metrics["faculty_per_second"] >= 5, f"Too slow for {size} faculty: {metrics['faculty_per_second']} faculty/sec"
            
            # Memory efficiency requirements
            assert metrics["peak_memory_mb"] < 500, f"Too much memory for {size} faculty: {metrics['peak_memory_mb']} MB"
            
            # Memory should scale reasonably
            assert metrics["memory_per_faculty"] < 10, f"Memory per faculty too high: {metrics['memory_per_faculty']} MB/faculty"
            
            # Should complete processing
            assert metrics["processing_success"], f"Failed to process all faculty for size {size}"
        
        # Save benchmark results
        with open("benchmark_results.json", "w") as f:
            json.dump(benchmark_results, f, indent=2)
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_scalability(self, performance_monitor, mock_aiohttp):
        """Test scalability with different concurrency levels."""
        faculty_data = []
        for i in range(100):  # Fixed dataset size
            faculty = {
                "name": f"Dr. Faculty {i}",
                "university": "Test University",
                "profile_url": f"https://test.edu/faculty{i}"
            }
            faculty_data.append(faculty)
        
        # Mock responses
        for i in range(150):
            mock_aiohttp.get(f"https://test.edu/faculty{i}", status=200)
        
        concurrency_results = {}
        concurrency_levels = [1, 2, 5, 10, 20]
        
        for concurrency in concurrency_levels:
            performance_monitor.start()
            
            enhanced_faculty, report = await identify_and_replace_social_media_links(
                faculty_data,
                use_ai_assistance=False,
                max_concurrent=concurrency
            )
            
            performance_monitor.stop()
            results = performance_monitor.get_results()
            
            concurrency_results[concurrency] = {
                "elapsed_time": results["elapsed_time_seconds"],
                "peak_memory_mb": results["peak_memory_mb"],
                "faculty_processed": len(enhanced_faculty)
            }
            
            # Reset for next test
            performance_monitor.peak_memory = 0
        
        # Verify concurrency improves performance (up to a point)
        assert concurrency_results[5]["elapsed_time"] <= concurrency_results[1]["elapsed_time"]
        assert concurrency_results[10]["elapsed_time"] <= concurrency_results[2]["elapsed_time"]
        
        # All should process same number of faculty
        for concurrency, metrics in concurrency_results.items():
            assert metrics["faculty_processed"] == 100, f"Concurrency {concurrency} processed {metrics['faculty_processed']} faculty"
    
    def test_link_heuristics_performance(self, performance_monitor):
        """Benchmark LinkHeuristics scoring performance."""
        heuristics = LinkHeuristics()
        
        # Generate test data
        test_links = []
        for i in range(1000):
            test_links.append({
                "dept_name": f"Faculty Directory {i}",
                "dept_url": f"https://university{i % 10}.edu/faculty",
                "target_department": "psychology"
            })
        
        performance_monitor.start()
        
        # Score all links
        scores = []
        for link in test_links:
            score = heuristics.score_faculty_link(
                link["dept_name"],
                link["dept_url"], 
                link["target_department"]
            )
            scores.append(score)
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Performance requirements for heuristics
        assert results["elapsed_time_seconds"] < 1.0, f"Heuristics too slow: {results['elapsed_time_seconds']}s"
        assert results["peak_memory_mb"] < 50, f"Heuristics uses too much memory: {results['peak_memory_mb']} MB"
        assert len(scores) == 1000, "Should score all links"
        
        # Calculate throughput
        links_per_second = 1000 / results["elapsed_time_seconds"]
        assert links_per_second >= 1000, f"Heuristics throughput too low: {links_per_second} links/sec"
    
    @pytest.mark.asyncio
    async def test_website_validation_performance(self, performance_monitor, mock_aiohttp):
        """Benchmark website validation performance."""
        # Generate test faculty data
        faculty_data = []
        for i in range(200):
            faculty = {
                "name": f"Dr. Faculty {i}",
                "profile_url": f"https://test{i % 10}.edu/faculty{i}",
                "personal_website": f"https://scholar.google.com/citations?user=faculty{i}",
                "lab_website": f"https://lab{i % 5}.edu/research"
            }
            faculty_data.append(faculty)
        
        # Mock all potential responses
        for i in range(250):
            mock_aiohttp.get(f"https://test{i % 10}.edu/faculty{i}", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/citations?user=faculty{i}", status=200)
            mock_aiohttp.get(f"https://lab{i % 5}.edu/research", status=200)
        
        performance_monitor.start()
        
        validated_faculty, report = await validate_faculty_websites(
            faculty_data,
            max_concurrent=15
        )
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Performance requirements for validation
        assert results["elapsed_time_seconds"] < 20, f"Validation too slow: {results['elapsed_time_seconds']}s"
        assert results["peak_memory_mb"] < 300, f"Validation uses too much memory: {results['peak_memory_mb']} MB"
        assert len(validated_faculty) == 200, "Should validate all faculty"
        
        # Calculate validation throughput
        validations_per_second = (200 * 3) / results["elapsed_time_seconds"]  # 3 links per faculty
        assert validations_per_second >= 20, f"Validation throughput too low: {validations_per_second} validations/sec"
    
    @pytest.mark.asyncio
    async def test_adaptive_crawler_performance(self, performance_monitor, mock_aiohttp):
        """Benchmark adaptive faculty crawler performance."""
        # Mock faculty directory page
        faculty_html = """
        <div class="faculty-listing">
        """ + "\n".join([
            f'<div class="faculty-card"><h3><a href="/faculty/prof{i}">Professor {i}</a></h3></div>'
            for i in range(50)
        ]) + """
        </div>
        """
        
        mock_aiohttp.get("https://test.edu/faculty", body=faculty_html)
        
        # Mock individual faculty profile pages
        for i in range(50):
            profile_html = f"""
            <div class="profile">
                <h1>Professor {i}</h1>
                <p>Email: prof{i}@test.edu</p>
                <p>Department: Psychology</p>
                <p>Research: Psychology Research {i}</p>
            </div>
            """
            mock_aiohttp.get(f"https://test.edu/faculty/prof{i}", body=profile_html)
        
        performance_monitor.start()
        
        crawler = AdaptiveFacultyCrawler()
        university_pattern = {
            'base_url': 'https://test.edu',
            'faculty_url': 'https://test.edu/faculty'
        }
        
        faculty_data = await crawler.scrape_faculty_comprehensive(
            university_pattern,
            department_name="Psychology",
            max_faculty=50
        )
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Performance requirements for adaptive crawler
        assert results["elapsed_time_seconds"] < 30, f"Crawler too slow: {results['elapsed_time_seconds']}s"
        assert results["peak_memory_mb"] < 200, f"Crawler uses too much memory: {results['peak_memory_mb']} MB"
        assert len(faculty_data) >= 40, f"Should extract most faculty: {len(faculty_data)}/50"
        
        # Calculate crawling throughput
        faculty_per_second = len(faculty_data) / results["elapsed_time_seconds"]
        assert faculty_per_second >= 1.5, f"Crawling throughput too low: {faculty_per_second} faculty/sec"
    
    @pytest.mark.asyncio
    async def test_memory_usage_scaling(self, performance_monitor, mock_aiohttp):
        """Test memory usage scaling with dataset size."""
        memory_usage = {}
        dataset_sizes = [10, 50, 100, 200]
        
        for size in dataset_sizes:
            # Generate dataset
            faculty_data = []
            for i in range(size):
                faculty = {
                    "name": f"Dr. Faculty {i}",
                    "university": "Test University",
                    "profile_url": f"https://test.edu/faculty{i}",
                    "research_interests": ["psychology"] * 5  # Fixed size per faculty
                }
                faculty_data.append(faculty)
            
            # Mock responses
            for i in range(size + 20):
                mock_aiohttp.get(f"https://test.edu/faculty{i}", status=200)
            
            performance_monitor.start()
            
            enhanced_faculty, _ = await identify_and_replace_social_media_links(
                faculty_data,
                use_ai_assistance=False,
                max_concurrent=5
            )
            
            performance_monitor.stop()
            results = performance_monitor.get_results()
            
            memory_usage[size] = {
                "peak_memory_mb": results["peak_memory_mb"],
                "memory_per_faculty": results["peak_memory_mb"] / size
            }
            
            # Reset for next test
            performance_monitor.peak_memory = 0
        
        # Verify memory scaling is reasonable
        for size in dataset_sizes:
            metrics = memory_usage[size]
            
            # Memory per faculty should be reasonable and relatively consistent
            assert metrics["memory_per_faculty"] < 5, f"Too much memory per faculty: {metrics['memory_per_faculty']} MB"
            
            # Total memory should scale sub-linearly (due to fixed overheads)
            if size >= 50:
                assert metrics["peak_memory_mb"] < size * 3, f"Memory scaling too high for {size} faculty"
    
    def test_cpu_usage_benchmark(self, performance_monitor):
        """Benchmark CPU-intensive operations."""
        heuristics = LinkHeuristics()
        replacer = SmartLinkReplacer(enable_ai_assistance=False)
        
        # Generate CPU-intensive test data
        test_data = []
        for i in range(1000):
            faculty_info = {
                "name": f"Dr. Very Long Faculty Name {i}",
                "university": f"University of {i} with Long Name",
                "department": "Department of Psychology and Cognitive Sciences",
                "research_interests": [f"research area {j}" for j in range(20)]
            }
            test_data.append(faculty_info)
        
        performance_monitor.start()
        
        # Perform CPU-intensive operations
        for faculty_info in test_data:
            # Score multiple links
            for j in range(5):
                heuristics.score_faculty_link(
                    f"Faculty Directory {j}",
                    f"https://university{j}.edu/faculty",
                    "psychology"
                )
            
            # Generate academic candidates
            candidates = replacer._generate_academic_candidates(faculty_info)
            
            # Score candidates
            for candidate in candidates[:10]:  # Limit to first 10
                replacer._score_academic_link(candidate)
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # CPU performance requirements
        assert results["elapsed_time_seconds"] < 5, f"CPU operations too slow: {results['elapsed_time_seconds']}s"
        assert results["peak_memory_mb"] < 100, f"CPU operations use too much memory: {results['peak_memory_mb']} MB"
        
        # Calculate operations per second
        total_operations = 1000 * 5 + 1000 * 10  # Scoring + candidate generation
        ops_per_second = total_operations / results["elapsed_time_seconds"]
        assert ops_per_second >= 1000, f"CPU throughput too low: {ops_per_second} ops/sec"
    
    @pytest.mark.asyncio
    async def test_end_to_end_performance_target(self, performance_monitor, mock_aiohttp):
        """Test end-to-end performance meets production targets."""
        # Production-scale test: 100 faculty with complete processing
        faculty_data = []
        for i in range(100):
            faculty = {
                "name": f"Dr. Faculty {i}",
                "university": "Production University",
                "department": "Psychology",
                "profile_url": f"https://prod.edu/faculty{i}",
                "personal_website": f"https://scholar.google.com/citations?user=faculty{i}",
                "lab_website": f"https://lab.prod.edu/research{i % 10}",
                "research_interests": [f"area {j}" for j in range(5)]
            }
            faculty_data.append(faculty)
        
        # Mock all responses
        for i in range(120):
            mock_aiohttp.get(f"https://prod.edu/faculty{i}", status=200)
            mock_aiohttp.get(f"https://scholar.google.com/citations?user=faculty{i}", status=200)
            mock_aiohttp.get(f"https://lab.prod.edu/research{i % 10}", status=200)
        
        performance_monitor.start()
        
        # Complete pipeline: validation + processing + enrichment
        validated_faculty, validation_report = await validate_faculty_websites(
            faculty_data,
            max_concurrent=10
        )
        
        enhanced_faculty, processing_report = await identify_and_replace_social_media_links(
            validated_faculty,
            use_ai_assistance=False,
            max_concurrent=10
        )
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Production performance targets
        assert results["elapsed_time_seconds"] < 60, f"End-to-end too slow: {results['elapsed_time_seconds']}s"
        assert results["peak_memory_mb"] < 400, f"End-to-end uses too much memory: {results['peak_memory_mb']} MB"
        assert len(enhanced_faculty) == 100, "Should process all faculty"
        
        # Calculate end-to-end throughput
        faculty_per_minute = 100 / (results["elapsed_time_seconds"] / 60)
        assert faculty_per_minute >= 120, f"End-to-end throughput too low: {faculty_per_minute} faculty/min"
        
        # Quality requirements
        assert validation_report["total_links_validated"] >= 200  # ~2-3 links per faculty
        assert processing_report["faculty_processed"] == 100
        
        # Save production benchmark
        production_benchmark = {
            "timestamp": time.time(),
            "faculty_processed": 100,
            "elapsed_time_seconds": results["elapsed_time_seconds"],
            "peak_memory_mb": results["peak_memory_mb"],
            "faculty_per_minute": faculty_per_minute,
            "meets_production_targets": True
        }
        
        with open("production_benchmark.json", "w") as f:
            json.dump(production_benchmark, f, indent=2) 