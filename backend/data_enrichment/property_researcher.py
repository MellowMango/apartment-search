import os
import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple

from backend.data_enrichment.mcp_client import DeepResearchMCPClient
from backend.data_enrichment.cache_manager import ResearchCacheManager
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
from backend.data_enrichment.research_enrichers.investment_metrics import InvestmentMetricsEnricher
from backend.data_enrichment.research_enrichers.market_analyzer import MarketAnalyzer
from backend.data_enrichment.research_enrichers.risk_assessor import RiskAssessor
from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler

logger = logging.getLogger(__name__)

class PropertyResearcher:
    """
    Main orchestrator for deep property research.
    
    This class coordinates the research process, using the MCP client for deep research
    and specialized enrichers for domain-specific analysis.
    """
    
    def __init__(self, mcp_client=None, db_ops=None, cache_manager=None):
        """
        Initialize the property researcher.
        
        Args:
            mcp_client: Deep Research MCP client (optional)
            db_ops: Database operations (optional)
            cache_manager: Research cache manager (optional)
        """
        self.mcp_client = mcp_client or DeepResearchMCPClient()
        self.db_ops = db_ops or EnrichmentDatabaseOps()
        self.cache_manager = cache_manager or ResearchCacheManager()
        
        # Initialize domain-specific enrichers
        self.investment_metrics = InvestmentMetricsEnricher()
        self.market_analyzer = MarketAnalyzer()
        self.risk_assessor = RiskAssessor()
        self.property_profiler = PropertyProfiler()
        
        logger.info("Property Researcher initialized")
    
    async def research_property(self, 
                             property_id: str = None,
                             property_data: Dict[str, Any] = None,
                             research_depth: str = "standard",
                             force_refresh: bool = False) -> Dict[str, Any]:
        """
        Conduct comprehensive research on a property.
        
        Args:
            property_id: Database ID of property to research (if in database)
            property_data: Property data (if not using database ID)
            research_depth: "basic", "standard", "comprehensive", or "exhaustive"
            force_refresh: Force fresh research ignoring cache
            
        Returns:
            Research results dictionary
        """
        # Get property data if property_id is provided
        if property_id and not property_data:
            property_data = await self.db_ops.get_property_by_id(property_id)
            if not property_data:
                return {"error": f"Property with ID {property_id} not found"}
        
        if not property_data:
            return {"error": "No property data provided"}
        
        # Check cache first
        cache_key = f"research_{property_data.get('id', str(hash(json.dumps(property_data))))}"
        if not force_refresh:
            cached_result = self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Using cached research for property {property_data.get('name', 'Unknown')}")
                return cached_result
        
        # Start timing
        start_time = datetime.now()
        logger.info(f"Starting research for property: {property_data.get('name', 'Unknown')}")
        
        # Initialize research result
        research_result = {
            "property_id": property_data.get("id", ""),
            "property_name": property_data.get("name", ""),
            "research_timestamp": datetime.now().isoformat(),
            "research_depth": research_depth,
            "modules": {}
        }
        
        try:
            # Conduct research using multiple specialized modules
            tasks = [
                self._research_property_details(property_data, research_depth),
                self._research_investment_potential(property_data, research_depth),
                self._research_market_conditions(property_data, research_depth),
                self._research_risks(property_data, research_depth)
            ]
            
            results = await asyncio.gather(*tasks)
            
            # Add results to research_result
            research_result["modules"]["property_details"] = results[0]
            research_result["modules"]["investment_potential"] = results[1]
            research_result["modules"]["market_conditions"] = results[2]
            research_result["modules"]["risks"] = results[3]
            
            # Generate executive summary
            research_result["executive_summary"] = await self._generate_executive_summary(
                property_data, research_result["modules"]
            )
            
            # Calculate elapsed time
            elapsed = datetime.now() - start_time
            research_result["processing_time_seconds"] = elapsed.total_seconds()
            
            # Cache the result
            self.cache_manager.set(cache_key, research_result)
            
            # Update database with research results
            if property_id:
                await self.db_ops.update_property_research(property_id, research_result)
            
            logger.info(f"Completed research for property: {property_data.get('name', 'Unknown')} "
                       f"in {elapsed.total_seconds():.2f} seconds")
            
            return research_result
            
        except Exception as e:
            logger.exception(f"Error during property research: {e}")
            return {
                "error": f"Research error: {str(e)}",
                "property_id": property_data.get("id", ""),
                "property_name": property_data.get("name", ""),
                "research_timestamp": datetime.now().isoformat()
            }
    
    async def _research_property_details(self, 
                                      property_data: Dict[str, Any],
                                      research_depth: str) -> Dict[str, Any]:
        """Research detailed property information"""
        # First, use our specialized property profiler
        profile_result = await self.property_profiler.enrich_property_details(property_data)
        
        # For deeper research, leverage the MCP for advanced extraction
        if research_depth in ["comprehensive", "exhaustive"]:
            # Get deep research from MCP
            mcp_result = await self.mcp_client.research_property(
                property_data=property_data,
                research_depth=research_depth
            )
            
            # Merge results
            if "error" not in mcp_result:
                for key, value in mcp_result.get("property_details", {}).items():
                    if key not in profile_result or not profile_result[key]:
                        profile_result[key] = value
        
        return profile_result
    
    async def _research_investment_potential(self, 
                                          property_data: Dict[str, Any],
                                          research_depth: str) -> Dict[str, Any]:
        """Research investment metrics and potential"""
        # First, use our specialized investment metrics enricher
        metrics_result = await self.investment_metrics.calculate_metrics(property_data)
        
        # For deeper metrics, use the MCP
        if research_depth in ["comprehensive", "exhaustive"]:
            # Get investment analysis from MCP
            mcp_result = await self.mcp_client.analyze_investment_potential(
                property_data=property_data,
                market_data=metrics_result.get("market_data")
            )
            
            # Merge results
            if "error" not in mcp_result:
                metrics_result["lbo_analysis"] = mcp_result.get("lbo_analysis", {})
                metrics_result["investment_scenarios"] = mcp_result.get("investment_scenarios", [])
                metrics_result["valuation_models"] = mcp_result.get("valuation_models", {})
        
        return metrics_result
    
    async def _research_market_conditions(self, 
                                       property_data: Dict[str, Any],
                                       research_depth: str) -> Dict[str, Any]:
        """Research market conditions and trends"""
        # Get location data
        location = {
            "address": property_data.get("address", ""),
            "city": property_data.get("city", ""),
            "state": property_data.get("state", ""),
            "zip": property_data.get("zip", ""),
            "latitude": property_data.get("latitude"),
            "longitude": property_data.get("longitude")
        }
        
        # First, use our specialized market analyzer
        market_result = await self.market_analyzer.analyze_market(
            location=location,
            property_type=property_data.get("property_type", "multifamily")
        )
        
        # For deeper market analysis, use the MCP
        if research_depth in ["comprehensive", "exhaustive"]:
            # Get market intelligence from MCP
            mcp_result = await self.mcp_client.get_market_intelligence(
                location=location,
                property_type=property_data.get("property_type", "multifamily")
            )
            
            # Merge results
            if "error" not in mcp_result:
                market_result["detailed_trends"] = mcp_result.get("trends", {})
                market_result["market_narrative"] = mcp_result.get("narrative", "")
                market_result["competitive_landscape"] = mcp_result.get("competitive_landscape", {})
        
        return market_result
    
    async def _research_risks(self, 
                           property_data: Dict[str, Any],
                           research_depth: str) -> Dict[str, Any]:
        """Research risks and blindspots"""
        # First, use our specialized risk assessor
        risk_result = await self.risk_assessor.assess_risks(property_data)
        
        # For deeper risk analysis, use the MCP
        if research_depth in ["comprehensive", "exhaustive"]:
            # Get risk analysis from MCP
            mcp_result = await self.mcp_client.identify_risks(
                property_data=property_data
            )
            
            # Merge results
            if "error" not in mcp_result:
                risk_result["blindspots"] = mcp_result.get("blindspots", [])
                risk_result["detailed_risks"] = mcp_result.get("detailed_risks", {})
                risk_result["mitigation_strategies"] = mcp_result.get("mitigation_strategies", [])
        
        return risk_result
    
    async def _generate_executive_summary(self, 
                                       property_data: Dict[str, Any],
                                       modules: Dict[str, Dict[str, Any]]) -> str:
        """Generate an executive summary of the research"""
        # Use the MCP client to generate a summary
        summary_payload = {
            "request_type": "executive_summary",
            "property_data": property_data,
            "research_modules": modules
        }
        
        try:
            session = await self.mcp_client._ensure_session()
            async with session.post(
                f"{self.mcp_client.base_url}/summarize",
                json=summary_payload
            ) as response:
                if response.status != 200:
                    return "Error generating executive summary"
                    
                result = await response.json()
                return result.get("summary", "No summary available")
        except Exception as e:
            logger.exception(f"Error generating executive summary: {e}")
            return f"Error generating summary: {str(e)}"
    
    async def batch_research_properties(self, 
                                     property_ids: List[str] = None,
                                     properties: List[Dict[str, Any]] = None,
                                     research_depth: str = "standard",
                                     concurrency: int = 3) -> List[Dict[str, Any]]:
        """
        Research multiple properties in batch mode.
        
        Args:
            property_ids: List of property IDs to research
            properties: List of property data dictionaries
            research_depth: Research depth level
            concurrency: Maximum concurrent researches
            
        Returns:
            List of research results
        """
        if not property_ids and not properties:
            return []
        
        # Get properties from database if IDs provided
        if property_ids and not properties:
            properties = []
            for property_id in property_ids:
                property_data = await self.db_ops.get_property_by_id(property_id)
                if property_data:
                    properties.append(property_data)
        
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def _research_with_semaphore(property_data):
            async with semaphore:
                return await self.research_property(
                    property_id=property_data.get("id"),
                    property_data=property_data,
                    research_depth=research_depth
                )
        
        # Create tasks for each property
        tasks = [_research_with_semaphore(prop) for prop in properties]
        
        # Run all tasks and return results
        return await asyncio.gather(*tasks)
    
    async def close(self):
        """Close all connections"""
        await self.mcp_client.close()
