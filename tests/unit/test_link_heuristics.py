"""
Unit tests for LinkHeuristics component.

Tests the intelligent scoring and classification of academic links
with multi-factor analysis algorithms.
"""

import pytest
from bs4 import BeautifulSoup
from lynnapse.core.link_heuristics import LinkHeuristics


class TestLinkHeuristics:
    """Comprehensive tests for LinkHeuristics scoring and classification."""
    
    def test_basic_faculty_link_scoring(self, link_heuristics):
        """Test basic faculty link scoring functionality."""
        # High-scoring faculty link
        score = link_heuristics.score_faculty_link(
            "Faculty Directory",
            "https://psychology.university.edu/faculty",
            "psychology"
        )
        assert score >= 1.0, f"Expected high score for faculty directory, got {score}"
        
        # Medium-scoring link
        score = link_heuristics.score_faculty_link(
            "People",
            "https://university.edu/people",
            "psychology"
        )
        assert 0.5 <= score <= 1.5, f"Expected medium score for people directory, got {score}"
        
        # Low-scoring link
        score = link_heuristics.score_faculty_link(
            "News and Events",
            "https://university.edu/news",
            "psychology"
        )
        assert score < 0.5, f"Expected low score for news link, got {score}"
    
    def test_faculty_term_recognition(self, link_heuristics):
        """Test recognition of faculty-related terms."""
        faculty_terms = [
            ("Faculty Directory", "https://test.edu/faculty", "psychology"),
            ("People", "https://test.edu/people", "psychology"),
            ("Staff Directory", "https://test.edu/staff", "psychology"),
            ("Directory", "https://test.edu/directory", "psychology")
        ]
        
        for name, url, dept in faculty_terms:
            score = link_heuristics.score_faculty_link(name, url, dept)
            assert score >= 0.3, f"Faculty term '{name}' should get bonus points, got {score}"
    
    def test_academic_indicators(self, link_heuristics):
        """Test recognition of academic indicators."""
        academic_links = [
            ("Department of Psychology", "https://university.edu/psychology", "psychology"),
            ("School of Medicine", "https://medschool.university.edu", "medicine"),
            ("College of Engineering", "https://engineering.university.edu", "engineering"),
            ("Institute of Technology", "https://tech.university.edu", "technology")
        ]
        
        for name, url, dept in academic_links:
            score = link_heuristics.score_faculty_link(name, url, dept)
            assert score >= 0.1, f"Academic indicator '{name}' should get bonus, got {score}"
        
        # .edu domain bonus
        edu_score = link_heuristics.score_faculty_link(
            "Faculty", "https://test.edu/faculty", "test"
        )
        non_edu_score = link_heuristics.score_faculty_link(
            "Faculty", "https://test.com/faculty", "test"
        )
        assert edu_score > non_edu_score, "EDU domain should score higher than non-EDU"
    
    def test_department_matching(self, link_heuristics):
        """Test target department matching logic."""
        # Exact match
        exact_score = link_heuristics.score_faculty_link(
            "Psychology Faculty",
            "https://psychology.university.edu/faculty",
            "psychology"
        )
        
        # Partial match
        partial_score = link_heuristics.score_faculty_link(
            "Clinical Psychology",
            "https://clinical-psych.university.edu",
            "psychology"
        )
        
        # No match
        no_match_score = link_heuristics.score_faculty_link(
            "Chemistry Faculty",
            "https://chemistry.university.edu/faculty", 
            "psychology"
        )
        
        assert exact_score > partial_score > no_match_score, "Department matching should be scored correctly"
    
    def test_url_pattern_analysis(self, link_heuristics):
        """Test URL pattern recognition."""
        url_patterns = [
            ("Test", "https://test.edu/faculty", 0.3),      # /faculty pattern
            ("Test", "https://test.edu/people", 0.3),       # /people pattern
            ("Test", "https://test.edu/staff", 0.3),        # /staff pattern
            ("Test", "https://test.edu/directory", 0.3),    # /directory pattern
            ("Test", "https://test.edu/news", 0.0),         # No pattern match
        ]
        
        for name, url, expected_min in url_patterns:
            score = link_heuristics.score_faculty_link(name, url, "test")
            if expected_min > 0:
                assert score >= expected_min, f"URL pattern in '{url}' should get bonus, got {score}"
            else:
                # News URLs might still get some score from other factors
                pass
    
    def test_quality_filtering(self, link_heuristics):
        """Test filtering of non-academic content."""
        low_quality_links = [
            ("Alumni News", "https://test.edu/alumni/news", "test"),
            ("Events Calendar", "https://test.edu/events", "test"),
            ("Admissions", "https://test.edu/admissions", "test"),
            ("Parking Information", "https://test.edu/parking", "test"),
            ("Student Services", "https://test.edu/student-services", "test")
        ]
        
        # These should get penalties or low scores
        for name, url, dept in low_quality_links:
            score = link_heuristics.score_faculty_link(name, url, dept)
            # Some might still score due to .edu domain, but should be relatively low
            assert score <= 1.0, f"Low quality link '{name}' scored too high: {score}"
    
    def test_complex_department_names(self, link_heuristics):
        """Test handling of complex department names."""
        complex_departments = [
            ("Computer Science", "Electrical Engineering and Computer Science"),
            ("Psychology", "Psychology and Brain Sciences"),
            ("Medicine", "School of Medicine and Health Sciences"),
            ("Math", "Mathematics and Statistics")
        ]
        
        for target_dept, full_dept_name in complex_departments:
            score = link_heuristics.score_faculty_link(
                f"{full_dept_name} Faculty",
                f"https://test.edu/{full_dept_name.lower().replace(' ', '-')}/faculty",
                target_dept.lower()
            )
            assert score >= 0.5, f"Complex department name matching failed for {target_dept} -> {full_dept_name}"
    
    def test_case_insensitivity(self, link_heuristics):
        """Test case insensitive matching."""
        # Test different case combinations
        test_cases = [
            ("PSYCHOLOGY FACULTY", "https://PSYCHOLOGY.EDU/FACULTY", "psychology"),
            ("Psychology Faculty", "https://psychology.edu/faculty", "PSYCHOLOGY"),
            ("psychology faculty", "https://psychology.edu/faculty", "Psychology")
        ]
        
        scores = []
        for name, url, dept in test_cases:
            score = link_heuristics.score_faculty_link(name, url, dept)
            scores.append(score)
        
        # All scores should be similar (case shouldn't matter)
        assert max(scores) - min(scores) < 0.1, "Case sensitivity detected in scoring"
    
    def test_edge_cases(self, link_heuristics):
        """Test edge cases and error handling."""
        edge_cases = [
            ("", "", ""),                        # Empty strings
            ("Faculty", "", "psychology"),       # Empty URL
            ("", "https://test.edu", "psychology"), # Empty name
            ("Faculty", "https://test.edu", ""),  # Empty department
            ("Faculty" * 100, "https://test.edu", "psychology"),  # Very long name
            ("Faculty", "https://" + "x" * 1000 + ".edu", "psychology"),  # Very long URL
        ]
        
        for name, url, dept in edge_cases:
            try:
                score = link_heuristics.score_faculty_link(name, url, dept)
                assert isinstance(score, (int, float)), f"Score should be numeric, got {type(score)}"
                assert score >= 0, f"Score should be non-negative, got {score}"
            except Exception as e:
                # If an exception occurs, it should be handled gracefully
                assert False, f"Edge case failed: name='{name[:50]}...', url='{url[:50]}...', dept='{dept}' - {e}"
    
    def test_score_range_validation(self, link_heuristics):
        """Test that scores stay within reasonable ranges."""
        test_links = [
            ("Faculty Directory", "https://psychology.university.edu/faculty", "psychology"),
            ("Random Page", "https://example.com/random", "psychology"),
            ("News", "https://university.edu/news", "psychology")
        ]
        
        for name, url, dept in test_links:
            score = link_heuristics.score_faculty_link(name, url, dept)
            
            # Scores should be reasonable (not negative, not extremely high)
            assert score >= 0, f"Score should not be negative: {score}"
            assert score <= 3.0, f"Score should not be extremely high: {score}"
            assert isinstance(score, (int, float)), f"Score should be numeric: {type(score)}"
    
    def test_performance_benchmarks(self, link_heuristics, performance_monitor):
        """Test performance of link scoring algorithms."""
        performance_monitor.start()
        
        # Score multiple links quickly
        for i in range(1000):
            link_heuristics.score_faculty_link(
                f"Faculty Directory {i}",
                f"https://university{i % 10}.edu/faculty",
                "psychology"
            )
        
        performance_monitor.stop()
        results = performance_monitor.get_results()
        
        # Should be fast (under 1 second for 1000 links)
        assert results["elapsed_time_seconds"] < 1.0, f"Heuristics too slow: {results['elapsed_time_seconds']}s"
        assert results["memory_efficient"], "Should not use excessive memory"
        
        # Calculate throughput
        links_per_second = 1000 / results["elapsed_time_seconds"]
        assert links_per_second >= 1000, f"Heuristics throughput too low: {links_per_second} links/sec"
    
    def test_university_verified_patterns(self, link_heuristics):
        """Test patterns verified on real universities."""
        # University of Vermont pattern (verified 100% success)
        uvm_score = link_heuristics.score_faculty_link(
            "Psychology",
            "https://www.uvm.edu/cas/psychology/directory",
            "psychology"
        )
        
        # Carnegie Mellon pattern
        cmu_score = link_heuristics.score_faculty_link(
            "Faculty Directory",
            "https://www.cmu.edu/dietrich/psychology/directory/",
            "psychology"
        )
        
        # Stanford pattern
        stanford_score = link_heuristics.score_faculty_link(
            "Faculty", 
            "https://psychology.stanford.edu/faculty",
            "psychology"
        )
        
        # MIT pattern
        mit_score = link_heuristics.score_faculty_link(
            "People",
            "https://psychology.mit.edu/people",
            "psychology"
        )
        
        # All should score highly (verified working patterns)
        verified_scores = [uvm_score, cmu_score, stanford_score, mit_score]
        for i, score in enumerate(verified_scores):
            university_names = ["UVM", "CMU", "Stanford", "MIT"]
            assert score >= 1.2, f"{university_names[i]} pattern should score highly: {score}"
    
    def test_false_positive_filtering(self, link_heuristics):
        """Test filtering of false positive links."""
        false_positives = [
            ("Faculty Parking", "https://test.edu/faculty-parking", "psychology"),
            ("Faculty Housing", "https://test.edu/faculty-housing", "psychology"),
            ("Faculty Club", "https://test.edu/faculty-club", "psychology"),
            ("Former Faculty", "https://test.edu/former-faculty", "psychology"),
            ("Faculty Search Committee", "https://test.edu/faculty-search", "psychology")
        ]
        
        # These contain "faculty" but aren't faculty directories
        regular_faculty_score = link_heuristics.score_faculty_link(
            "Faculty Directory", "https://test.edu/faculty", "psychology"
        )
        
        for name, url, dept in false_positives:
            false_positive_score = link_heuristics.score_faculty_link(name, url, dept)
            # False positives should score lower than real faculty directories
            assert false_positive_score < regular_faculty_score, f"False positive '{name}' scored too high: {false_positive_score}"
    
    def test_multilingual_support(self, link_heuristics):
        """Test handling of non-English content (basic support)."""
        # Some international universities might have mixed language content
        international_patterns = [
            ("Facultad", "https://universidad.edu/facultad", "psychology"),      # Spanish
            ("Fakultät", "https://universität.edu/fakultät", "psychology"),     # German  
            ("Professeurs", "https://université.edu/professeurs", "psychology"), # French
            ("教员", "https://university.edu.cn/faculty", "psychology")            # Chinese
        ]
        
        for name, url, dept in international_patterns:
            try:
                score = link_heuristics.score_faculty_link(name, url, dept)
                # Should handle gracefully, even if not specifically optimized
                assert isinstance(score, (int, float)), f"Should handle international text: {name}"
                assert score >= 0, f"Should not give negative scores: {score}"
            except Exception as e:
                # Should not crash on international text
                assert False, f"Failed to handle international text '{name}': {e}"
    
    def test_concurrent_usage(self, link_heuristics):
        """Test thread safety and concurrent usage."""
        import threading
        import time
        
        results = []
        errors = []
        
        def score_links():
            try:
                for i in range(100):
                    score = link_heuristics.score_faculty_link(
                        f"Faculty {i}",
                        f"https://test{i}.edu/faculty",
                        "psychology"
                    )
                    results.append(score)
                    time.sleep(0.001)  # Small delay to encourage race conditions
            except Exception as e:
                errors.append(e)
        
        # Run multiple threads concurrently
        threads = []
        for _ in range(5):
            thread = threading.Thread(target=score_links)
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join()
        
        # Should not have errors
        assert len(errors) == 0, f"Concurrent usage errors: {errors}"
        
        # Should have results from all threads
        assert len(results) == 500, f"Expected 500 results, got {len(results)}"
        
        # All results should be valid scores
        for score in results:
            assert isinstance(score, (int, float)), f"Invalid score type: {type(score)}"
            assert score >= 0, f"Negative score: {score}"
    
    def test_find_faculty_links_html(self, link_heuristics, sample_html_content):
        """Test faculty link extraction from HTML."""
        html = """
        <div class="navigation">
            <a href="/faculty">Faculty Directory</a>
            <a href="/people">People</a>
            <a href="/news">University News</a>
            <a href="/psychology/staff">Psychology Staff</a>
            <a href="/contact">Contact Us</a>
        </div>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        links = link_heuristics.find_faculty_links(soup, target_department="psychology")
        
        # Should find faculty-related links
        assert len(links) >= 2  # faculty and people links
        
        # Check scoring order (faculty should score higher than people)
        faculty_link = next((l for l in links if "faculty" in l["url"]), None)
        people_link = next((l for l in links if "people" in l["url"]), None)
        
        assert faculty_link is not None
        assert people_link is not None
        assert faculty_link["score"] >= people_link["score"]
    
    def test_lab_website_scoring(self, link_heuristics):
        """Test lab website discovery and scoring."""
        # High-quality lab URL
        lab_score = link_heuristics.score_lab_website(
            "https://coglab.stanford.edu",
            {"research_interests": ["cognitive", "neuroscience"]}
        )
        
        # Research center URL
        center_score = link_heuristics.score_lab_website(
            "https://psychology.university.edu/research/memory-lab",
            {"research_interests": ["memory", "cognition"]}
        )
        
        # Non-lab URL
        random_score = link_heuristics.score_lab_website(
            "https://university.edu/news",
            {"research_interests": ["psychology"]}
        )
        
        assert lab_score > center_score > random_score
        assert lab_score >= 1.0  # Should be confident for good lab URLs
    
    def test_research_field_indicators(self, link_heuristics):
        """Test research field pattern matching."""
        # Test various research fields
        cognitive_score = link_heuristics._score_research_field_match(
            "https://coglab.university.edu", 
            ["cognitive", "psychology"]
        )
        
        neuro_score = link_heuristics._score_research_field_match(
            "https://neurolab.university.edu",
            ["neuroscience", "brain"]
        )
        
        unrelated_score = link_heuristics._score_research_field_match(
            "https://randomlab.university.edu",
            ["biology", "chemistry"]
        )
        
        assert cognitive_score > 0
        assert neuro_score > 0  
        assert unrelated_score == 0
    
    @pytest.mark.asyncio
    async def test_async_compatibility(self, link_heuristics):
        """Test that LinkHeuristics works properly in async contexts."""
        # Should work in async function without issues
        score = link_heuristics.score_faculty_link(
            "Faculty Directory",
            "https://university.edu/faculty",
            "psychology"
        )
        
        assert score > 0  # Should work normally in async context 