"""
University of Arizona Psychology Department scraper.
Captures faculty information including personal websites and lab details.
"""

import re
from typing import List, Dict, Optional
from urllib.parse import urljoin

from .base_university import BaseUniversityScraper


class ArizonaPsychologyScraper(BaseUniversityScraper):
    """Specialized scraper for University of Arizona Psychology Department."""
    
    def __init__(self):
        super().__init__(
            university_name="University of Arizona",
            base_url="https://psychology.arizona.edu",
            department="Psychology"
        )
        self.faculty_list_url = "https://psychology.arizona.edu/people/faculty/core"
    
    async def scrape_faculty_list(self) -> List[Dict]:
        """Scrape the main faculty listing page."""
        html = await self.fetch_page(self.faculty_list_url)
        if not html:
            return []
            
        soup = self.parse_soup(html)
        faculty_members = []
        
        # Find faculty member containers
        faculty_sections = soup.find_all(['article', 'div'], class_=lambda x: x and 'faculty' in x.lower() if x else False)
        
        # If no faculty-specific containers, look for general content areas
        if not faculty_sections:
            faculty_sections = soup.find_all('article')
        
        for section in faculty_sections:
            faculty = self._parse_faculty_listing(section)
            if faculty:
                faculty_members.append(faculty)
        
        # Remove duplicates by name
        seen_names = set()
        unique_faculty = []
        for faculty in faculty_members:
            name = faculty.get('name', '').strip()
            if name and name not in seen_names and len(name) > 1:
                seen_names.add(name)
                unique_faculty.append(faculty)
        
        return unique_faculty
    
    def _parse_faculty_listing(self, section) -> Optional[Dict]:
        """Parse faculty information from a listing section."""
        # Find the faculty name (usually in h3 or h4)
        name_elem = section.find(['h3', 'h4', 'h2'])
        if not name_elem:
            return None
            
        name = self.clean_text(name_elem.get_text())
        
        # Skip navigation elements and non-faculty headings
        skip_terms = ['search', 'navigation', 'main', 'connect', 'people', 'core faculty', 'faculty', 'overview']
        if any(term in name.lower() for term in skip_terms) or len(name) < 2:
            return None
        
        # Extract all text from the section
        section_text = section.get_text()
        
        # Find profile link
        profile_url = self._find_profile_link(section, name)
        
        # Extract basic information
        title = self._extract_title(section_text)
        email = self.extract_email(section_text)
        phone = self._extract_phone_info(section_text)
        
        # Extract research information
        lab_name = self._extract_lab_name(section_text)
        research_areas = self._extract_research_areas(section_text)
        
        # Extract pronouns
        pronouns = self._extract_pronouns(section_text)
        
        # Extract image URL
        image_url = self._extract_image_url(section)
        
        # Look for personal website links in this section
        personal_website = self._find_personal_website(section, name)
        
        return self.create_faculty_dict(
            name=name,
            title=title,
            email=email,
            phone=phone.get('main'),
            office_phone=phone.get('office'),
            lab_phone=phone.get('lab'),
            pronouns=pronouns,
            research_areas=research_areas,
            lab_name=lab_name,
            personal_website=personal_website,
            university_profile_url=profile_url,
            image_url=image_url
        )
    
    def _find_profile_link(self, section, faculty_name: str) -> Optional[str]:
        """Find the faculty member's university profile link."""
        # Look for links that might be profiles
        for link in section.find_all('a', href=True):
            href = link['href']
            link_text = self.clean_text(link.get_text())
            
            # Check if this could be a profile link
            if (faculty_name.lower() in link_text.lower() or 
                '/people/' in href or 
                '/faculty/' in href or
                'profile' in href.lower()):
                
                # Convert relative to absolute URL
                if href.startswith('/'):
                    return urljoin(self.base_url, href)
                elif href.startswith('http'):
                    return href
        
        return None
    
    def _find_personal_website(self, section, faculty_name: str) -> Optional[str]:
        """Find personal website links for the faculty member."""
        for link in section.find_all('a', href=True):
            href = link['href']
            link_text = self.clean_text(link.get_text()).lower()
            
            # Skip obvious non-personal links
            skip_terms = ['email', 'mailto', 'phone', 'tel:', 'office', 'directory']
            if any(term in href.lower() or term in link_text for term in skip_terms):
                continue
            
            # Convert relative to absolute
            if href.startswith('/'):
                full_url = urljoin(self.base_url, href)
            elif href.startswith('http'):
                full_url = href
            else:
                continue
            
            # Check if this looks like a personal website
            if self.is_personal_website(full_url, faculty_name):
                return full_url
        
        return None
    
    def _extract_title(self, text: str) -> Optional[str]:
        """Extract academic title/position."""
        lines = text.split('\n')
        for line in lines:
            line = self.clean_text(line)
            # Look for common academic titles
            if any(title in line.lower() for title in ['professor', 'director', 'chair', 'instructor']):
                return line
        return None
    
    def _extract_phone_info(self, text: str) -> Dict[str, Optional[str]]:
        """Extract different types of phone numbers."""
        phones = {'main': None, 'office': None, 'lab': None}
        
        # Find all phone numbers
        phone_pattern = r'\b\d{3}-\d{3}-\d{4}\b'
        phone_matches = re.finditer(phone_pattern, text)
        
        for match in phone_matches:
            phone_num = match.group()
            # Get context around the phone number
            start = max(0, match.start() - 50)
            end = min(len(text), match.end() + 50)
            context = text[start:end].lower()
            
            if 'office' in context:
                phones['office'] = phone_num
            elif 'lab' in context:
                phones['lab'] = phone_num
            elif not phones['main']:  # First phone number becomes main
                phones['main'] = phone_num
        
        return phones
    
    def _extract_pronouns(self, text: str) -> Optional[str]:
        """Extract pronouns from text."""
        pronouns_match = re.search(r'Pronouns?:\s*([^,\n]+)', text, re.IGNORECASE)
        if pronouns_match:
            return self.clean_text(pronouns_match.group(1))
        return None
    
    def _extract_lab_name(self, text: str) -> Optional[str]:
        """Extract laboratory name."""
        # Look for "Director" mentions with lab/laboratory
        lab_pattern = r'Director,?\s*([^,\n]*(?:Lab|Laboratory|Center|Institute)[^,\n]*)'
        match = re.search(lab_pattern, text, re.IGNORECASE)
        if match:
            return self.clean_text(match.group(1))
        return None
    
    def _extract_research_areas(self, text: str) -> List[str]:
        """Extract research areas and programs."""
        areas = []
        
        # Common research areas in psychology
        research_keywords = [
            'Clinical', 'CNS', 'Social', 'Cognition', 'Neural Systems', 
            'Personality', 'Cognitive', 'Behavioral', 'Developmental',
            'Health Psychology', 'Neuropsychology'
        ]
        
        for keyword in research_keywords:
            if keyword in text:
                areas.append(keyword)
        
        return list(set(areas))  # Remove duplicates
    
    def _extract_image_url(self, section) -> Optional[str]:
        """Extract faculty headshot URL."""
        img = section.find('img')
        if img and img.get('src'):
            src = img['src']
            if src.startswith('/'):
                return urljoin(self.base_url, src)
            elif src.startswith('http'):
                return src
        return None
    
    async def scrape_faculty_profile(self, profile_url: str) -> Optional[Dict]:
        """Scrape detailed information from faculty profile page."""
        html = await self.fetch_page(profile_url)
        if not html:
            return None
        
        soup = self.parse_soup(html)
        
        # Extract detailed information from profile page
        profile_info = {}
        
        # Look for biography/research interests
        bio_elem = soup.find(text=re.compile(r'research|biography|bio|interests', re.I))
        if bio_elem:
            bio_container = bio_elem.parent
            while bio_container and bio_container.name not in ['div', 'section', 'article']:
                bio_container = bio_container.parent
            if bio_container:
                profile_info['bio'] = self.clean_text(bio_container.get_text())
        
        # Look for education information
        education_elem = soup.find(text=re.compile(r'education|degree', re.I))
        if education_elem:
            education_container = education_elem.parent
            while education_container and education_container.name not in ['div', 'section', 'article']:
                education_container = education_container.parent
            if education_container:
                education_text = self.clean_text(education_container.get_text())
                profile_info['education'] = [education_text]
        
        # Look for office location
        office_elem = soup.find(text=re.compile(r'office|room|building', re.I))
        if office_elem:
            office_text = office_elem.parent.get_text() if office_elem.parent else ""
            office_match = re.search(r'(room|office|building)\s*[:\-]?\s*([^\n,]+)', office_text, re.I)
            if office_match:
                profile_info['office_location'] = self.clean_text(office_match.group(2))
        
        # Look for additional websites
        all_urls = self.extract_urls(soup)
        for url in all_urls:
            if self.is_personal_website(url):
                profile_info['personal_website'] = url
                break
        
        # Look for lab website
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = self.clean_text(link.get_text()).lower()
            if 'lab' in link_text or 'laboratory' in link_text:
                if href.startswith('/'):
                    profile_info['lab_website'] = urljoin(self.base_url, href)
                elif href.startswith('http'):
                    profile_info['lab_website'] = href
                break
        
        return profile_info 