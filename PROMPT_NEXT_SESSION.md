# Next Session: Phase 5 - Collection Layer Improvements

## Objectives

For the next session, we should focus on implementing Phase 5 of the Architecture Migration Plan, focusing on the Collection Layer:

1. Standardizing scraper interfaces and abstractions
2. Implementing adapter patterns for different scraper technologies
3. Adding resilience with proper retry logic
4. Improving monitoring and error tracking
5. Implementing rate limiting and request caching
6. Creating better scheduling and coordination

## Key Tasks

1. **Design Standardized Scraper Interfaces**:
   - Create base interface in `backend/app/interfaces/scraper.py`
   - Define common methods and properties
   - Implement lifecycle hooks (setup, teardown, etc.)
   - Add configuration standardization

2. **Create Adapter Pattern Implementation**:
   - Implement adapter for Playwright scrapers
   - Add adapter for HTTP/API-based collectors
   - Create adapter for existing scraper implementations
   - Design extension points for future technologies

3. **Add Resilience Features**:
   - Implement exponential backoff retry logic
   - Add circuit breaker pattern for external failures
   - Create request throttling mechanisms
   - Implement timeouts and failure handling

4. **Improve Monitoring and Alerting**:
   - Add standardized logging patterns
   - Implement metrics collection for scrapers
   - Create health check mechanisms
   - Add alerting for critical failures

5. **Implement Request Management**:
   - Create rate limiting for external sources
   - Implement HTTP request caching
   - Add request deduplication
   - Create request prioritization

6. **Enhance Scheduling and Coordination**:
   - Implement improved scheduling mechanisms
   - Add dependency management between scrapers
   - Create coordination for distributed scraping
   - Implement result aggregation logic

## Resources and Dependencies

- Existing scraper implementations:
  - `backend/scrapers/*.py`
  - `backend/scrapers/run_scraper.py`
  - `runners/*.py`
- Repository implementations:
  - `backend/app/interfaces/repository.py`
  - `backend/app/db/supabase_repository.py`
- API response and error handling:
  - `backend/app/schemas/api.py`
  - `backend/app/core/exceptions.py`
  - `backend/app/middleware/*.py`

## Implementation Details

### Standardized Scraper Interface

```python
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, List, Optional, Any, Union

class ScraperStatus(Enum):
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    PARTIAL = "partial_success"

class ScraperResult:
    """Standardized result for any scraper operation"""
    success: bool
    items: List[Dict[str, Any]]
    errors: List[Dict[str, Any]]
    stats: Dict[str, Any]
    status: ScraperStatus
    
    @classmethod
    def success(cls, items, stats=None):
        return cls(
            success=True,
            items=items,
            errors=[],
            stats=stats or {},
            status=ScraperStatus.COMPLETED
        )
    
    @classmethod
    def failure(cls, errors, partial_items=None, stats=None):
        return cls(
            success=False,
            items=partial_items or [],
            errors=errors,
            stats=stats or {},
            status=ScraperStatus.FAILED if not partial_items else ScraperStatus.PARTIAL
        )

class BaseScraper(ABC):
    """Base interface for all scrapers"""
    
    @abstractmethod
    async def setup(self) -> bool:
        """Initialize the scraper and required resources"""
        pass
    
    @abstractmethod
    async def scrape(self, **params) -> ScraperResult:
        """Execute the scraping operation"""
        pass
    
    @abstractmethod
    async def teardown(self) -> bool:
        """Clean up resources"""
        pass
    
    @property
    @abstractmethod
    def status(self) -> ScraperStatus:
        """Current status of the scraper"""
        pass
    
    @property
    @abstractmethod
    def metadata(self) -> Dict[str, Any]:
        """Metadata about the scraper"""
        pass
```

### Adapter Pattern for Scraper Technologies

```python
class PlaywrightScraperAdapter(BaseScraper):
    """Adapter for Playwright-based scrapers"""
    
    def __init__(self, config: Dict[str, Any], **kwargs):
        self._config = config
        self._browser = None
        self._page = None
        self._status = ScraperStatus.IDLE
        self._metadata = {
            "type": "playwright",
            "target": config.get("target_url"),
            "source": config.get("source_name"),
            "version": "1.0.0"
        }
    
    async def setup(self) -> bool:
        """Initialize Playwright browser and page"""
        try:
            import playwright.async_api as pw
            
            self._browser = await pw.chromium.launch(
                headless=self._config.get("headless", True)
            )
            self._page = await self._browser.new_page()
            return True
        except Exception as e:
            logger.error(f"Failed to setup Playwright: {str(e)}")
            return False
    
    async def scrape(self, **params) -> ScraperResult:
        """Implement the scraping logic using Playwright"""
        self._status = ScraperStatus.RUNNING
        
        try:
            # Implementation details would depend on specific scraper
            # This is just a skeleton
            await self._page.goto(self._config["target_url"])
            
            # Extract data
            results = []
            errors = []
            
            # Set success based on results
            if results:
                self._status = ScraperStatus.COMPLETED
                return ScraperResult.success(results)
            else:
                self._status = ScraperStatus.FAILED
                return ScraperResult.failure([{"error": "No results found"}])
                
        except Exception as e:
            self._status = ScraperStatus.FAILED
            return ScraperResult.failure([{"error": str(e)}])
    
    async def teardown(self) -> bool:
        """Clean up Playwright resources"""
        try:
            if self._page:
                await self._page.close()
            if self._browser:
                await self._browser.close()
            return True
        except Exception as e:
            logger.error(f"Failed to teardown Playwright: {str(e)}")
            return False
    
    @property
    def status(self) -> ScraperStatus:
        return self._status
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return self._metadata
```

### Resilience Implementation

```python
class RetryConfiguration:
    """Configuration for retry behavior"""
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_backoff: float = 1.0,
        backoff_multiplier: float = 2.0,
        max_backoff: float = 60.0,
        jitter: bool = True
    ):
        self.max_attempts = max_attempts
        self.initial_backoff = initial_backoff
        self.backoff_multiplier = backoff_multiplier
        self.max_backoff = max_backoff
        self.jitter = jitter

class ResilienceScraper(BaseScraper):
    """Decorator that adds resilience to any scraper"""
    
    def __init__(
        self,
        base_scraper: BaseScraper,
        retry_config: RetryConfiguration = None
    ):
        self._scraper = base_scraper
        self._retry_config = retry_config or RetryConfiguration()
        
    async def setup(self) -> bool:
        """Initialize with retry logic"""
        attempt = 0
        
        while attempt < self._retry_config.max_attempts:
            try:
                result = await self._scraper.setup()
                if result:
                    return True
                    
                attempt += 1
                await self._wait_for_backoff(attempt)
            except Exception as e:
                logger.error(f"Setup attempt {attempt} failed: {str(e)}")
                attempt += 1
                if attempt >= self._retry_config.max_attempts:
                    return False
                await self._wait_for_backoff(attempt)
                
        return False
    
    async def scrape(self, **params) -> ScraperResult:
        """Scrape with retry logic"""
        attempt = 0
        
        while attempt < self._retry_config.max_attempts:
            try:
                result = await self._scraper.scrape(**params)
                if result.success:
                    return result
                    
                attempt += 1
                if attempt >= self._retry_config.max_attempts:
                    return result
                await self._wait_for_backoff(attempt)
            except Exception as e:
                logger.error(f"Scrape attempt {attempt} failed: {str(e)}")
                attempt += 1
                if attempt >= self._retry_config.max_attempts:
                    return ScraperResult.failure([{"error": str(e)}])
                await self._wait_for_backoff(attempt)
                
        return ScraperResult.failure([{"error": "Max retry attempts exceeded"}])
    
    async def _wait_for_backoff(self, attempt: int):
        """Calculate and wait for backoff time"""
        import random
        import asyncio
        
        backoff = min(
            self._retry_config.initial_backoff * (self._retry_config.backoff_multiplier ** (attempt - 1)),
            self._retry_config.max_backoff
        )
        
        if self._retry_config.jitter:
            # Add jitter to avoid thundering herd problem
            backoff = backoff * (0.5 + random.random())
            
        logger.info(f"Waiting {backoff:.2f} seconds before retry attempt {attempt}")
        await asyncio.sleep(backoff)
        
    # Delegate other methods to base scraper
    async def teardown(self) -> bool:
        return await self._scraper.teardown()
    
    @property
    def status(self) -> ScraperStatus:
        return self._scraper.status
    
    @property
    def metadata(self) -> Dict[str, Any]:
        return {
            **self._scraper.metadata,
            "resilience": {
                "max_attempts": self._retry_config.max_attempts,
                "backoff_strategy": "exponential"
            }
        }
```

## Testing Plan

- Create unit tests for scraper interfaces and adapters
- Add integration tests for resilience features
- Test rate limiting and caching mechanisms
- Add end-to-end tests for complete scraping workflows
- Create documentation for the new scraper architecture

## Expected Outcomes

1. More reliable and maintainable scrapers
2. Improved error handling and recovery
3. Better monitoring and observability
4. Optimized resource usage with caching and rate limiting
5. Standardized approach for all data collection

## Next Steps

After completing the Collection Layer improvements:
1. Update all existing scrapers to use the new patterns
2. Implement monitoring dashboards for scrapers
3. Add automatic recovery mechanisms
4. Continue with Phase 6: Scheduled Tasks and Background Jobs