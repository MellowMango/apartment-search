#!/usr/bin/env python3
"""
Full HTML Body Content Extraction Demo
======================================

This demonstrates capturing complete HTML body content from academic lab websites
for comprehensive LLM processing, excluding social media content.
"""

import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from pathlib import Path
from datetime import datetime
import re

class FullHTMLExtractor:
    """Extract complete HTML body content from academic websites."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            headers={'User-Agent': 'Academic Research Crawler 1.0'}
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def extract_full_content(self, url: str) -> dict:
        """Extract complete HTML body content and structured data."""
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    html_content = await response.text()
                    soup = BeautifulSoup(html_content, 'html.parser')
                    
                    # Remove script and style elements
                    for script in soup(["script", "style"]):
                        script.decompose()
                    
                    # Remove social media elements (as requested)
                    social_selectors = [
                        'a[href*="facebook"]', 'a[href*="twitter"]', 'a[href*="linkedin"]',
                        'a[href*="instagram"]', 'a[href*="youtube"]', 'a[href*="tiktok"]',
                        '.social', '.social-media', '.social-links', '.social-icons'
                    ]
                    for selector in social_selectors:
                        for element in soup.select(selector):
                            element.decompose()
                    
                    # Extract complete body content
                    body = soup.find('body')
                    if not body:
                        body = soup
                    
                    return {
                        'url': url,
                        'title': soup.find('title').get_text(strip=True) if soup.find('title') else '',
                        'full_html_body': str(body),
                        'full_text_content': body.get_text(separator=' ', strip=True),
                        'structured_content': {
                            'headings': self._extract_headings(body),
                            'paragraphs': self._extract_paragraphs(body),
                            'lists': self._extract_lists(body),
                            'tables': self._extract_tables(body),
                            'links': self._extract_academic_links(body),
                            'images': self._extract_images(body),
                            'contact_info': self._extract_contact_info(body),
                            'research_content': self._extract_research_content(body)
                        },
                        'extraction_timestamp': datetime.now().isoformat(),
                        'content_length': len(str(body)),
                        'text_length': len(body.get_text())
                    }
                else:
                    return {'url': url, 'error': f'HTTP {response.status}'}
        except Exception as e:
            return {'url': url, 'error': str(e)}
    
    def _extract_headings(self, soup):
        """Extract all headings with hierarchy."""
        headings = []
        for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            headings.append({
                'level': tag.name,
                'text': tag.get_text(strip=True),
                'html': str(tag)
            })
        return headings
    
    def _extract_paragraphs(self, soup):
        """Extract all paragraph content."""
        paragraphs = []
        for p in soup.find_all('p'):
            text = p.get_text(strip=True)
            if text and len(text) > 20:  # Filter out short paragraphs
                paragraphs.append({
                    'text': text,
                    'html': str(p)
                })
        return paragraphs
    
    def _extract_lists(self, soup):
        """Extract all lists (ordered and unordered)."""
        lists = []
        for list_tag in soup.find_all(['ul', 'ol']):
            items = [li.get_text(strip=True) for li in list_tag.find_all('li')]
            if items:
                lists.append({
                    'type': list_tag.name,
                    'items': items,
                    'html': str(list_tag)
                })
        return lists
    
    def _extract_tables(self, soup):
        """Extract all table content."""
        tables = []
        for table in soup.find_all('table'):
            rows = []
            for tr in table.find_all('tr'):
                cells = [td.get_text(strip=True) for td in tr.find_all(['td', 'th'])]
                if cells:
                    rows.append(cells)
            if rows:
                tables.append({
                    'rows': rows,
                    'html': str(table)
                })
        return tables
    
    def _extract_academic_links(self, soup):
        """Extract academic and professional links (no social media)."""
        academic_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # Skip social media links
            social_domains = ['facebook.com', 'twitter.com', 'linkedin.com', 'instagram.com', 
                            'youtube.com', 'tiktok.com', 'snapchat.com']
            if any(domain in href.lower() for domain in social_domains):
                continue
            
            # Include academic and professional links
            if href and text and len(text) > 2:
                academic_links.append({
                    'url': href,
                    'text': text,
                    'context': self._get_link_context(link)
                })
        return academic_links[:50]  # Limit to first 50 academic links
    
    def _extract_images(self, soup):
        """Extract image information."""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src', '')
            alt = img.get('alt', '')
            if src:
                images.append({
                    'src': src,
                    'alt': alt,
                    'html': str(img)
                })
        return images
    
    def _extract_contact_info(self, soup):
        """Extract contact information."""
        contact_info = {
            'emails': [],
            'phones': [],
            'addresses': []
        }
        
        text = soup.get_text()
        
        # Extract emails
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        contact_info['emails'] = list(set(re.findall(email_pattern, text)))
        
        # Extract phone numbers
        phone_pattern = r'\b(?:\+?1[-.\s]?)?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}\b'
        contact_info['phones'] = list(set(re.findall(phone_pattern, text)))
        
        return contact_info
    
    def _extract_research_content(self, soup):
        """Extract research-specific content."""
        research_content = {
            'research_interests': [],
            'publications': [],
            'projects': [],
            'equipment': [],
            'methods': []
        }
        
        # Look for research-related sections
        research_keywords = ['research', 'publication', 'project', 'study', 'investigation', 
                           'analysis', 'equipment', 'method', 'technique']
        
        for keyword in research_keywords:
            sections = soup.find_all(string=re.compile(keyword, re.IGNORECASE))
            for section in sections[:10]:  # Limit per keyword
                parent = section.parent
                if parent:
                    content = parent.get_text(strip=True)
                    if len(content) > 50:
                        research_content[f'{keyword}_sections'] = research_content.get(f'{keyword}_sections', [])
                        research_content[f'{keyword}_sections'].append(content[:500])  # First 500 chars
        
        return research_content
    
    def _get_link_context(self, link_element):
        """Get context around a link."""
        parent = link_element.parent
        if parent:
            return parent.get_text(strip=True)[:200]  # First 200 chars of context
        return ""

async def test_full_html_extraction():
    """Test full HTML extraction on academic lab websites."""
    print("🧪 FULL HTML BODY EXTRACTION TEST")
    print("="*80)
    
    # Test URLs - academic lab websites
    test_urls = [
        "https://www.uvm.edu/cas/psychology/profile/robert-althoff",  # Faculty profile
        "https://www.cmu.edu/dietrich/psychology/",  # Department page
        "https://cogscimtu.org/",  # Cognitive science lab (example)
    ]
    
    results = []
    
    async with FullHTMLExtractor(timeout=60) as extractor:
        for url in test_urls:
            print(f"\n🔍 Extracting full content from: {url}")
            
            result = await extractor.extract_full_content(url)
            results.append(result)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                continue
            
            print(f"✅ Title: {result['title']}")
            print(f"📄 HTML Body Length: {result['content_length']:,} characters")
            print(f"📝 Text Content Length: {result['text_length']:,} characters")
            print(f"📊 Structured Content:")
            print(f"   - Headings: {len(result['structured_content']['headings'])}")
            print(f"   - Paragraphs: {len(result['structured_content']['paragraphs'])}")
            print(f"   - Lists: {len(result['structured_content']['lists'])}")
            print(f"   - Tables: {len(result['structured_content']['tables'])}")
            print(f"   - Academic Links: {len(result['structured_content']['links'])}")
            print(f"   - Images: {len(result['structured_content']['images'])}")
            print(f"   - Emails Found: {len(result['structured_content']['contact_info']['emails'])}")
            print(f"   - Phones Found: {len(result['structured_content']['contact_info']['phones'])}")
            
            # Show sample of full HTML content
            html_sample = result['full_html_body'][:1000]
            print(f"\n📄 SAMPLE HTML BODY CONTENT (first 1000 chars):")
            print("-" * 40)
            print(html_sample)
            if len(result['full_html_body']) > 1000:
                print(f"... [truncated, full content is {len(result['full_html_body']):,} characters]")
            
            # Show sample structured content
            if result['structured_content']['paragraphs']:
                print(f"\n📝 SAMPLE PARAGRAPH CONTENT:")
                print("-" * 40)
                print(result['structured_content']['paragraphs'][0]['text'][:300])
                if len(result['structured_content']['paragraphs'][0]['text']) > 300:
                    print("... [truncated]")
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"full_html_extraction_results_{timestamp}.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Full results saved to: {output_file}")
    print(f"📈 Total URLs processed: {len(results)}")
    print(f"✅ Successful extractions: {len([r for r in results if 'error' not in r])}")
    
    print(f"\n🎯 WHAT YOU GET FOR LLM PROCESSING:")
    print("- Complete HTML body content (no social media)")
    print("- Full text content extracted")
    print("- Structured headings, paragraphs, lists, tables")
    print("- Academic links (social media filtered out)")
    print("- Contact information extracted")
    print("- Research-specific content identified")
    print("- Ready for row-by-row LLM processing")

if __name__ == "__main__":
    asyncio.run(test_full_html_extraction()) 