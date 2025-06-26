"""
DataCleaner - Text normalization and data cleaning utilities.

Provides comprehensive text cleaning, normalization, and extraction
functionality for scraped university data.
"""

import re
import html
import logging
from typing import List, Optional, Dict, Any, Set
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup, Tag


logger = logging.getLogger(__name__)


class DataCleaner:
    """Utility class for cleaning and normalizing scraped data."""
    
    def __init__(self):
        """Initialize the data cleaner with regex patterns."""
        # Email patterns
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Phone patterns (US format)
        self.phone_patterns = [
            re.compile(r'\((\d{3})\)\s*(\d{3})-(\d{4})'),  # (520) 123-4567
            re.compile(r'(\d{3})-(\d{3})-(\d{4})'),        # 520-123-4567
            re.compile(r'(\d{3})\.(\d{3})\.(\d{4})'),      # 520.123.4567
            re.compile(r'(\d{3})\s+(\d{3})\s+(\d{4})'),    # 520 123 4567
            re.compile(r'(\d{10})'),                       # 5201234567
        ]
        
        # URL patterns
        self.url_pattern = re.compile(
            r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'
        )
        
        # Academic domains for website validation
        self.academic_domains = {'.edu', '.ac.', '.org'}
        
        # Common title prefixes/suffixes
        self.title_prefixes = {'Dr.', 'Professor', 'Prof.', 'Mr.', 'Ms.', 'Mrs.'}
        self.title_suffixes = {'Ph.D.', 'PhD', 'M.D.', 'MD', 'J.D.', 'JD'}
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize text content.
        
        Args:
            text: Raw text to clean
            
        Returns:
            Cleaned and normalized text
        """
        if not text:
            return ""
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove non-printable characters
        text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\xff]', '', text)
        
        return text
    
    def clean_html(self, html_content: str) -> str:
        """
        Extract clean text from HTML content.
        
        Args:
            html_content: Raw HTML content
            
        Returns:
            Cleaned text content
        """
        if not html_content:
            return ""
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text and clean it
        text = soup.get_text()
        return self.clean_text(text)
    
    def extract_emails(self, text: str) -> List[str]:
        """
        Extract email addresses from text.
        
        Args:
            text: Text to search for emails
            
        Returns:
            List of unique email addresses
        """
        if not text:
            return []
        
        emails = self.email_pattern.findall(text)
        return list(set(email.lower() for email in emails))
    
    def extract_phone_numbers(self, text: str) -> List[str]:
        """
        Extract and normalize phone numbers from text.
        
        Args:
            text: Text to search for phone numbers
            
        Returns:
            List of normalized phone numbers
        """
        if not text:
            return []
        
        phones = []
        
        for pattern in self.phone_patterns:
            matches = pattern.findall(text)
            for match in matches:
                if isinstance(match, tuple):
                    # Format: (area, exchange, number)
                    if len(match) == 3:
                        phone = f"({match[0]}) {match[1]}-{match[2]}"
                    else:
                        continue
                else:
                    # Single match - format as (xxx) xxx-xxxx
                    if len(match) == 10:
                        phone = f"({match[:3]}) {match[3:6]}-{match[6:]}"
                    else:
                        continue
                
                phones.append(phone)
        
        return list(set(phones))
    
    def extract_urls(self, text: str, base_url: Optional[str] = None) -> List[str]:
        """
        Extract URLs from text.
        
        Args:
            text: Text to search for URLs
            base_url: Base URL for resolving relative URLs
            
        Returns:
            List of absolute URLs
        """
        if not text:
            return []
        
        urls = []
        
        # Find all URLs in text
        for match in self.url_pattern.finditer(text):
            url = match.group(0)
            
            # Convert relative URLs to absolute if base_url provided
            if base_url and not url.startswith(('http://', 'https://')):
                url = urljoin(base_url, url)
            
            urls.append(url)
        
        return list(set(urls))
    
    def normalize_name(self, name: str) -> str:
        """
        Normalize a person's name by removing titles and cleaning.
        
        Args:
            name: Raw name string
            
        Returns:
            Normalized name
        """
        if not name:
            return ""
        
        name = self.clean_text(name)
        
        # Remove common titles
        for prefix in self.title_prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        
        for suffix in self.title_suffixes:
            if name.endswith(suffix):
                name = name[:-len(suffix)].strip()
        
        # Remove extra commas and normalize
        name = re.sub(r',\s*,', ',', name)
        name = re.sub(r',\s*$', '', name)
        
        return name.strip()
    
    def normalize_title(self, title: str) -> str:
        """
        Normalize an academic title.
        
        Args:
            title: Raw title string
            
        Returns:
            Normalized title
        """
        if not title:
            return ""
        
        title = self.clean_text(title)
        
        # Common title normalizations
        title = re.sub(r'\bProf\b', 'Professor', title)
        title = re.sub(r'\bAsst\b', 'Assistant', title)
        title = re.sub(r'\bAssoc\b', 'Associate', title)
        
        return title.strip()
    
    def extract_research_areas(self, text: str) -> List[str]:
        """
        Extract research areas from text using keyword matching.
        
        Args:
            text: Text to analyze
            
        Returns:
            List of identified research areas
        """
        if not text:
            return []
        
        # Common psychology research areas
        research_keywords = [
            'Clinical Psychology', 'Cognitive Psychology', 'Social Psychology',
            'Developmental Psychology', 'Neuropsychology', 'Behavioral Psychology',
            'Health Psychology', 'Educational Psychology', 'Personality Psychology',
            'Biological Psychology', 'Experimental Psychology', 'Applied Psychology',
            'Cognitive Neuroscience', 'Behavioral Neuroscience', 'Psychopathology',
            'Psychotherapy', 'Assessment', 'Statistics', 'Research Methods',
            'Memory', 'Attention', 'Perception', 'Learning', 'Motivation',
            'Emotion', 'Stress', 'Anxiety', 'Depression', 'ADHD', 'Autism',
            'Aging', 'Child Development', 'Family Psychology', 'Group Therapy',
            'Trauma', 'PTSD', 'Addiction', 'Substance Abuse', 'Eating Disorders'
        ]
        
        found_areas = []
        text_lower = text.lower()
        
        for area in research_keywords:
            if area.lower() in text_lower:
                found_areas.append(area)
        
        return found_areas
    
    def extract_lab_name(self, text: str) -> Optional[str]:
        """
        Extract laboratory name from text.
        
        Args:
            text: Text to search
            
        Returns:
            Laboratory name if found
        """
        if not text:
            return None
        
        # Look for lab name patterns
        lab_patterns = [
            r'Director,?\s*([^,\n]*(?:Lab|Laboratory|Center|Institute)[^,\n]*)',
            r'([^,\n]*(?:Lab|Laboratory|Center|Institute)[^,\n]*)',
            r'PI,?\s*([^,\n]*(?:Lab|Laboratory)[^,\n]*)'
        ]
        
        for pattern in lab_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                lab_name = self.clean_text(match.group(1))
                if len(lab_name) > 5:  # Minimum reasonable length
                    return lab_name
        
        return None
    
    def is_academic_website(self, url: str) -> bool:
        """
        Determine if a URL is likely an academic website.
        
        Args:
            url: URL to check
            
        Returns:
            True if URL appears to be academic
        """
        if not url:
            return False
        
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # Check for academic domains
            for academic_domain in self.academic_domains:
                if academic_domain in domain:
                    return True
            
            return False
            
        except Exception:
            return False
    
    def extract_personal_website(self, links: List[str], faculty_name: str, 
                                base_url: str) -> Optional[str]:
        """
        Intelligent extraction of personal academic websites.
        
        Args:
            links: List of URLs to analyze
            faculty_name: Faculty member's name for matching
            base_url: Base university URL
            
        Returns:
            Most likely personal website URL
        """
        if not links or not faculty_name:
            return None
        
        candidates = []
        name_parts = faculty_name.lower().split()
        
        for link in links:
            if not self.is_academic_website(link):
                continue
            
            link_lower = link.lower()
            
            # Skip email and phone links
            if link_lower.startswith(('mailto:', 'tel:')):
                continue
            
            # Skip social media
            if any(social in link_lower for social in ['twitter', 'facebook', 'linkedin', 'instagram']):
                continue
            
            score = 0
            
            # Personal page indicators
            personal_indicators = ['/~', '/people/', '/faculty/', '/profile/', 'personal', 'homepage']
            for indicator in personal_indicators:
                if indicator in link_lower:
                    score += 2
            
            # Name matching
            for name_part in name_parts:
                if len(name_part) > 2 and name_part in link_lower:
                    score += 3
            
            # Prefer same domain
            if base_url and urlparse(base_url).netloc in link:
                score += 1
            
            if score > 0:
                candidates.append((link, score))
        
        if candidates:
            # Return the highest scoring candidate
            return max(candidates, key=lambda x: x[1])[0]
        
        return None
    
    def clean_bio_text(self, bio: str) -> str:
        """
        Clean biography text by removing HTML and normalizing.
        
        Args:
            bio: Raw biography text
            
        Returns:
            Cleaned biography text
        """
        if not bio:
            return ""
        
        # Remove HTML if present
        bio = self.clean_html(bio)
        
        # Remove excessive newlines
        bio = re.sub(r'\n\s*\n', '\n', bio)
        
        # Normalize whitespace
        bio = self.clean_text(bio)
        
        return bio
    
    def extract_pronouns(self, text: str) -> Optional[str]:
        """
        Extract pronouns from text.
        
        Args:
            text: Text to search
            
        Returns:
            Pronouns if found
        """
        if not text:
            return None
        
        # Common pronoun patterns
        pronoun_patterns = [
            r'\b((?:He|She|They)/(?:Him|Her|Them))\b',
            r'\b((?:he|she|they)/(?:him|her|them))\b',
            r'\(([^)]*(?:he|she|they)/[^)]*)\)',
            r'Pronouns?\s*:\s*([^,\n.]+)'
        ]
        
        for pattern in pronoun_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                pronouns = self.clean_text(match.group(1))
                if pronouns:
                    return pronouns
        
        return None 