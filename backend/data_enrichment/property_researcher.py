import os
import json
import asyncio
import logging
import time
import random
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple, Callable

from backend.data_enrichment.mcp_client import DeepResearchMCPClient
from backend.data_enrichment.cache_manager import ResearchCacheManager
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
from backend.data_enrichment.geocoding_service import GeocodingService

logger = logging.getLogger(__name__)

class PropertyResearcher:
    """
    Main orchestrator for deep property research.
    
    This class coordinates the research process, using the MCP client for deep research
    and specialized enrichers for domain-specific analysis.
    """
    
    def __init__(self, mcp_client=None, db_ops=None, cache_manager=None, geocoding_service=None):
        """
        Initialize the property researcher.
        
        Args:
            mcp_client: Deep Research MCP client (optional)
            db_ops: Database operations (optional)
            cache_manager: Research cache manager (optional)
            geocoding_service: Geocoding service (optional)
        """
        self.mcp_client = mcp_client or DeepResearchMCPClient()
        self.db_ops = db_ops or EnrichmentDatabaseOps()
        self.cache_manager = cache_manager or ResearchCacheManager()
        self.geocoding_service = geocoding_service or GeocodingService(cache_manager=self.cache_manager)
        
        # Initialize domain-specific enrichers
        from backend.data_enrichment.research_enrichers.investment_metrics import InvestmentMetricsEnricher
        from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler
        from backend.data_enrichment.research_enrichers.market_analyzer import MarketAnalyzer
        from backend.data_enrichment.research_enrichers.risk_assessor import RiskAssessor
        
        self.investment_metrics = InvestmentMetricsEnricher()
        self.property_profiler = PropertyProfiler()
        self.market_analyzer = MarketAnalyzer()  # Initialize our new Market Analyzer
        self.risk_assessor = RiskAssessor()      # Initialize our new Risk Assessor
        
        logger.info("Property Researcher initialized with all enrichers and geocoding service")
    
    async def research_property(self, property_data: Dict[str, Any], 
                                research_depth: str = "standard",
                                force_refresh: bool = False) -> Dict[str, Any]:
        """
        Conduct deep research on a property.
        
        Args:
            property_data: Property details
            research_depth: Depth of research (basic, standard, comprehensive, exhaustive)
            force_refresh: Force refresh of cached data
            
        Returns:
            Comprehensive research results
        """
        # Validate property data
        if not self._validate_property_data(property_data):
            return {"error": "Invalid property data. Required fields: address, city, state."}
        
        # Create cache key
        property_id = property_data.get("id") or property_data.get("property_id")
        address = property_data.get("address", "")
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        
        cache_key = f"research:{property_id or ''}:{address}:{city}:{state}:{research_depth}"
        
        # Check cache first unless force refresh is requested
        if not force_refresh:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Using cached research for {address}, {city}, {state}")
                return cached_result
        
        # Initialize research results
        research_results = {
            "property_id": property_id,
            "property_address": address,
            "city": city,
            "state": state,
            "research_depth": research_depth,
            "research_date": datetime.now().isoformat(),
            "modules": {}
        }
        
        # For MVP, log which of the essential fields are missing from the initial data
        essential_fields = ["address", "latitude", "longitude", "property_website", "name", "year_built", "units", "broker_website"]
        missing_fields = [field for field in essential_fields if not property_data.get(field)]
        if missing_fields:
            logger.info(f"Property {address} missing essential fields for MVP: {', '.join(missing_fields)}")
            
        # If coordinates are missing, geocode the property
        if not self._has_valid_coordinates(property_data):
            logger.info(f"Property {address} missing coordinates, geocoding...")
            property_data = await self.geocode_property(property_data)
        
        # Execute research modules concurrently based on depth
        tasks = []
        
        # Add basic tasks
        tasks.append(self._research_property_details(property_data, research_depth))
        tasks.append(self._research_investment_potential(property_data, research_depth))
        
        # Add market analysis task for standard depth and above
        if research_depth in ["standard", "comprehensive", "exhaustive"]:
            tasks.append(self._research_market_conditions(property_data, research_depth))
        
        # Add risk assessment task for comprehensive and exhaustive depths
        if research_depth in ["comprehensive", "exhaustive"]:
            tasks.append(self._research_risk_assessment(property_data, research_depth))
        
        # Debug tasks
        logger.info(f"Executing {len(tasks)} research tasks concurrently")
        
        for i, task in enumerate(tasks):
            if task is None:
                logger.error(f"Task {i} is None")
                continue
        
        # Execute all research tasks concurrently (avoid None tasks)
        tasks = [task for task in tasks if task is not None]
        
        if not tasks:
            logger.error("No valid research tasks were found")
            research_results["error"] = "No valid research tasks were found"
            return research_results
        
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Error in research module {i}: {result}")
                    continue
                
                # Add successful results to the research_results
                if isinstance(result, dict):
                    logger.info(f"Adding result keys: {list(result.keys())}")
                    research_results["modules"].update(result)
                else:
                    logger.error(f"Unexpected result type in module {i}: {type(result)}")
        except Exception as e:
            logger.error(f"Error during task execution: {str(e)}")
            research_results["error"] = f"Error during task execution: {str(e)}"
        
        # For comprehensive and exhaustive research, get executive summary from MCP
        if research_depth in ["comprehensive", "exhaustive"]:
            try:
                # Add property modules to context for summary generation
                context = {
                    "property_data": property_data,
                    "research_results": research_results["modules"]
                }
                summary = await self.mcp_client.generate_executive_summary(context)
                research_results["executive_summary"] = summary
            except Exception as e:
                logger.error(f"Error generating executive summary: {e}")
                # Generate a basic summary if MCP fails
                research_results["executive_summary"] = self._generate_basic_summary(research_results)
        else:
            # Generate a basic summary for lower research depths
            research_results["executive_summary"] = self._generate_basic_summary(research_results)
        
        # Cache the results
        await self.cache_manager.set(cache_key, research_results)
        
        # Save to database if property_id is provided
        if property_id:
            try:
                await self.db_ops.save_research_results(property_id, research_results)
                logger.info(f"Saved research results for property {property_id}")
            except Exception as e:
                logger.error(f"Error saving research results to database: {e}")
        
        return research_results
    
    async def batch_research_properties(self, properties: List[Dict[str, Any]], 
                                       research_depth: str = "standard",
                                       concurrency: int = 3,
                                       force_refresh: bool = False,
                                       on_progress: Optional[Callable[[int, int, Dict[str, Any]], None]] = None) -> Dict[str, Any]:
        """
        Research multiple properties concurrently.
        
        Args:
            properties: List of property details
            research_depth: Depth of research
            concurrency: Maximum number of concurrent research operations
            force_refresh: Force refresh of cached data
            on_progress: Optional callback function to report progress (completed, total, latest_result)
            
        Returns:
            Dictionary mapping property_id/address to research results
        """
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        total = len(properties)
        completed = 0
        batch_results = {}
        
        # Add jitter to avoid API rate limit issues on external services
        async def research_with_semaphore(property_data, index):
            nonlocal completed
            
            # Add small random delay to avoid thundering herd problem
            if index > 0:
                await asyncio.sleep(random.uniform(0.1, 0.5))
                
            try:
                async with semaphore:
                    # Implement exponential backoff for retries
                    max_retries = 3
                    retry_delay = 1.0
                    
                    for attempt in range(max_retries):
                        try:
                            result = await self.research_property(
                                property_data=property_data, 
                                research_depth=research_depth,
                                force_refresh=force_refresh
                            )
                            
                            # Update progress
                            completed += 1
                            if on_progress:
                                await on_progress(completed, total, result)
                                
                            return result
                        except Exception as e:
                            if attempt < max_retries - 1:
                                # Log retry attempt
                                logger.warning(
                                    f"Attempt {attempt+1}/{max_retries} failed for property "
                                    f"{property_data.get('id', property_data.get('address', 'unknown'))}: {e}"
                                )
                                # Wait with exponential backoff before retry
                                await asyncio.sleep(retry_delay * (2 ** attempt))
                            else:
                                # Last attempt failed, raise the exception
                                raise
            except Exception as e:
                # Update progress even on error
                completed += 1
                if on_progress:
                    error_result = {"error": str(e)}
                    await on_progress(completed, total, error_result)
                raise e
                
        # Create tasks for all properties with index
        tasks = [research_with_semaphore(prop, i) for i, prop in enumerate(properties)]
        
        # Execute tasks and collect results with proper exception handling
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(results):
            property_data = properties[i]
            property_id = property_data.get("id") or property_data.get("property_id")
            address = property_data.get("address", "")
            
            # Use property_id if available, otherwise use address as key
            key = property_id if property_id else address
            
            if isinstance(result, Exception):
                logger.error(f"Error researching property {key}: {result}")
                batch_results[key] = {"error": str(result), "timestamp": datetime.now().isoformat()}
            else:
                batch_results[key] = result
        
        # Batch save to database with retry logic
        try:
            property_ids_with_results = [
                (prop.get("id") or prop.get("property_id"), batch_results[prop.get("id") or prop.get("property_id")])
                for prop in properties
                if (prop.get("id") or prop.get("property_id")) and 
                   (prop.get("id") or prop.get("property_id")) in batch_results and
                   "error" not in batch_results[prop.get("id") or prop.get("property_id")]
            ]
            
            if property_ids_with_results:
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        await self.db_ops.batch_save_research_results(property_ids_with_results)
                        logger.info(f"Batch saved {len(property_ids_with_results)} research results")
                        break
                    except Exception as e:
                        if attempt < max_retries - 1:
                            logger.warning(f"Database batch save attempt {attempt+1}/{max_retries} failed: {e}")
                            await asyncio.sleep(1 * (2 ** attempt))  # Exponential backoff
                        else:
                            logger.error(f"All database batch save attempts failed: {e}")
                            raise
        except Exception as e:
            logger.error(f"Error batch saving research results: {e}")
        
        # Return a dictionary with statistics
        success_count = sum(1 for result in batch_results.values() if "error" not in result)
        
        return {
            "results": batch_results,
            "stats": {
                "total": total,
                "success": success_count,
                "errors": total - success_count,
                "success_rate": f"{(success_count / total * 100):.1f}%" if total > 0 else "0%"
            }
        }
    
    async def _research_property_details(self, property_data: Dict[str, Any], 
                                       research_depth: str) -> Dict[str, Any]:
        """Research detailed property information."""
        try:
            logger.info(f"Researching property details for {property_data.get('address')}")
            
            # Use the PropertyProfiler enricher
            property_details = await self.property_profiler.profile_property(
                property_data=property_data,
                depth=research_depth
            )
            
            return {"property_details": property_details}
        except Exception as e:
            logger.error(f"Error researching property details: {e}")
            return {"property_details": {"error": str(e)}}
    
    async def _research_investment_potential(self, property_data: Dict[str, Any], 
                                           research_depth: str) -> Dict[str, Any]:
        """Research investment potential and metrics."""
        try:
            logger.info(f"Researching investment potential for {property_data.get('address')}")
            
            # Use the InvestmentMetricsEnricher
            investment_metrics = await self.investment_metrics.calculate_metrics(
                property_data=property_data
            )
            
            return {"investment_potential": investment_metrics}
        except Exception as e:
            logger.error(f"Error researching investment potential: {e}")
            return {"investment_potential": {"error": str(e)}}
    
    async def _research_market_conditions(self, property_data: Dict[str, Any], 
                                        research_depth: str) -> Dict[str, Any]:
        """Research market conditions and trends."""
        try:
            logger.info(f"Researching market conditions for {property_data.get('address')}")
            
            # Use our new MarketAnalyzer
            market_analysis = await self.market_analyzer.analyze_market(
                property_data=property_data,
                depth=research_depth
            )
            
            return {"market_conditions": market_analysis}
        except Exception as e:
            logger.error(f"Error researching market conditions: {e}")
            return {"market_conditions": {"error": str(e)}}
    
    async def _research_risk_assessment(self, property_data: Dict[str, Any], 
                                      research_depth: str) -> Dict[str, Any]:
        """Research risks and blindspots."""
        try:
            logger.info(f"Researching risks for {property_data.get('address')}")
            
            # Collect data from other modules for context
            additional_data = {}
            
            # Use our new RiskAssessor
            risk_assessment = await self.risk_assessor.assess_risks(
                property_data=property_data,
                additional_data=additional_data,
                depth=research_depth
            )
            
            # For comprehensive and exhaustive research, also get insurance requirements
            if research_depth in ["comprehensive", "exhaustive"]:
                insurance_requirements = await self.risk_assessor.assess_insurance_requirements(
                    property_data=property_data,
                    risk_assessment=risk_assessment
                )
                risk_assessment.update(insurance_requirements)
                
                # Add risk vs. reward analysis
                investment_module = await self._research_investment_potential(property_data, research_depth)
                investment_metrics = investment_module.get("investment_potential", {})
                
                risk_reward = await self.risk_assessor.analyze_investment_risk_vs_reward(
                    property_data=property_data,
                    risk_assessment=risk_assessment,
                    investment_metrics=investment_metrics
                )
                risk_assessment.update(risk_reward)
            
            return {"risk_assessment": risk_assessment}
        except Exception as e:
            logger.error(f"Error researching risks: {e}")
            return {"risk_assessment": {"error": str(e)}}
    
    async def geocode_property(self, property_data: Dict[str, Any], force_refresh: bool = False) -> Dict[str, Any]:
        """
        Geocode a property to obtain latitude and longitude coordinates.
        
        Args:
            property_data: Property details dictionary
            force_refresh: Force refresh of existing coordinates
            
        Returns:
            Updated property dictionary with geocoded coordinates
        """
        # Create a copy to avoid modifying the original
        updated_property = property_data.copy()
        
        # Check if we already have valid coordinates and not forcing refresh
        if not force_refresh and self._has_valid_coordinates(updated_property):
            logger.info(f"Property already has valid coordinates: {updated_property.get('address')}")
            return updated_property
            
        # Get address components
        address = updated_property.get("address", "")
        city = updated_property.get("city", "")
        state = updated_property.get("state", "")
        zip_code = updated_property.get("zip_code", "")
        
        # Verify we have minimum required data for geocoding
        if not address or not (city or state):
            logger.warning(f"Insufficient address data for geocoding: {address}, {city}, {state}")
            return updated_property
            
        try:
            # Create cache key for this geocoding operation
            property_id = updated_property.get("id", "")
            cache_key = f"geocode:{property_id or ''}:{address}:{city}:{state}"
            
            # Check cache first unless force refresh is requested
            if not force_refresh:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Using cached geocoding for {address}, {city}, {state}")
                    
                    # Update property with cached coordinates
                    updated_property["latitude"] = cached_result.get("latitude")
                    updated_property["longitude"] = cached_result.get("longitude")
                    
                    if "formatted_address" in cached_result:
                        updated_property["formatted_address"] = cached_result.get("formatted_address")
                        
                    return updated_property
                    
            # Use geocoding service to get coordinates
            geocode_result = await self.geocoding_service.geocode_address(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code
            )
            
            # Update property with geocoded data
            updated_property["latitude"] = geocode_result.get("latitude")
            updated_property["longitude"] = geocode_result.get("longitude")
            
            if "formatted_address" in geocode_result:
                updated_property["formatted_address"] = geocode_result.get("formatted_address")
                
            # Cache the geocoding result
            await self.cache_manager.set(cache_key, geocode_result)
            
            logger.info(f"Successfully geocoded property: {address}, {city}, {state}")
            
            # If this property has an ID, update the database with new coordinates
            if property_id and self.db_ops and self._has_valid_coordinates(updated_property):
                try:
                    # Prepare minimal update with just coordinates
                    coord_update = {
                        "id": property_id,
                        "latitude": updated_property["latitude"],
                        "longitude": updated_property["longitude"],
                        "updated_at": datetime.now().isoformat()
                    }
                    
                    if "formatted_address" in updated_property:
                        coord_update["formatted_address"] = updated_property["formatted_address"]
                        
                    # Update database
                    await self.db_ops._update_property_with_enriched_data(property_id, {"modules": {"property_details": coord_update}})
                    logger.info(f"Updated database with geocoded coordinates for property {property_id}")
                except Exception as e:
                    logger.error(f"Error updating database with coordinates: {e}")
            
        except Exception as e:
            logger.error(f"Error geocoding property {address}, {city}, {state}: {e}")
            
        return updated_property
        
    async def batch_geocode_properties(self, 
                                    properties: List[Dict[str, Any]], 
                                    concurrency: int = 3,
                                    force_refresh: bool = False) -> Dict[str, Any]:
        """
        Geocode multiple properties concurrently.
        
        Args:
            properties: List of property dictionaries
            concurrency: Maximum number of concurrent geocoding operations
            force_refresh: Force refresh of existing coordinates
            
        Returns:
            Dictionary with geocoding results and statistics
        """
        # Use the geocoding service's batch functionality
        batch_results = await self.geocoding_service.batch_geocode(
            properties=properties,
            concurrency=concurrency,
            use_cache=not force_refresh
        )
        
        # Update properties with geocoded coordinates
        updated_properties = []
        
        for prop in properties:
            property_id = prop.get("id", "")
            
            if property_id in batch_results["results"]:
                # Create a copy of the property
                updated_prop = prop.copy()
                
                # Get geocoding result
                geocode_result = batch_results["results"][property_id]
                
                # Update property with coordinates if no error
                if "error" not in geocode_result:
                    updated_prop["latitude"] = geocode_result.get("latitude")
                    updated_prop["longitude"] = geocode_result.get("longitude")
                    
                    if "formatted_address" in geocode_result:
                        updated_prop["formatted_address"] = geocode_result.get("formatted_address")
                
                updated_properties.append(updated_prop)
            else:
                # If no result found, include original property
                updated_properties.append(prop)
        
        # Return the updated properties and geocoding statistics
        return {
            "properties": updated_properties,
            "stats": batch_results["stats"]
        }
    
    def _has_valid_coordinates(self, property_data: Dict[str, Any]) -> bool:
        """Check if property has valid latitude and longitude coordinates."""
        latitude = property_data.get("latitude")
        longitude = property_data.get("longitude")
        
        # Check if coordinates exist and are within valid ranges
        if latitude is not None and longitude is not None:
            try:
                lat_value = float(latitude)
                lng_value = float(longitude)
                
                return (-90 <= lat_value <= 90) and (-180 <= lng_value <= 180)
            except (ValueError, TypeError):
                return False
                
        return False
        
    def _validate_property_data(self, property_data: Dict[str, Any]) -> bool:
        """Validate that property data contains required fields."""
        # We only require one of the fields to validate since we're working with real data
        # that might be partially complete
        required_fields = ["address", "city", "state", "name"]
        return any(field in property_data and property_data[field] for field in required_fields)
    
    def _generate_basic_summary(self, research_results: Dict[str, Any]) -> str:
        """Generate a basic executive summary when MCP is not available."""
        try:
            # Extract property information
            address = research_results.get("property_address", "")
            city = research_results.get("city", "")
            state = research_results.get("state", "")
            modules = research_results.get("modules", {})
            
            # Extract relevant data from modules
            property_details = modules.get("property_details", {})
            investment = modules.get("investment_potential", {})
            market = modules.get("market_conditions", {})
            risk = modules.get("risk_assessment", {})
            
            # Basic property information
            summary = f"Property Research Summary for {address}, {city}, {state}\n\n"
            
            # Property details
            if "error" not in property_details:
                prop_type = property_details.get("property_type", "")
                units = property_details.get("units")
                year_built = property_details.get("year_built")
                
                summary += "Property Profile: "
                if prop_type:
                    summary += f"{prop_type.capitalize()} property"
                if units:
                    summary += f" with {units} units"
                if year_built:
                    summary += f", built in {year_built}"
                summary += ".\n"
            
            # Investment potential
            if "error" not in investment:
                cap_rate = investment.get("cap_rate")
                projected_irr = investment.get("projected_irr")
                
                if cap_rate:
                    summary += f"Investment Profile: Cap rate of {cap_rate}%, "
                if projected_irr:
                    summary += f"with projected IRR of {projected_irr}%. "
                summary += "\n"
            
            # Market conditions
            if "error" not in market and market.get("executive_summary"):
                summary += f"Market Analysis: {market.get('executive_summary')}\n"
            
            # Risk assessment
            if "error" not in risk and risk.get("executive_summary"):
                summary += f"Risk Assessment: {risk.get('executive_summary')}\n"
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating basic summary: {e}")
            return f"Research completed for property at {address}, {city}, {state}. See detailed modules for specific findings."
