"""
LinkHeuristics - Fast, zero-cost lab link extraction from faculty pages.

This module implements regex-based heuristics to identify laboratory and research
center links from faculty profile HTML. It uses keyword matching and domain scoring
to prioritize the most relevant lab URLs without any external API calls.
"""

import re
import logging
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class LinkHeuristics:
    """Fast heuristic-based lab link extraction from HTML content."""
    
    # Core lab keywords pattern - covers most academic lab naming conventions
    LAB_KEYWORDS = r"(lab|laboratory|center|centre|group|clinic|institute|facility|unit)"
    
    # Extended patterns for better matching
    RESEARCH_PATTERNS = [
        r"research\s+(lab|laboratory|center|centre|group)",
        r"(lab|laboratory)\s+for\s+\w+",
        r"\w+\s+(lab|laboratory|center|centre)",
        r"(institute|center|centre)\s+for\s+\w+",
        r"computational\s+\w+\s+(lab|center|centre)",
        r"cognitive\s+\w*\s*(lab|laboratory|center|centre)",
    ]
    
    # Negative patterns to exclude non-lab links
    EXCLUDE_PATTERNS = [
        r"mailto:",
        r"tel:",
        r"javascript:",
        r"#",
        r"facebook\.com",
        r"twitter\.com",
        r"linkedin\.com",
        r"instagram\.com",
        r"youtube\.com",
        r"contact",
        r"email",
        r"phone",
        r"address",
        r"cv\.pdf",
        r"resume\.pdf",
    ]
    
    def __init__(self, base_url: Optional[str] = None):
        """
        Initialize LinkHeuristics engine.
        
        Args:
            base_url: Base URL for resolving relative links
        """
        self.base_url = base_url
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) 
                                for pattern in self.RESEARCH_PATTERNS]
        self.exclude_pattern = re.compile("|".join(self.EXCLUDE_PATTERNS), re.IGNORECASE)
        
    def find_lab_links(self, soup: BeautifulSoup) -> List[Dict]:
        """
        Extract lab links with confidence scores from HTML soup.
        
        Args:
            soup: BeautifulSoup object of faculty profile page
            
        Returns:
            List of dicts with keys: url, text, score, context
            Sorted by score in descending order
        """
        links = []
        processed_urls = set()  # Avoid duplicates
        
        # Find all anchor tags with href attributes
        for anchor in soup.find_all("a", href=True):
            url = anchor.get("href", "").strip()
            text = anchor.get_text(" ", strip=True)
            
            if not url or not text:
                continue
                
            # Skip if already processed or matches exclude patterns
            if url in processed_urls or self.exclude_pattern.search(url.lower()):
                continue
                
            # Resolve relative URLs
            full_url = self._resolve_url(url)
            if not full_url:
                continue
                
            # Check if link text contains lab keywords
            if self._contains_lab_keywords(text):
                score = self._score_link(full_url, text, anchor)
                if score > 0:  # Only include links with positive scores
                    links.append({
                        "url": full_url,
                        "text": text,
                        "score": score,
                        "context": self._get_context(anchor)
                    })
                    processed_urls.add(url)
        
        # Also check parent containers for missed links
        links.extend(self._find_contextual_links(soup, processed_urls))
        
        # Sort by score (highest first) and return
        return sorted(links, key=lambda x: x["score"], reverse=True)
    
    def _contains_lab_keywords(self, text: str) -> bool:
        """Check if text contains lab-related keywords."""
        text_lower = text.lower()
        
        # Basic keyword check
        if re.search(self.LAB_KEYWORDS, text_lower):
            return True
            
        # Check against extended patterns
        for pattern in self.compiled_patterns:
            if pattern.search(text_lower):
                return True
                
        return False
    
    def _score_link(self, url: str, text: str, anchor) -> float:
        """
        Score a link based on multiple factors.
        
        Scoring factors:
        - Domain relevance (.edu = 0.4, .org = 0.2, others = 0.0)
        - Keyword density in link text (0.3 per keyword)
        - URL path patterns (0.2 for lab-like paths)
        - Context relevance (0.1 bonus)
        
        Returns:
            Float score between 0.0 and 1.0+
        """
        score = 0.0
        text_lower = text.lower()
        url_lower = url.lower()
        
        # Domain scoring - prefer academic domains
        if ".edu" in url_lower:
            score += 0.4
        elif ".org" in url_lower:
            score += 0.2
        elif ".gov" in url_lower:
            score += 0.15
            
        # Keyword density in link text
        keyword_matches = len(re.findall(self.LAB_KEYWORDS, text_lower))
        score += keyword_matches * 0.3
        
        # URL path patterns that suggest lab websites
        lab_url_patterns = [
            r"/lab",
            r"/laboratory",
            r"/research",
            r"/center",
            r"/institute",
            r"/~\w+",  # Personal pages
        ]
        
        for pattern in lab_url_patterns:
            if re.search(pattern, url_lower):
                score += 0.2
                break
                
        # Length penalty for very long link text (likely not a lab name)
        if len(text) > 100:
            score -= 0.1
            
        # Bonus for specific high-confidence patterns
        high_confidence_patterns = [
            r"visit\s+(our\s+)?(lab|laboratory)",
            r"(lab|laboratory)\s+website",
            r"(lab|laboratory)\s+homepage",
        ]
        
        for pattern in high_confidence_patterns:
            if re.search(pattern, text_lower):
                score += 0.2
                break
                
        return max(0.0, score)  # Ensure non-negative score
    
    def _find_contextual_links(self, soup: BeautifulSoup, processed_urls: set) -> List[Dict]:
        """
        Find lab links by examining context around lab-related text.
        
        Sometimes lab names appear in text but the link is nearby rather than
        wrapping the lab name directly.
        """
        contextual_links = []
        
        # Find text that looks like lab names
        for text_element in soup.find_all(text=True):
            text = text_element.strip()
            if len(text) < 10 or not self._contains_lab_keywords(text):
                continue
                
            # Look for nearby links in parent containers
            parent = text_element.parent
            if not parent:
                continue
                
            # Check up to 2 levels up for related links
            for level in range(3):
                if not parent:
                    break
                    
                # Find links in this container
                for anchor in parent.find_all("a", href=True):
                    url = anchor.get("href", "").strip()
                    link_text = anchor.get_text(" ", strip=True)
                    
                    if (url and url not in processed_urls and 
                        not self.exclude_pattern.search(url.lower())):
                        
                        full_url = self._resolve_url(url)
                        if full_url:
                            # Score based on context proximity
                            score = self._score_contextual_link(full_url, link_text, text)
                            if score > 0.3:  # Higher threshold for contextual links
                                contextual_links.append({
                                    "url": full_url,
                                    "text": f"{link_text} (contextual: {text[:50]}...)",
                                    "score": score,
                                    "context": text[:100]
                                })
                                processed_urls.add(url)
                
                parent = parent.parent
                
        return contextual_links
    
    def _score_contextual_link(self, url: str, link_text: str, context_text: str) -> float:
        """Score links found through contextual analysis."""
        base_score = self._score_link(url, link_text, None)
        
        # Boost score if context contains strong lab indicators
        context_lower = context_text.lower()
        if re.search(r"(directs?|leads?|heads?).+(lab|laboratory|center)", context_lower):
            base_score += 0.3
        elif re.search(r"(lab|laboratory|center).+(website|site|page)", context_lower):
            base_score += 0.2
            
        return base_score
    
    def _resolve_url(self, url: str) -> Optional[str]:
        """Resolve relative URLs to absolute URLs."""
        if not url:
            return None
            
        # Already absolute
        if url.startswith(("http://", "https://")):
            return url
            
        # Skip non-HTTP schemes
        if ":" in url and not url.startswith("/"):
            return None
            
        # Resolve relative URL
        if self.base_url:
            try:
                return urljoin(self.base_url, url)
            except Exception as e:
                logger.warning(f"Failed to resolve URL {url}: {e}")
                return None
        else:
            # Return as-is if no base URL provided
            return url if url.startswith("/") else None
    
    def _get_context(self, anchor) -> str:
        """Extract surrounding context for a link."""
        if not anchor.parent:
            return ""
            
        # Get text from parent container
        parent_text = anchor.parent.get_text(" ", strip=True)
        
        # Limit context length
        if len(parent_text) > 200:
            # Try to find the most relevant part
            anchor_text = anchor.get_text()
            if anchor_text in parent_text:
                start = parent_text.find(anchor_text)
                context_start = max(0, start - 50)
                context_end = min(len(parent_text), start + len(anchor_text) + 50)
                return parent_text[context_start:context_end].strip()
        
        return parent_text[:200]
    
    def get_stats(self) -> Dict:
        """Get statistics about the last extraction run."""
        # This would be populated during actual runs
        return {
            "total_links_found": 0,
            "lab_links_found": 0,
            "highest_score": 0.0,
            "average_score": 0.0
        }


def demo_link_heuristics():
    """Demo function to show LinkHeuristics in action."""
    sample_html = """
    <div class="faculty-profile">
        <h1>Dr. Jane Smith</h1>
        <p>Dr. Smith is the director of the <a href="/cognitive-lab">Cognitive Neuroscience Laboratory</a> 
           and leads research in memory and attention.</p>
        <p>Visit our <a href="https://coglab.arizona.edu">lab website</a> for more information.</p>
        <p>She also collaborates with the <a href="https://neuro.stanford.edu/center">
           Stanford Neuroscience Research Center</a>.</p>
        <p>Contact: <a href="mailto:jsmith@arizona.edu">jsmith@arizona.edu</a></p>
        <p>Follow us on <a href="https://twitter.com/coglab">Twitter</a></p>
    </div>
    """
    
    soup = BeautifulSoup(sample_html, 'html.parser')
    heuristics = LinkHeuristics(base_url="https://psychology.arizona.edu")
    
    links = heuristics.find_lab_links(soup)
    
    print("Found lab links:")
    for i, link in enumerate(links, 1):
        print(f"{i}. {link['url']} (score: {link['score']:.2f})")
        print(f"   Text: {link['text']}")
        print(f"   Context: {link['context'][:100]}...")
        print()


if __name__ == "__main__":
    demo_link_heuristics() 