# Property Research Enrichers

This directory contains specialized enricher modules for the deep property research system. Each enricher focuses on a specific domain of property analysis, working together to build a comprehensive research profile.

## Architecture

The enrichers follow a modular design pattern:

```
research_enrichers/
├── __init__.py
├── investment_metrics.py    # Financial and investment analysis
├── market_analyzer.py       # Market conditions and trends
├── property_profiler.py     # Detailed property information
├── risk_assessor.py         # Risk and blindspot analysis
└── README.md                # This file
```

Each enricher can work independently with direct API calls, but can also leverage the Microsoft open-deep-research MCP server for more sophisticated analysis when needed.

## Enricher Modules

### Investment Metrics Enricher

**File:** `investment_metrics.py`  
**Class:** `InvestmentMetricsEnricher`

Calculates financial metrics and investment potential:

- Cap rates and NOI estimation
- Property valuation models
- Value-add opportunity identification
- Investment scenarios (hold, value-add, repositioning)
- LBO (Leveraged Buyout) analysis
- ROI projections

**APIs Used:**
- Financial Modeling Prep (FMP)
- FRED (Federal Reserve Economic Data)
- Polygon
- Alpha Vantage

### Market Analyzer

**File:** `market_analyzer.py`  
**Class:** `MarketAnalyzer`

Analyzes market conditions and competitive landscape:

- Comparable property analysis
- Rental rate trends
- Supply/demand metrics
- Market performance indicators
- Demographic analysis
- Future market projections

**APIs Used:**
- Various real estate data APIs
- Census data
- FRED for economic indicators
- Local market data sources

### Property Profiler

**File:** `property_profiler.py`  
**Class:** `PropertyProfiler`

Enhances property details with comprehensive information:

- Ownership and transaction history
- Detailed unit mix analysis
- Construction and renovation details
- Amenities and features analysis
- Zoning and development potential
- Historical performance metrics

**APIs Used:**
- Property records APIs
- Real estate listing data
- Building permit databases
- Public records

### Risk Assessor

**File:** `risk_assessor.py`  
**Class:** `RiskAssessor`

Identifies potential risks and blindspots:

- Legal and regulatory issues
- Environmental concerns
- Maintenance and structural risks
- Tenant profile risk analysis
- Market-related risks
- Financial and operational risks

**APIs Used:**
- Legal databases
- Environmental databases
- Building code databases
- Crime statistics APIs

## How Enrichers Work

Each enricher follows a consistent pattern:

1. **Independent Analysis** - Performs basic analysis using available data and direct API calls
2. **MCP Integration** - For deeper analysis, delegates to the open-deep-research MCP server
3. **Result Merging** - Combines results from direct analysis and MCP-based research
4. **Caching** - Implements efficient caching to minimize redundant API calls

## Common Interfaces

All enrichers implement these common patterns:

### Initialization

```python
def __init__(self):
    # Initialize with API keys from environment
    self.some_api_key = os.getenv("SOME_API_KEY", "")
    self.cache = {}
```

### Main Analysis Method

```python
async def analyze_something(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze something about the property.
    
    Args:
        property_data: Property details
        
    Returns:
        Analysis results dictionary
    """
    # Implementation
```

## Adding a New Enricher

To add a new enricher:

1. Create a new file in this directory (e.g., `new_enricher.py`)
2. Implement a class that follows the common interface pattern
3. Register the enricher in `__init__.py`
4. Update the `PropertyResearcher` class to use your new enricher

Example:

```python
# new_enricher.py
import os
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class NewEnricher:
    def __init__(self):
        self.api_key = os.getenv("NEW_API_KEY", "")
        self.cache = {}
    
    async def analyze_something(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        # Implementation
        return results
```

## Integration with MCP

Enrichers can leverage the MCP client for sophisticated analysis:

```python
async def analyze_something(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
    # First, do basic analysis with direct API calls
    basic_results = self._do_basic_analysis(property_data)
    
    # For deeper analysis, use the MCP
    try:
        mcp_client = DeepResearchMCPClient()
        mcp_results = await mcp_client.some_analysis_method(property_data)
        
        # Merge results
        if "error" not in mcp_results:
            for key, value in mcp_results.items():
                if key not in basic_results:
                    basic_results[key] = value
    except Exception as e:
        logger.error(f"Error using MCP for analysis: {e}")
    
    return basic_results
```

## Error Handling

All enrichers should implement robust error handling:

1. Catch and log exceptions
2. Provide fallback values when APIs fail
3. Return partial results rather than failing completely
4. Use tiered API fallbacks (try preferred API first, then fallbacks)

## Caching Strategy

Enrichers implement a tiered caching strategy:

1. **Memory Cache** - Fast access for recent queries
2. **File Cache** - Persistent storage for less frequent data
3. **Cache Invalidation** - Different TTLs (Time To Live) based on data type:
   - Market data: 7 days
   - Property details: 30 days
   - Risk assessments: 90 days

## Performance Considerations

When implementing enrichers, follow these performance guidelines:

1. Use `asyncio` for concurrent API calls
2. Implement proper connection pooling
3. Batch API requests when possible
4. Use semaphores to limit concurrent external requests
5. Implement exponential backoff for API retries 