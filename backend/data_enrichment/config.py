#!/usr/bin/env python3
"""
Configuration for the Deep Property Research System

This module contains configuration settings for the deep property research system,
including MCP server settings, API configurations, and research depth levels.
"""

import os
from typing import Dict, Any, List

# MCP Server Configuration
MCP_CONFIG = {
    "server_name": "property-deep-research",
    "version": "0.1.0",
    "url": os.getenv("DEEP_RESEARCH_MCP_URL", "http://localhost:6020/sse"),
    "timeout": 120,  # seconds
    "retry_attempts": 3,
    "retry_delay": 1,  # seconds
    
    # Capabilities offered by the MCP server
    "capabilities": [
        "property_research",
        "investment_analysis",
        "market_intelligence",
        "risk_assessment",
        "executive_summary"
    ]
}

# Research Depth Levels
RESEARCH_DEPTH_LEVELS = {
    "basic": {
        "description": "Quick analysis using readily available data",
        "api_calls": "minimal",
        "mcp_usage": False,
        "execution_time": "1-2 minutes",
        "data_sources": ["basic property data", "description extraction"]
    },
    "standard": {
        "description": "Standard analysis with some API enrichment",
        "api_calls": "moderate",
        "mcp_usage": True,
        "execution_time": "2-5 minutes",
        "data_sources": ["property data", "basic APIs", "limited MCP analysis"]
    },
    "comprehensive": {
        "description": "Comprehensive analysis with full API enrichment and MCP research",
        "api_calls": "extensive",
        "mcp_usage": True,
        "execution_time": "5-15 minutes",
        "data_sources": ["property data", "all available APIs", "full MCP analysis"]
    },
    "exhaustive": {
        "description": "Maximum depth analysis with all available data sources and advanced MCP research",
        "api_calls": "maximum",
        "mcp_usage": True,
        "execution_time": "15-30 minutes",
        "data_sources": ["property data", "all available APIs", "advanced MCP analysis", "alternative data sources"]
    }
}

# Cache Configuration
CACHE_CONFIG = {
    "memory_cache_size": 100,  # Number of items to keep in memory
    "disk_cache_dir": os.path.join("data", "research_cache"),
    "ttl_days": {
        "property_details": 30,
        "investment_potential": 7,
        "market_conditions": 7,
        "risks": 90,
        "research": 14,
        "default": 7
    }
}

# API Configuration
API_CONFIG = {
    # Financial APIs
    "financial": {
        "fmp": {
            "key_env_var": "FMP_API_KEY",
            "base_url": "https://financialmodelingprep.com/api/v3",
            "rate_limit": 10,  # requests per second
            "timeout": 30  # seconds
        },
        "fred": {
            "key_env_var": "FRED_API_KEY",
            "base_url": "https://api.stlouisfed.org/fred",
            "rate_limit": 5,
            "timeout": 30
        },
        "alpha_vantage": {
            "key_env_var": "ALPHA_VANTAGE_API_KEY",
            "base_url": "https://www.alphavantage.co/query",
            "rate_limit": 5,
            "timeout": 30
        },
        "polygon": {
            "key_env_var": "POLYGON_API_KEY",
            "base_url": "https://api.polygon.io",
            "rate_limit": 5,
            "timeout": 30
        }
    },
    
    # Property-specific APIs
    "property": {
        "property_records": {
            "key_env_var": "PROPERTY_RECORDS_API_KEY",
            "base_url": "https://api.propertyrecords.com/v1",
            "rate_limit": 5,
            "timeout": 30
        },
        "building_permits": {
            "key_env_var": "BUILDING_PERMITS_API_KEY",
            "base_url": "https://api.buildingpermits.com/v1",
            "rate_limit": 5,
            "timeout": 30
        }
    },
    
    # Market and location APIs
    "market": {
        "walkscore": {
            "key_env_var": "WALKSCORE_API_KEY",
            "base_url": "https://api.walkscore.com",
            "rate_limit": 5,
            "timeout": 30
        },
        "census": {
            "key_env_var": "CENSUS_API_KEY",
            "base_url": "https://api.census.gov/data",
            "rate_limit": 5,
            "timeout": 30
        }
    },
    
    # LLM APIs
    "llm": {
        "openai": {
            "key_env_var": "OPENAI_API_KEY",
            "base_url": "https://api.openai.com/v1",
            "rate_limit": 10,
            "timeout": 60
        },
        "anthropic": {
            "key_env_var": "ANTHROPIC_API_KEY",
            "base_url": "https://api.anthropic.com/v1",
            "rate_limit": 10,
            "timeout": 60
        }
    }
}

# Database Operations Configuration
DB_CONFIG = {
    "supabase": {
        "research_table": "property_research",
        "property_table": "properties",
        "batch_size": 50,  # Maximum items to update in a batch
        "update_interval": 86400  # Seconds between auto-updates (1 day)
    },
    "neo4j": {
        "relationship_types": {
            "HAS_RESEARCH": {
                "from": "Property",
                "to": "PropertyResearch"
            },
            "IN_MARKET": {
                "from": "Property",
                "to": "Market"
            },
            "OWNED_BY": {
                "from": "Property",
                "to": "Owner"
            }
        }
    }
}

# Default Properties for Testing
TEST_PROPERTIES = [
    {
        "name": "Riverside Apartments",
        "address": "1234 Riverside Dr",
        "city": "Austin",
        "state": "TX",
        "units": 120,
        "year_built": 1995,
        "property_type": "multifamily",
        "description": "Riverside Apartments is a 120-unit multifamily property built in 1995. The property features a pool, fitness center, and covered parking. Units have washer/dryer connections, granite countertops, and hardwood floors."
    },
    {
        "name": "Downtown Tower",
        "address": "500 Congress Ave",
        "city": "Austin",
        "state": "TX",
        "units": 200,
        "year_built": 2010,
        "property_type": "mixed use",
        "description": "Downtown Tower is a 200-unit mixed-use property built in 2010. The property features ground-floor retail, luxury apartments, and office space. Amenities include a rooftop pool, fitness center, coworking space, and 24-hour concierge service."
    }
]
