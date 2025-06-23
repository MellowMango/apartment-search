"""
HTML scraper using Playwright - First layer of the three-layer scraping strategy.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import time

from playwright.async_api import async_playwright, Browser, Page, TimeoutError as PlaywrightTimeoutError


logger = logging.getLogger(__name__)


class HTMLScraper:
    """HTML scraper using Playwright for dynamic content."""
    
    def __init__(self, headless: bool = True, timeout: int = 30000):
        """Initialize the HTML scraper."""
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None
        self.playwright = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def start(self) -> None:
        """Start the Playwright browser."""
        try:
            self.playwright = await async_playwright().start()
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            logger.info("Playwright browser started successfully")
        except Exception as e:
            logger.error(f"Failed to start Playwright browser: {e}")
            raise
    
    async def close(self) -> None:
        """Close the Playwright browser."""
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        logger.info("Playwright browser closed")
    
    async def scrape_page(self, url: str, wait_for_selector: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape a single page using Playwright.
        
        Args:
            url: URL to scrape
            wait_for_selector: Optional CSS selector to wait for before scraping
            
        Returns:
            Dictionary containing scraped data and metadata
        """
        start_time = time.time()
        
        if not self.browser:
            await self.start()
        
        page = await self.browser.new_page()
        
        try:
            # Navigate to the page
            response = await page.goto(url, timeout=self.timeout)
            
            if not response:
                raise Exception(f"Failed to load page: {url}")
            
            # Wait for specific selector if provided
            if wait_for_selector:
                await page.wait_for_selector(wait_for_selector, timeout=self.timeout)
            else:
                # Wait for network to be idle
                await page.wait_for_load_state('networkidle', timeout=self.timeout)
            
            # Extract page content
            content = await page.content()
            title = await page.title()
            
            # Extract links
            links = await page.evaluate("""
                () => {
                    return Array.from(document.querySelectorAll('a[href]')).map(a => ({
                        text: a.textContent?.trim() || '',
                        href: a.href,
                        title: a.title || ''
                    }));
                }
            """)
            
            # Extract meta information
            meta_description = await page.get_attribute('meta[name="description"]', 'content') or ''
            meta_keywords = await page.get_attribute('meta[name="keywords"]', 'content') or ''
            
            # Extract text content
            text_content = await page.evaluate("""
                () => document.body.innerText || document.body.textContent || ''
            """)
            
            load_time = time.time() - start_time
            
            result = {
                'url': url,
                'status_code': response.status,
                'title': title,
                'content': content,
                'text_content': text_content,
                'meta_description': meta_description,
                'meta_keywords': meta_keywords,
                'links': links,
                'load_time_seconds': load_time,
                'scraped_at': datetime.utcnow().isoformat(),
                'scraper_method': 'playwright',
                'success': True
            }
            
            logger.info(f"Successfully scraped {url} in {load_time:.2f}s")
            return result
            
        except PlaywrightTimeoutError as e:
            logger.error(f"Timeout scraping {url}: {e}")
            return {
                'url': url,
                'error': f"Timeout: {str(e)}",
                'success': False,
                'scraper_method': 'playwright',
                'scraped_at': datetime.utcnow().isoformat()
            }
        except Exception as e:
            logger.error(f"Error scraping {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'success': False,
                'scraper_method': 'playwright',
                'scraped_at': datetime.utcnow().isoformat()
            }
        finally:
            await page.close()
    
    async def scrape_multiple_pages(self, urls: List[str], 
                                   max_concurrent: int = 3,
                                   wait_for_selector: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Scrape multiple pages concurrently.
        
        Args:
            urls: List of URLs to scrape
            max_concurrent: Maximum number of concurrent scraping operations
            wait_for_selector: Optional CSS selector to wait for
            
        Returns:
            List of scraping results
        """
        if not self.browser:
            await self.start()
        
        semaphore = asyncio.Semaphore(max_concurrent)
        
        async def scrape_with_semaphore(url: str) -> Dict[str, Any]:
            async with semaphore:
                return await self.scrape_page(url, wait_for_selector)
        
        tasks = [scrape_with_semaphore(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'url': urls[i],
                    'error': str(result),
                    'success': False,
                    'scraper_method': 'playwright',
                    'scraped_at': datetime.utcnow().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def extract_faculty_links(self, url: str) -> List[Dict[str, str]]:
        """
        Extract faculty profile links from a faculty directory page.
        
        Args:
            url: Faculty directory URL
            
        Returns:
            List of faculty profile links with metadata
        """
        page_data = await self.scrape_page(url)
        
        if not page_data.get('success'):
            return []
        
        if not self.browser:
            await self.start()
        
        page = await self.browser.new_page()
        
        try:
            await page.goto(url, timeout=self.timeout)
            await page.wait_for_load_state('networkidle', timeout=self.timeout)
            
            # Extract faculty links using common patterns
            faculty_links = await page.evaluate("""
                () => {
                    const links = [];
                    const selectors = [
                        'a[href*="faculty"]',
                        'a[href*="people"]',
                        'a[href*="staff"]',
                        '.faculty-list a',
                        '.people-list a',
                        '.directory a',
                        'a[href*="profile"]'
                    ];
                    
                    selectors.forEach(selector => {
                        document.querySelectorAll(selector).forEach(link => {
                            const text = link.textContent?.trim() || '';
                            const href = link.href;
                            
                            // Filter for faculty-related links
                            if (href && (
                                href.includes('faculty') || 
                                href.includes('people') || 
                                href.includes('profile') ||
                                text.toLowerCase().includes('dr.') ||
                                text.toLowerCase().includes('prof')
                            )) {
                                links.push({
                                    name: text,
                                    url: href,
                                    title: link.title || ''
                                });
                            }
                        });
                    });
                    
                    // Remove duplicates
                    const unique = [];
                    const seen = new Set();
                    links.forEach(link => {
                        if (!seen.has(link.url)) {
                            seen.add(link.url);
                            unique.push(link);
                        }
                    });
                    
                    return unique;
                }
            """)
            
            logger.info(f"Extracted {len(faculty_links)} faculty links from {url}")
            return faculty_links
            
        except Exception as e:
            logger.error(f"Error extracting faculty links from {url}: {e}")
            return []
        finally:
            await page.close() 