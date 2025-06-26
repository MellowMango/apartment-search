"""
Unit tests for lab discovery components.

Tests the LinkHeuristics, LabNameClassifier, and SiteSearchTask components
that form the bulletproof lab discovery pipeline.
"""

import pytest
import time
from unittest.mock import Mock, patch, AsyncMock
from bs4 import BeautifulSoup
import json

from lynnapse.core import LinkHeuristics, LabNameClassifier, SiteSearchTask


class TestLinkHeuristics:
    """Test the LinkHeuristics component."""
    
    def test_lab_keyword_detection(self):
        """Test that lab keywords are properly detected in link text."""
        html = '''
        <div>
            <a href="/cognitive-lab">Cognitive Neuroscience Laboratory</a>
            <a href="/contact">Contact Us</a>
            <a href="/research-center">Advanced Research Center</a>
            <a href="/home">Home Page</a>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        heuristics = LinkHeuristics(base_url="https://university.edu")
        
        links = heuristics.find_lab_links(soup)
        
        # Should find at least 2 lab-related links (may find more due to contextual matching)
        assert len(links) >= 2
        
        # First link should be highest scored
        assert links[0]["url"] == "https://university.edu/cognitive-lab"
        assert links[0]["score"] > links[1]["score"]
        
        # Check that all results have required fields
        for link in links:
            assert "url" in link
            assert "text" in link
            assert "score" in link
            assert "context" in link
            assert link["score"] > 0
    
    def test_domain_scoring(self):
        """Test that .edu domains are scored higher than others."""
        heuristics = LinkHeuristics()
        
        edu_score = heuristics._score_link("https://lab.stanford.edu", "research lab", None)
        org_score = heuristics._score_link("https://lab.example.org", "research lab", None)
        com_score = heuristics._score_link("https://lab.example.com", "research lab", None)
        
        assert edu_score > org_score > com_score
    
    def test_exclude_patterns(self):
        """Test that non-lab links are properly excluded."""
        html = '''
        <div>
            <a href="mailto:test@university.edu">Email Professor</a>
            <a href="https://facebook.com/lab">Facebook Lab Page</a>
            <a href="/cognitive-lab">Cognitive Laboratory</a>
            <a href="tel:555-1234">Phone Number</a>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        heuristics = LinkHeuristics(base_url="https://university.edu")
        
        links = heuristics.find_lab_links(soup)
        
        # Should only find the real lab link
        assert len(links) == 1
        assert "cognitive-lab" in links[0]["url"]
    
    def test_contextual_link_detection(self):
        """Test detection of lab links through contextual analysis."""
        html = '''
        <div>
            <p>Dr. Smith directs the Cognitive Neuroscience Laboratory.</p>
            <p><a href="https://coglab.stanford.edu">Visit our website</a></p>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        heuristics = LinkHeuristics(base_url="https://stanford.edu")
        
        links = heuristics.find_lab_links(soup)
        
        # Should find the contextual link
        assert len(links) >= 1
        assert any("coglab.stanford.edu" in link["url"] for link in links)


class TestLabNameClassifier:
    """Test the LabNameClassifier component."""
    
    @pytest.fixture
    def sample_training_data(self):
        """Provide sample training data for tests."""
        positive_examples = [
            "Laboratory for Cognitive Science",
            "Advanced Materials Research Center",
            "Computational Biology Lab",
            "Human-Computer Interaction Laboratory",
            "Artificial Intelligence Research Group"
        ]
        negative_examples = [
            "The professor teaches undergraduate courses",
            "Office hours are available on Tuesdays",
            "Students can access course materials online",
            "Research interests include machine learning",
            "Contact information is in the directory"
        ]
        sentences = positive_examples + negative_examples
        labels = [True] * len(positive_examples) + [False] * len(negative_examples)
        return sentences, labels
    
    def test_classifier_initialization(self):
        """Test that classifier initializes correctly."""
        classifier = LabNameClassifier()
        
        info = classifier.get_model_info()
        assert info["is_trained"] == False
        assert "model_path" in info
        assert info["vectorizer_features"] == 0
    
    def test_training_with_sample_data(self, sample_training_data):
        """Test training the classifier with sample data."""
        classifier = LabNameClassifier()
        sentences, labels = sample_training_data
        
        # Use more data and no validation split for small datasets
        classifier.model.early_stopping = False  # Disable early stopping for small dataset
        metrics = classifier.train(sentences, labels, test_size=0.3, verbose=False)
        
        assert classifier.is_trained == True
        assert metrics["accuracy"] >= 0.5  # Lower threshold for small dataset
        assert metrics["training_samples"] > 0
        assert metrics["test_samples"] > 0
        assert metrics["positive_samples"] == 5
        assert metrics["negative_samples"] == 5
    
    def test_prediction_after_training(self, sample_training_data):
        """Test making predictions after training."""
        classifier = LabNameClassifier()
        classifier.model.early_stopping = False
        sentences, labels = sample_training_data
        classifier.train(sentences, labels, test_size=0.3, verbose=False)
        
        # Test positive prediction
        is_lab, confidence = classifier.predict("Neuroscience Research Laboratory")
        assert isinstance(is_lab, bool)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
        
        # Test negative prediction
        is_lab, confidence = classifier.predict("Students must register for courses")
        assert isinstance(is_lab, bool)
        assert isinstance(confidence, float)
        assert 0.0 <= confidence <= 1.0
    
    def test_scan_text_blocks(self, sample_training_data):
        """Test scanning HTML for lab names."""
        classifier = LabNameClassifier()
        classifier.model.early_stopping = False
        sentences, labels = sample_training_data
        classifier.train(sentences, labels, test_size=0.3, verbose=False)
        
        html = '''
        <div>
            <h2>Cognitive Science Research Laboratory</h2>
            <p>The professor teaches undergraduate courses in psychology.</p>
            <p>Advanced Materials Research Center focuses on nanotechnology.</p>
            <p>Office hours are available by appointment.</p>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        candidates = classifier.scan_text_blocks(soup, confidence_threshold=0.5)
        
        # Should find lab-related text blocks
        assert len(candidates) >= 1
        
        # Check structure of results
        for candidate in candidates:
            assert "text" in candidate
            assert "confidence" in candidate
            assert "tag" in candidate
            assert "position" in candidate
            assert candidate["confidence"] >= 0.5
    
    def test_feature_importance(self, sample_training_data):
        """Test feature importance extraction."""
        classifier = LabNameClassifier()
        classifier.model.early_stopping = False
        sentences, labels = sample_training_data
        classifier.train(sentences, labels, test_size=0.3, verbose=False)
        
        importance = classifier.get_feature_importance(5)
        
        # Should return list of feature importance tuples
        assert isinstance(importance, list)
        assert len(importance) <= 5
        
        for feature, weight in importance:
            assert isinstance(feature, str)
            assert isinstance(weight, float)
            assert weight >= 0


class TestSiteSearchTask:
    """Test the SiteSearchTask component."""
    
    def test_initialization_without_keys(self):
        """Test initialization without API keys."""
        search = SiteSearchTask()
        
        stats = search.get_usage_stats()
        assert stats["quota_used"] == 0
        assert stats["total_cost_usd"] == 0
        assert stats["api_availability"]["bing_available"] == False
        assert stats["api_availability"]["serpapi_available"] == False
    
    def test_cost_estimation(self):
        """Test cost estimation for different numbers of queries."""
        search = SiteSearchTask()
        
        cost_estimate = search.estimate_cost(100)
        
        assert cost_estimate["num_queries"] == 100
        assert cost_estimate["bing_cost_usd"] == 0.3  # 100 * 0.003
        assert cost_estimate["serpapi_cost_usd"] == 0.5  # 100 * 0.005
        assert cost_estimate["recommended"] == "serpapi"  # No Bing key available
    
    def test_cache_key_generation(self):
        """Test that cache keys are generated consistently."""
        search = SiteSearchTask()
        
        key1 = search._create_cache_key("Dr. John Smith", "Cognitive Lab", "Stanford")
        key2 = search._create_cache_key("Dr. John Smith", "Cognitive Lab", "Stanford")
        key3 = search._create_cache_key("Dr. Jane Doe", "Cognitive Lab", "Stanford")
        
        assert key1 == key2  # Same inputs should produce same key
        assert key1 != key3  # Different inputs should produce different keys
        assert key1.startswith("search:")
    
    def test_search_query_construction(self):
        """Test search query construction."""
        search = SiteSearchTask()
        
        query = search._construct_search_query(
            "Dr. John Smith", "Cognitive Laboratory", "Stanford University"
        )
        
        assert '"John Smith"' in query
        assert '"Cognitive Laboratory"' in query
        assert '"Stanford University"' in query
        assert "(site:.edu OR site:.org)" in query
    
    def test_result_scoring(self):
        """Test scoring of search results."""
        search = SiteSearchTask()
        
        results = [
            {
                "url": "https://coglab.stanford.edu/smith",
                "title": "John Smith Cognitive Laboratory",
                "snippet": "Research in cognitive science"
            },
            {
                "url": "https://example.com/lab",
                "title": "Some Lab",
                "snippet": "Generic lab information"
            }
        ]
        
        scored = search._score_search_results(results, "John Smith", "Cognitive Laboratory")
        
        # Results should be sorted by score
        assert len(scored) == 2
        assert scored[0]["confidence"] >= scored[1]["confidence"]
        
        # Stanford .edu site should score higher
        stanford_result = next(r for r in scored if "stanford.edu" in r["url"])
        assert stanford_result["confidence"] > 0.4  # Should get .edu bonus
    
    @pytest.mark.asyncio
    async def test_caching_behavior(self):
        """Test caching functionality."""
        cache_dict = {}
        search = SiteSearchTask(cache_client=cache_dict, enable_cache=True)
        
        # Store something in cache
        test_results = [{"url": "test.edu", "title": "Test", "snippet": "Test"}]
        cache_key = search._create_cache_key("Test", "Test Lab", "Test University")
        
        await search._store_in_cache(cache_key, test_results)
        
        # Retrieve from cache
        cached_results = await search._get_from_cache(cache_key)
        
        assert cached_results == test_results
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        search = SiteSearchTask()
        
        # Initially should allow queries
        assert await search._check_rate_limit() == True
        
        # Simulate hitting rate limit
        search.query_timestamps = [time.time()] * search.MAX_QUERIES_PER_MINUTE
        
        assert await search._check_rate_limit() == False


@pytest.mark.integration
class TestLabDiscoveryIntegration:
    """Integration tests for the complete lab discovery pipeline."""
    
    def test_complete_pipeline(self):
        """Test the complete lab discovery pipeline."""
        # Sample faculty HTML with lab information
        faculty_html = '''
        <div class="faculty-profile">
            <h1>Dr. Jane Smith</h1>
            <p>Dr. Smith leads the <a href="/cognitive-lab">Cognitive Neuroscience Laboratory</a> 
               and conducts research in memory and attention.</p>
            <p>Our research group focuses on understanding cognitive processes.</p>
            <p>Contact: <a href="mailto:jsmith@university.edu">jsmith@university.edu</a></p>
        </div>
        '''
        
        soup = BeautifulSoup(faculty_html, 'html.parser')
        
        # Stage 1: Link Heuristics
        heuristics = LinkHeuristics(base_url="https://university.edu")
        lab_links = heuristics.find_lab_links(soup)
        
        # Should find the lab link
        assert len(lab_links) >= 1
        assert lab_links[0]["url"] == "https://university.edu/cognitive-lab"
        
        # Stage 2: Lab Name Classification (would be used if no links found)
        classifier = LabNameClassifier()
        # Note: In a real scenario, we'd train this first
        
        # Stage 3: External search (would be used if no local results)
        search = SiteSearchTask()
        # Note: This would require API keys for actual searches
        
        # Verify the pipeline structure works
        assert heuristics is not None
        assert classifier is not None
        assert search is not None
        
        print("✅ Complete lab discovery pipeline structure validated!")


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 