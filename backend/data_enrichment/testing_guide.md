# Data Enrichment Testing Guide

This guide provides a structured approach to testing the data enrichment module, troubleshooting common issues, and verifying that all components are working properly.

## Prerequisites

1. Ensure all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   ```

2. Verify environment variables are set (check `.env` file):
   ```
   OPENAI_API_KEY=your_key
   ANTHROPIC_API_KEY=your_key
   GOOGLE_PLACES_API_KEY=your_key
   # Additional API keys as needed
   ```

3. Ensure database connections are configured properly (if using database features)

## Basic Testing

Start with the simplest tests to verify core functionality:

```bash
# Run a basic test with sample properties
python -m backend.data_enrichment.cli test --depth basic

# Test with a specific sample property from a file
echo '{"name":"Test Property","address":"123 Main St","city":"Austin","state":"TX","units":100,"year_built":2005,"description":"Test property for research"}' > test_property.json
python -m backend.data_enrichment.cli research-file --input-file test_property.json --depth basic --output-file test_output.json
```

## Troubleshooting Dependencies

If you encounter dependency issues:

1. Check Python paths:
   ```python
   import sys
   print(sys.path)
   ```

2. Verify imports by running a minimal script:
   ```python
   # save as verify_imports.py
   import os
   import sys
   
   # Add project root to path
   sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
   
   # Try importing each module
   try:
       from backend.data_enrichment.property_researcher import PropertyResearcher
       print("PropertyResearcher: OK")
   except Exception as e:
       print(f"PropertyResearcher import error: {e}")
       
   try:
       from backend.data_enrichment.mcp_client import DeepResearchMCPClient
       print("DeepResearchMCPClient: OK")
   except Exception as e:
       print(f"DeepResearchMCPClient import error: {e}")
   
   # Add other imports as needed
   ```

3. Run with specific environment variables for debugging:
   ```bash
   DEBUG=1 python -m backend.data_enrichment.cli test --depth basic
   ```

## Testing Each Component

To isolate issues, test each component separately:

### 1. Test Property Profiler

```python
# save as test_property_profiler.py
import os
import sys
import asyncio
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler
from backend.data_enrichment.config import TEST_PROPERTIES

async def test_profiler():
    profiler = PropertyProfiler()
    test_property = TEST_PROPERTIES[0]
    
    print(f"Testing property profiler with: {test_property['address']}, {test_property['city']}")
    
    result = await profiler.profile_property(
        property_data=test_property,
        depth="basic"
    )
    
    print("\nProperty Profile Results:")
    print(json.dumps(result, indent=2))
    
    return result

if __name__ == "__main__":
    asyncio.run(test_profiler())
```

### 2. Test Investment Metrics Enricher

Create similar test scripts for each enricher.

## Testing the MCP Integration

If you're using the MCP server:

```python
# save as test_mcp.py
import os
import sys
import asyncio
import json

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data_enrichment.mcp_client import DeepResearchMCPClient
from backend.data_enrichment.config import TEST_PROPERTIES

async def test_mcp():
    client = DeepResearchMCPClient()
    test_property = TEST_PROPERTIES[0]
    
    print(f"Testing MCP with: {test_property['address']}, {test_property['city']}")
    
    try:
        result = await client.research_property(test_property)
        print("\nMCP Research Results:")
        print(json.dumps(result, indent=2))
        return result
    except Exception as e:
        print(f"MCP error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    asyncio.run(test_mcp())
```

## Mocking External APIs for Testing

For reliable testing without hitting actual APIs:

```python
# save as test_with_mocks.py
import os
import sys
import asyncio
import json
import unittest
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.config import TEST_PROPERTIES

class TestWithMocks(unittest.TestCase):
    
    @patch('backend.data_enrichment.research_enrichers.property_profiler.PropertyProfiler.profile_property')
    @patch('backend.data_enrichment.research_enrichers.investment_metrics.InvestmentMetricsEnricher.calculate_metrics')
    async def test_research_with_mocks(self, mock_investment, mock_profiler):
        # Setup mocks
        mock_profiler.return_value = {
            "property_type": "multifamily",
            "units": 150,
            "year_built": 2005,
            "ownership_history": {"current_owner": "Test Owner"}
        }
        
        mock_investment.return_value = {
            "cap_rate": 5.2,
            "price_per_unit": 125000,
            "projected_irr": 12.5
        }
        
        # Test with mocks
        researcher = PropertyResearcher()
        result = await researcher.research_property(
            property_data=TEST_PROPERTIES[0],
            research_depth="basic"
        )
        
        self.assertIn('modules', result)
        self.assertIn('property_details', result['modules'])
        self.assertIn('investment_potential', result['modules'])
        
        return result

def run_test():
    test = TestWithMocks()
    loop = asyncio.get_event_loop()
    result = loop.run_until_complete(test.test_research_with_mocks())
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    run_test()
```

## Advanced Testing Scenarios

Once basic functionality is confirmed, test more complex scenarios:

1. Test with different research depths:
   ```bash
   python -m backend.data_enrichment.cli test --depth standard
   python -m backend.data_enrichment.cli test --depth comprehensive
   ```

2. Test batch processing:
   ```bash
   python -m backend.data_enrichment.cli batch-research --limit 3 --depth basic --concurrency 2
   ```

3. Test with missing or invalid data to verify error handling:
   ```python
   # Create test with missing fields
   invalid_property = {"name": "Invalid Property", "city": "Austin"}
   # Then use this property for testing
   ```

## Performance Testing

For larger deployments, measure performance:

```python
# save as performance_test.py
import os
import sys
import asyncio
import time
import statistics
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.config import TEST_PROPERTIES

async def performance_test(iterations=5, depth="basic"):
    researcher = PropertyResearcher()
    test_property = TEST_PROPERTIES[0]
    
    print(f"Running performance test with {iterations} iterations at {depth} depth")
    
    durations = []
    for i in range(iterations):
        start_time = time.time()
        
        result = await researcher.research_property(
            property_data=test_property,
            research_depth=depth,
            force_refresh=True
        )
        
        duration = time.time() - start_time
        durations.append(duration)
        print(f"Iteration {i+1}: {duration:.2f} seconds")
    
    avg_duration = statistics.mean(durations)
    min_duration = min(durations)
    max_duration = max(durations)
    
    print("\nPerformance Summary:")
    print(f"Average duration: {avg_duration:.2f} seconds")
    print(f"Min duration: {min_duration:.2f} seconds")
    print(f"Max duration: {max_duration:.2f} seconds")

if __name__ == "__main__":
    asyncio.run(performance_test())
```

## Common Issues and Solutions

1. **Import errors**: Ensure your Python path includes the project root
2. **API key issues**: Verify keys are correctly set in environment variables
3. **MCP server connection**: Check if the MCP server is running and configured correctly
4. **Missing dependencies**: Run `pip install -r requirements.txt` again
5. **Timeout errors**: Increase timeout settings for external API calls
6. **Caching issues**: Clear cache files and directories if testing new changes

## Debugging Tips

1. Add temporary debug logging:
   ```python
   import logging
   logging.basicConfig(level=logging.DEBUG)
   ```

2. Inspect intermediate results:
   ```python
   # Add in property_researcher.py
   print(f"API response: {response}")
   ```

3. Use `asyncio.gather()` with `return_exceptions=True` to see which async tasks fail

## Next Steps

After testing, consider implementing:

1. Continuous integration tests
2. More comprehensive error handling
3. Fallbacks for when APIs are unavailable
4. A test coverage report