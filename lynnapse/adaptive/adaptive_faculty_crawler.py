from bs4 import BeautifulSoup
from typing import List, Dict
from urllib.parse import urljoin

class AdaptiveFacultyCrawler:
    def _extract_stanford_faculty(self, soup: BeautifulSoup, url: str) -> List[Dict[str, str]]:
        """Extract faculty from Stanford's specific page structure."""
        faculty = []
        
        try:
            # Look for faculty in the views structure
            faculty_divs = soup.find_all('div', class_='views-field views-field-title')
            
            if not faculty_divs:
                # Fallback to h3 headers containing names
                headers = soup.find_all(['h3', 'h4'])
            else:
                headers = []
                for div in faculty_divs:
                    h3 = div.find('h3')
                    if h3:
                        headers.append(h3)
            
            self.logger.debug(f"Found {len(headers)} potential faculty headers")
            
            for header in headers:
                try:
                    # Skip if header is not a proper element
                    if not hasattr(header, 'get_text'):
                        continue
                        
                    name = header.get_text(strip=True)
                    if not name or len(name) < 2:
                        continue
                    
                    # Clean the name
                    name = self.data_cleaner.normalize_name(name)
                    if not name:
                        continue
                    
                    # Try to find profile URL from parent link
                    profile_url = ""
                    parent_link = header.find_parent('a')
                    if parent_link and parent_link.get('href'):
                        profile_url = parent_link['href']
                        if profile_url.startswith('/'):
                            profile_url = urljoin(url, profile_url)
                    
                    # Try to extract email - look in surrounding elements
                    email = ""
                    
                    # Look for email in the same container or nearby elements
                    parent_container = header.find_parent('div')
                    if parent_container:
                        email_text = parent_container.get_text()
                        emails = self.data_cleaner.extract_emails(email_text)
                        if emails:
                            email = emails[0]
                    
                    # If no email found in container, try siblings
                    if not email:
                        next_sibling = header.find_next_sibling()
                        if next_sibling and hasattr(next_sibling, 'get_text'):
                            emails = self.data_cleaner.extract_emails(next_sibling.get_text())
                            if emails:
                                email = emails[0]
                    
                    faculty_info = {
                        'name': name,
                        'title': '',  # Not easily extractable from this format
                        'email': email,
                        'profile_url': profile_url,
                        'department': 'Psychology',
                        'university': 'Stanford University'
                    }
                    
                    faculty.append(faculty_info)
                    self.logger.debug(f"Extracted faculty: {name} ({email})")
                    
                except Exception as e:
                    self.logger.debug(f"Error processing header: {e}")
                    continue
                    
        except Exception as e:
            self.logger.error(f"Error in Stanford faculty extraction: {e}")
        
        return faculty 