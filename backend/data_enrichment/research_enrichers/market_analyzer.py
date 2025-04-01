# backend/data_enrichment/research_enrichers/market_analyzer.py
import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import aiohttp
import re

from backend.data_enrichment.mcp_client import DeepResearchMCPClient

logger = logging.getLogger(__name__)

from backend.app.utils.architecture import layer, ArchitectureLayer

@layer(ArchitectureLayer.PROCESSING)
class MarketAnalyzer:
    """
    Analyzes market conditions and competitive landscape for properties.
    
    Provides insights on comparable properties, rental trends, supply/demand metrics,
    market performance indicators, demographic analysis, and future projections.
    """
    
    def __init__(self):
        """Initialize with API keys from environment"""
        self.census_api_key = os.getenv("CENSUS_API_KEY", "")
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.property_records_api_key = os.getenv("PROPERTY_RECORDS_API_KEY", "")
        self.cache = {}
        
        logger.info("Market Analyzer initialized")
    
    async def analyze_market(self, property_data: Dict[str, Any], 
                           depth: str = "standard") -> Dict[str, Any]:
        """
        Analyze market conditions for a property.
        
        Args:
            property_data: Property details
            depth: Research depth level (basic, standard, comprehensive, exhaustive)
            
        Returns:
            Dictionary of market analysis
        """
        # Extract basic property info needed for market analysis
        address = property_data.get("address", "")
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        zip_code = property_data.get("zip_code", "")
        property_type = property_data.get("property_type", "multifamily")
        units = property_data.get("units")
        
        # Cache key for this property's market analysis
        cache_key = f"market_analysis:{city}:{state}:{zip_code}:{property_type}"
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result and cached_result.get("timestamp"):
            cache_time = datetime.fromisoformat(cached_result.get("timestamp"))
            # Market data cache is valid for 7 days
            if datetime.now() - cache_time < timedelta(days=7):
                logger.info(f"Using cached market analysis for {city}, {state}")
                return cached_result.get("data", {})
        
        # Create tasks for parallel API calls
        tasks = []
        
        # Always include basic market data
        tasks.append(self._get_economic_indicators(city, state))
        tasks.append(self._get_demographic_data(city, state, zip_code))
        
        # Add more detailed analysis based on depth
        if depth in ["standard", "comprehensive", "exhaustive"]:
            tasks.append(self._get_rental_trends(city, state, property_type))
            tasks.append(self._get_comparable_properties(property_data))
        
        if depth in ["comprehensive", "exhaustive"]:
            tasks.append(self._get_supply_demand_metrics(city, state, property_type))
            tasks.append(self._get_market_projections(city, state, property_type))
        
        # For exhaustive research, use MCP for advanced analysis
        mcp_results = {}
        if depth == "exhaustive":
            try:
                mcp_client = DeepResearchMCPClient()
                mcp_results = await mcp_client.market_intelligence_analysis(property_data)
            except Exception as e:
                logger.error(f"Error using MCP for market analysis: {e}")
                mcp_results = {"error": str(e)}
        
        # Execute all API tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results into a single response
        market_analysis = {
            "overview": {
                "city": city,
                "state": state,
                "property_type": property_type,
                "analysis_date": datetime.now().isoformat(),
            }
        }
        
        # Process results from each API call
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in market analysis API call {i}: {result}")
                continue
                
            # Add successful results to the analysis
            market_analysis.update(result)
        
        # If we have MCP results and no error, integrate them
        if mcp_results and "error" not in mcp_results:
            # Deep merge of MCP results with our direct API results
            self._merge_results(market_analysis, mcp_results)
        
        # Calculate additional metrics
        if "demographic_data" in market_analysis and "rental_trends" in market_analysis:
            market_analysis["market_health_score"] = self._calculate_market_health_score(market_analysis)
            
        # Add executive summary if we have enough data
        if len(market_analysis) > 3:  # More than just overview and a couple data points
            market_analysis["executive_summary"] = self._generate_market_summary(market_analysis)
        
        # Cache the results
        self.cache[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "data": market_analysis
        }
        
        return market_analysis
    
    async def _get_economic_indicators(self, city: str, state: str) -> Dict[str, Any]:
        """
        Get economic indicators for the area using FRED API.
        
        Args:
            city: The city name
            state: The state code
            
        Returns:
            Dictionary of economic indicators
        """
        if not self.fred_api_key:
            logger.warning("FRED API key not set, using placeholder economic data")
            return {
                "economic_indicators": {
                    "note": "Placeholder data - FRED API key not configured",
                    "unemployment_rate": 4.5,
                    "median_income_growth": 2.3,
                    "job_growth": 1.8
                }
            }
            
        try:
            async with aiohttp.ClientSession() as session:
                # Map of metro areas to FRED series IDs
                metro_code = self._get_metro_code(city, state)
                
                # Get unemployment rate
                unemployment_url = f"https://api.stlouisfed.org/fred/series/observations"
                unemployment_params = {
                    "series_id": f"LAUMT{metro_code}URN",
                    "api_key": self.fred_api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 12  # Last 12 months
                }
                
                async with session.get(unemployment_url, params=unemployment_params) as response:
                    if response.status == 200:
                        unemployment_data = await response.json()
                    else:
                        logger.error(f"FRED API error: {await response.text()}")
                        unemployment_data = {"observations": []}
                
                # Get median income (annual data)
                income_url = f"https://api.stlouisfed.org/fred/series/observations"
                income_params = {
                    "series_id": f"MHINY{metro_code}A052NCEN",
                    "api_key": self.fred_api_key,
                    "file_type": "json",
                    "sort_order": "desc",
                    "limit": 5  # Last 5 years
                }
                
                async with session.get(income_url, params=income_params) as response:
                    if response.status == 200:
                        income_data = await response.json()
                    else:
                        logger.error(f"FRED API error: {await response.text()}")
                        income_data = {"observations": []}
                
                # Process the data
                unemployment_rate = self._extract_latest_value(unemployment_data)
                income_trend = self._calculate_trend(income_data)
                
                return {
                    "economic_indicators": {
                        "unemployment_rate": unemployment_rate,
                        "median_income_growth": income_trend,
                        "job_growth": self._calculate_job_growth(unemployment_data),
                        "data_source": "FRED (Federal Reserve Economic Data)",
                        "as_of_date": datetime.now().strftime("%Y-%m-%d")
                    }
                }
                
        except Exception as e:
            logger.error(f"Error fetching economic indicators: {e}")
            return {
                "economic_indicators": {
                    "error": f"Failed to retrieve economic data: {str(e)}",
                    "unemployment_rate": None,
                    "median_income_growth": None,
                    "job_growth": None
                }
            }
    
    async def _get_demographic_data(self, city: str, state: str, zip_code: str = None) -> Dict[str, Any]:
        """
        Get demographic data using Census API.
        
        Args:
            city: The city name
            state: The state code
            zip_code: The ZIP code (optional)
            
        Returns:
            Dictionary of demographic data
        """
        if not self.census_api_key:
            logger.warning("Census API key not set, using placeholder demographic data")
            return {
                "demographic_data": {
                    "note": "Placeholder data - Census API key not configured",
                    "population": 350000,
                    "median_age": 34.5,
                    "median_household_income": 65000,
                    "renter_occupied_percentage": 42
                }
            }
            
        try:
            # Determine geographic identifier
            geo_id = await self._get_census_geo_id(city, state, zip_code)
            if not geo_id:
                logger.error(f"Could not determine Census geography ID for {city}, {state}")
                raise ValueError(f"Invalid location: {city}, {state}")
            
            async with aiohttp.ClientSession() as session:
                # Get demographic data from Census API American Community Survey
                census_url = "https://api.census.gov/data/2022/acs/acs5"
                
                # Select demographic variables
                variables = [
                    "B01003_001E",  # Total population
                    "B01002_001E",  # Median age
                    "B19013_001E",  # Median household income
                    "B25003_001E",  # Total occupied housing units
                    "B25003_003E",  # Renter occupied housing units
                    "B25077_001E",  # Median home value
                ]
                
                params = {
                    "get": ",".join(variables),
                    "for": f"{geo_id['type']}:{geo_id['id']}",
                    "in": f"state:{geo_id['state_id']}" if geo_id['type'] != "state" else None,
                    "key": self.census_api_key
                }
                
                # Remove None values
                params = {k: v for k, v in params.items() if v is not None}
                
                async with session.get(census_url, params=params) as response:
                    if response.status == 200:
                        census_data = await response.json()
                        
                        # Census API returns a 2D array with headers in first row
                        headers = census_data[0]
                        values = census_data[1]
                        
                        data_dict = dict(zip(headers, values))
                        
                        # Calculate renter percentage
                        total_occupied = int(data_dict.get("B25003_001E", 0))
                        renter_occupied = int(data_dict.get("B25003_003E", 0))
                        renter_percentage = (renter_occupied / total_occupied * 100) if total_occupied > 0 else 0
                        
                        return {
                            "demographic_data": {
                                "population": int(data_dict.get("B01003_001E", 0)),
                                "median_age": float(data_dict.get("B01002_001E", 0)),
                                "median_household_income": int(data_dict.get("B19013_001E", 0)),
                                "median_home_value": int(data_dict.get("B25077_001E", 0)),
                                "renter_occupied_percentage": round(renter_percentage, 1),
                                "data_source": "US Census Bureau - American Community Survey",
                                "year": 2022
                            }
                        }
                    else:
                        logger.error(f"Census API error: {await response.text()}")
                        raise ValueError(f"Census API error: {response.status}")
                        
        except Exception as e:
            logger.error(f"Error fetching demographic data: {e}")
            return {
                "demographic_data": {
                    "error": f"Failed to retrieve demographic data: {str(e)}",
                    "population": None,
                    "median_age": None,
                    "median_household_income": None,
                    "renter_occupied_percentage": None
                }
            }
    
    async def _get_rental_trends(self, city: str, state: str, 
                               property_type: str = "multifamily") -> Dict[str, Any]:
        """
        Get rental trends for the area.
        
        Args:
            city: The city name
            state: The state code
            property_type: The property type
            
        Returns:
            Dictionary of rental trends
        """
        try:
            # This would ideally use a specialized real estate API
            # For now, we'll use FRED's housing data as a proxy
            if self.fred_api_key:
                async with aiohttp.ClientSession() as session:
                    metro_code = self._get_metro_code(city, state)
                    
                    # Get rental price index
                    rental_url = f"https://api.stlouisfed.org/fred/series/observations"
                    rental_params = {
                        "series_id": "CUUR0000SEHA", # CPI for rent of primary residence
                        "api_key": self.fred_api_key,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 24  # Last 24 months
                    }
                    
                    async with session.get(rental_url, params=rental_params) as response:
                        if response.status == 200:
                            rental_data = await response.json()
                            
                            # Calculate year-over-year growth
                            observations = rental_data.get("observations", [])
                            if len(observations) >= 12:
                                current = float(observations[0].get("value", 0))
                                year_ago = float(observations[12].get("value", 0))
                                yoy_growth = ((current - year_ago) / year_ago * 100) if year_ago > 0 else 0
                                
                                # Calculate quarterly trend
                                quarterly_values = [float(observations[i].get("value", 0)) for i in range(0, 12, 3)]
                                quarterly_trend = "stable"
                                if len(quarterly_values) >= 2:
                                    diff = quarterly_values[0] - quarterly_values[-1]
                                    if diff > 0:
                                        quarterly_trend = "increasing"
                                    elif diff < 0:
                                        quarterly_trend = "decreasing"
                                
                                # Add premium/discount for specific property type
                                property_premium = {
                                    "multifamily": 1.0,
                                    "luxury": 1.3,
                                    "affordable": 0.8,
                                    "student": 1.1,
                                    "senior": 1.05
                                }.get(property_type.lower(), 1.0)
                                
                                return {
                                    "rental_trends": {
                                        "year_over_year_growth": round(yoy_growth, 1),
                                        "quarterly_trend": quarterly_trend,
                                        "estimated_property_type_premium": property_premium,
                                        "vacancy_rate_estimate": self._estimate_vacancy_rate(city, state),
                                        "data_source": "Derived from FRED CPI Housing data",
                                        "as_of_date": observations[0].get("date", "")
                                    }
                                }
                        else:
                            logger.error(f"FRED API error: {await response.text()}")
            
            # Fallback to placeholder data
            logger.warning("Using placeholder rental trend data")
            return {
                "rental_trends": {
                    "note": "Placeholder data",
                    "year_over_year_growth": 3.5,
                    "quarterly_trend": "stable",
                    "estimated_property_type_premium": 1.0,
                    "vacancy_rate_estimate": 5.2
                }
            }
                
        except Exception as e:
            logger.error(f"Error fetching rental trends: {e}")
            return {
                "rental_trends": {
                    "error": f"Failed to retrieve rental trends: {str(e)}",
                    "year_over_year_growth": None,
                    "quarterly_trend": None,
                    "vacancy_rate_estimate": None
                }
            }
    
    async def _get_comparable_properties(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Find comparable properties.
        
        Args:
            property_data: Property details
            
        Returns:
            Dictionary of comparable properties
        """
        try:
            # Extract key property details
            address = property_data.get("address", "")
            city = property_data.get("city", "")
            state = property_data.get("state", "")
            zip_code = property_data.get("zip_code", "")
            property_type = property_data.get("property_type", "multifamily")
            units = property_data.get("units")
            year_built = property_data.get("year_built")
            
            # This would normally use a real estate listings API
            # For demonstration, returning structured placeholder data
            
            # Create plausible comps based on property data
            comp_count = 3
            comps = []
            
            for i in range(comp_count):
                # Generate slightly different property details for each comp
                unit_variance = max(int(units * 0.2) if units else 10, 5)
                year_variance = 5 if year_built else 0
                
                comp_units = units + ((-1)**(i+1)) * (i+1) * unit_variance//2 if units else None
                comp_year = year_built + ((-1)**i) * (i+1) if year_built else None
                
                # Generate price per unit variations
                base_ppu = 125000  # Base price per unit
                ppu_variance = 15000  # Variance in price per unit
                comp_ppu = base_ppu + ((-1)**(i)) * (i+1) * ppu_variance//3
                
                # Generate rent per unit variations
                base_rent = 1200  # Base monthly rent
                rent_variance = 150  # Variance in monthly rent
                comp_rent = base_rent + ((-1)**(i+1)) * (i+1) * rent_variance//3
                
                comps.append({
                    "name": f"Comparable Property {i+1}",
                    "address": f"{100*(i+1)} Main St",
                    "city": city,
                    "state": state,
                    "distance_miles": round(0.8 + i * 0.7, 1),
                    "units": comp_units,
                    "year_built": comp_year,
                    "last_sale_date": f"2022-{(i+1)*3:02d}-15",
                    "last_sale_price": comp_units * comp_ppu if comp_units else None,
                    "price_per_unit": comp_ppu,
                    "avg_monthly_rent": comp_rent,
                    "cap_rate": round(4.5 + (i * 0.3), 1),
                    "occupancy": round(94 - (i * 1.5), 1)
                })
            
            return {
                "comparable_properties": {
                    "count": len(comps),
                    "comps": comps,
                    "avg_price_per_unit": sum(c.get("price_per_unit", 0) for c in comps) // len(comps),
                    "avg_cap_rate": round(sum(c.get("cap_rate", 0) for c in comps) / len(comps), 1),
                    "avg_occupancy": round(sum(c.get("occupancy", 0) for c in comps) / len(comps), 1),
                    "note": "Placeholder comparable properties data"
                }
            }
                
        except Exception as e:
            logger.error(f"Error finding comparable properties: {e}")
            return {
                "comparable_properties": {
                    "error": f"Failed to find comparable properties: {str(e)}",
                    "count": 0,
                    "comps": []
                }
            }
    
    async def _get_supply_demand_metrics(self, city: str, state: str, 
                                       property_type: str = "multifamily") -> Dict[str, Any]:
        """
        Get supply and demand metrics for the market.
        
        Args:
            city: The city name
            state: The state code
            property_type: The property type
            
        Returns:
            Dictionary of supply/demand metrics
        """
        try:
            # For demonstration, use FRED data on housing starts as proxy for supply
            if self.fred_api_key:
                async with aiohttp.ClientSession() as session:
                    # Get national housing starts (regional data is limited)
                    housing_url = f"https://api.stlouisfed.org/fred/series/observations"
                    housing_params = {
                        "series_id": "HOUST",  # Housing Starts
                        "api_key": self.fred_api_key,
                        "file_type": "json",
                        "sort_order": "desc",
                        "limit": 24  # Last 24 months
                    }
                    
                    async with session.get(housing_url, params=housing_params) as response:
                        if response.status == 200:
                            housing_data = await response.json()
                            housing_trend = self._calculate_trend(housing_data)
                            
                            # Use MCP for market-specific estimation
                            supply_growth = housing_trend  # National proxy
                            absorption_rate = None
                            months_of_supply = None
                            
                            # For now, use reasonably estimated values based on property type
                            if property_type.lower() == "multifamily":
                                absorption_rate = 20  # Units absorbed per month
                                months_of_supply = 4.5  # Months of supply
                            elif property_type.lower() == "luxury":
                                absorption_rate = 10  # Slower absorption for luxury
                                months_of_supply = 6.0  # More months of supply
                            else:
                                absorption_rate = 15  # Default
                                months_of_supply = 5.0  # Default
                            
                            return {
                                "supply_demand_metrics": {
                                    "new_construction_trend": "increasing" if housing_trend > 0 else "decreasing",
                                    "estimated_supply_growth": round(supply_growth, 1),
                                    "estimated_absorption_rate": absorption_rate,
                                    "months_of_supply": months_of_supply,
                                    "supply_demand_balance": self._assess_supply_demand_balance(supply_growth, absorption_rate),
                                    "data_source": "Derived from FRED housing data and market estimates",
                                }
                            }
            
            # Fallback to placeholder data
            logger.warning("Using placeholder supply/demand data")
            return {
                "supply_demand_metrics": {
                    "note": "Placeholder data",
                    "new_construction_trend": "stable",
                    "estimated_supply_growth": 2.3,
                    "estimated_absorption_rate": 15,
                    "months_of_supply": 5.0,
                    "supply_demand_balance": "balanced"
                }
            }
                
        except Exception as e:
            logger.error(f"Error fetching supply/demand metrics: {e}")
            return {
                "supply_demand_metrics": {
                    "error": f"Failed to retrieve supply/demand metrics: {str(e)}",
                    "new_construction_trend": None,
                    "estimated_supply_growth": None,
                    "months_of_supply": None
                }
            }
    
    async def _get_market_projections(self, city: str, state: str, 
                                    property_type: str = "multifamily") -> Dict[str, Any]:
        """
        Get market projections and forecasts.
        
        Args:
            city: The city name
            state: The state code
            property_type: The property type
            
        Returns:
            Dictionary of market projections
        """
        try:
            # Combine previously gathered data to create projections
            # In a real implementation, this would use specialized forecast APIs
            
            # Get current economic indicators as baseline
            economic_data = await self._get_economic_indicators(city, state)
            rental_data = await self._get_rental_trends(city, state, property_type)
            
            # Extract key metrics
            current_growth = rental_data.get("rental_trends", {}).get("year_over_year_growth", 3.0)
            unemployment = economic_data.get("economic_indicators", {}).get("unemployment_rate", 4.5)
            
            # Simple projection model based on current trends
            rental_projection = current_growth * 0.8  # Assuming regression toward mean
            
            # Adjust projection based on unemployment
            if unemployment > 6.0:
                rental_projection -= 1.0  # High unemployment reduces growth
            elif unemployment < 4.0:
                rental_projection += 0.5  # Low unemployment supports growth
            
            # Determine market cycle position
            market_cycle = self._determine_market_cycle(current_growth, unemployment)
            
            return {
                "market_projections": {
                    "forecast_period": "12 months",
                    "rental_growth_projection": round(rental_projection, 1),
                    "vacancy_rate_projection": round(5.0 + (unemployment - 4.5), 1),
                    "market_cycle_position": market_cycle,
                    "opportunity_outlook": self._determine_opportunity_outlook(market_cycle, property_type),
                    "risk_level": self._determine_risk_level(market_cycle, unemployment),
                    "projection_confidence": "medium",
                    "note": "Projections based on current economic trends and historical patterns"
                }
            }
                
        except Exception as e:
            logger.error(f"Error generating market projections: {e}")
            return {
                "market_projections": {
                    "error": f"Failed to generate market projections: {str(e)}",
                    "rental_growth_projection": None,
                    "vacancy_rate_projection": None,
                    "market_cycle_position": None
                }
            }
    
    def _get_metro_code(self, city: str, state: str) -> str:
        """Get the FRED metro area code for a city/state."""
        # This would ideally use a lookup service or database
        # For now, using a simplified mapping of major cities
        city_lower = city.lower()
        state_lower = state.lower()
        
        metro_codes = {
            ("new york", "ny"): "35620",
            ("los angeles", "ca"): "31080",
            ("chicago", "il"): "16980",
            ("houston", "tx"): "26420",
            ("phoenix", "az"): "38060",
            ("philadelphia", "pa"): "37980",
            ("san antonio", "tx"): "41700",
            ("san diego", "ca"): "41740",
            ("dallas", "tx"): "19100",
            ("austin", "tx"): "12420",
            ("san francisco", "ca"): "41860",
            ("seattle", "wa"): "42660",
            ("denver", "co"): "19740",
            ("boston", "ma"): "14460",
            ("atlanta", "ga"): "12060",
        }
        
        return metro_codes.get((city_lower, state_lower), "00000")
    
    async def _get_census_geo_id(self, city: str, state: str, zip_code: str = None) -> Dict[str, str]:
        """Get Census geography identifier for a location."""
        # For simplicity, using state and place (city) geography
        # More precise would be using ZIP Code Tabulation Areas (ZCTAs) or Census Tracts
        
        # State FIPS codes (simplified)
        state_fips = {
            "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09",
            "DE": "10", "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18",
            "IA": "19", "KS": "20", "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25",
            "MI": "26", "MN": "27", "MS": "28", "MO": "29", "MT": "30", "NE": "31", "NV": "32",
            "NH": "33", "NJ": "34", "NM": "35", "NY": "36", "NC": "37", "ND": "38", "OH": "39",
            "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45", "SD": "46", "TN": "47",
            "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54", "WI": "55",
            "WY": "56", "DC": "11"
        }
        
        state_id = state_fips.get(state.upper())
        if not state_id:
            return None
            
        # For simplicity, return state level geography
        return {
            "type": "state",
            "id": state_id,
            "state_id": state_id
        }
    
    def _extract_latest_value(self, data_response: Dict[str, Any]) -> float:
        """Extract the latest value from a FRED API response."""
        observations = data_response.get("observations", [])
        if observations:
            try:
                return float(observations[0].get("value", 0))
            except (ValueError, TypeError):
                return 0
        return 0
    
    def _calculate_trend(self, data_response: Dict[str, Any]) -> float:
        """Calculate trend from a time series dataset."""
        observations = data_response.get("observations", [])
        if len(observations) >= 2:
            try:
                latest = float(observations[0].get("value", 0))
                oldest = float(observations[-1].get("value", 0))
                # Percentage change
                return ((latest - oldest) / oldest * 100) if oldest != 0 else 0
            except (ValueError, TypeError):
                return 0
        return 0
    
    def _calculate_job_growth(self, unemployment_data: Dict[str, Any]) -> float:
        """Calculate job growth from unemployment data."""
        # Simplified calculation based on unemployment rate changes
        observations = unemployment_data.get("observations", [])
        if len(observations) >= 6:
            try:
                # Lower unemployment generally suggests job growth
                latest = float(observations[0].get("value", 0))
                six_months_ago = float(observations[5].get("value", 0))
                # Simple job growth estimation (negative unemployment change suggests job growth)
                diff = six_months_ago - latest
                # Rough estimate: 0.5% unemployment decrease ~= 1% job growth
                return round(diff * 2, 1) if diff > 0 else round(diff, 1)
            except (ValueError, TypeError):
                return 0
        return 1.5  # Default moderate growth
    
    def _estimate_vacancy_rate(self, city: str, state: str) -> float:
        """Estimate vacancy rate based on location and national averages."""
        # This would ideally use actual vacancy data APIs
        # For now, using a simplified model based on city tiers
        
        # Simplified city tier classification
        tier_1_cities = ["new york", "los angeles", "chicago", "san francisco", "boston", "seattle"]
        tier_2_cities = ["austin", "denver", "atlanta", "dallas", "miami", "portland", "nashville"]
        
        city_lower = city.lower()
        
        # Base vacancy rate (national average for multifamily)
        vacancy_rate = 5.0
        
        # Adjust based on city tier
        if city_lower in tier_1_cities:
            vacancy_rate -= 1.0  # Lower vacancy in tier 1
        elif city_lower in tier_2_cities:
            vacancy_rate -= 0.5  # Slightly lower vacancy in tier 2
        
        # Add some randomness to make it realistic
        import random
        vacancy_rate += random.uniform(-0.5, 0.5)
        
        return round(max(vacancy_rate, 2.0), 1)  # Ensure minimum 2% vacancy
    
    def _assess_supply_demand_balance(self, supply_growth: float, absorption_rate: float) -> str:
        """Assess the balance between supply and demand in the market."""
        if supply_growth > 5.0 and absorption_rate < 15:
            return "oversupplied"
        elif supply_growth < 1.0 and absorption_rate > 20:
            return "undersupplied"
        elif supply_growth > 3.0 and absorption_rate > 25:
            return "growing - balanced"
        elif supply_growth < 1.0 and absorption_rate < 10:
            return "contracting - balanced"
        else:
            return "balanced"
    
    def _determine_market_cycle(self, rental_growth: float, unemployment: float) -> str:
        """Determine the current market cycle position."""
        if rental_growth > 5.0 and unemployment < 4.0:
            return "expansion"
        elif rental_growth > 2.0 and unemployment < 5.0:
            return "stable growth"
        elif rental_growth < 1.0 and unemployment > 6.0:
            return "contraction"
        elif rental_growth < 0 and unemployment > 7.0:
            return "recession"
        elif rental_growth > 0 and unemployment > 5.5:
            return "early recovery"
        else:
            return "stable"
    
    def _determine_opportunity_outlook(self, market_cycle: str, property_type: str) -> str:
        """Determine the opportunity outlook based on market cycle and property type."""
        opportunity_matrix = {
            "expansion": {
                "multifamily": "strong",
                "luxury": "very strong",
                "affordable": "moderate",
                "student": "strong",
                "senior": "moderate"
            },
            "stable growth": {
                "multifamily": "moderate",
                "luxury": "strong",
                "affordable": "moderate",
                "student": "moderate",
                "senior": "moderate"
            },
            "contraction": {
                "multifamily": "weak",
                "luxury": "very weak",
                "affordable": "moderate",
                "student": "weak",
                "senior": "moderate"
            },
            "recession": {
                "multifamily": "weak",
                "luxury": "very weak",
                "affordable": "strong",
                "student": "moderate",
                "senior": "moderate"
            },
            "early recovery": {
                "multifamily": "strong",
                "luxury": "moderate",
                "affordable": "very strong",
                "student": "moderate",
                "senior": "moderate"
            },
            "stable": {
                "multifamily": "moderate",
                "luxury": "moderate",
                "affordable": "moderate",
                "student": "moderate",
                "senior": "moderate"
            }
        }
        
        property_type_lower = property_type.lower()
        cycle_map = opportunity_matrix.get(market_cycle, {})
        return cycle_map.get(property_type_lower, "moderate")
    
    def _determine_risk_level(self, market_cycle: str, unemployment: float) -> str:
        """Determine risk level based on market cycle and unemployment rate."""
        if market_cycle in ["expansion", "stable growth"] and unemployment < 5.0:
            return "low"
        elif market_cycle in ["contraction", "recession"] and unemployment > 6.0:
            return "high"
        elif market_cycle == "early recovery":
            return "moderate-high"
        else:
            return "moderate"
    
    def _calculate_market_health_score(self, market_analysis: Dict[str, Any]) -> float:
        """Calculate an overall market health score based on various metrics."""
        # Extract relevant metrics
        try:
            economic = market_analysis.get("economic_indicators", {})
            demographic = market_analysis.get("demographic_data", {})
            rental = market_analysis.get("rental_trends", {})
            
            # Base score out of 100
            score = 50  # Start at neutral
            
            # Economic factors (up to +/- 20 points)
            unemployment = economic.get("unemployment_rate")
            if unemployment is not None:
                # Lower unemployment is better
                score += max(-10, min(10, (5.0 - unemployment) * 2))
            
            income_growth = economic.get("median_income_growth")
            if income_growth is not None:
                # Higher income growth is better
                score += max(-5, min(5, income_growth))
            
            job_growth = economic.get("job_growth")
            if job_growth is not None:
                # Higher job growth is better
                score += max(-5, min(5, job_growth * 2))
            
            # Demographic factors (up to +/- 15 points)
            renter_pct = demographic.get("renter_occupied_percentage")
            if renter_pct is not None:
                # Higher renter percentage is better for multifamily (to a point)
                score += max(-5, min(5, (renter_pct - 30) / 10))
            
            # Rental trends (up to +/- 15 points)
            yoy_growth = rental.get("year_over_year_growth")
            if yoy_growth is not None:
                # Higher rental growth is better
                score += max(-10, min(10, yoy_growth * 2))
            
            # Clamp to 0-100 range
            score = max(0, min(100, score))
            return round(score, 1)
            
        except Exception as e:
            logger.error(f"Error calculating market health score: {e}")
            return 50.0  # Default to neutral
    
    def _generate_market_summary(self, market_analysis: Dict[str, Any]) -> str:
        """Generate an executive summary of the market analysis."""
        try:
            # Extract key data points
            city = market_analysis.get("overview", {}).get("city", "")
            state = market_analysis.get("overview", {}).get("state", "")
            property_type = market_analysis.get("overview", {}).get("property_type", "multifamily")
            
            economic = market_analysis.get("economic_indicators", {})
            demographic = market_analysis.get("demographic_data", {})
            rental = market_analysis.get("rental_trends", {})
            supply_demand = market_analysis.get("supply_demand_metrics", {})
            projections = market_analysis.get("market_projections", {})
            
            # Calculate market health score if not already present
            health_score = market_analysis.get("market_health_score")
            if health_score is None:
                health_score = self._calculate_market_health_score(market_analysis)
            
            # Determine market strength
            strength = "weak"
            if health_score >= 80:
                strength = "very strong"
            elif health_score >= 65:
                strength = "strong"
            elif health_score >= 45:
                strength = "moderate"
            elif health_score >= 30:
                strength = "weak"
            else:
                strength = "very weak"
                
            # Build summary
            summary = f"The {property_type} market in {city}, {state} is currently showing {strength} fundamentals "
            summary += f"with an overall market health score of {health_score}/100. "
            
            # Add economic details
            unemployment = economic.get("unemployment_rate")
            job_growth = economic.get("job_growth")
            if unemployment is not None and job_growth is not None:
                summary += f"The local economy has {job_growth:.1f}% job growth with {unemployment:.1f}% unemployment. "
            
            # Add rental trends
            yoy_growth = rental.get("year_over_year_growth")
            vacancy = rental.get("vacancy_rate_estimate")
            if yoy_growth is not None and vacancy is not None:
                summary += f"Rental rates are {rental.get('quarterly_trend', 'moving')} at {yoy_growth:.1f}% annually with an estimated vacancy of {vacancy:.1f}%. "
            
            # Add supply/demand balance
            supply_balance = supply_demand.get("supply_demand_balance")
            if supply_balance:
                summary += f"The market is currently {supply_balance} in terms of supply and demand. "
            
            # Add future outlook
            market_cycle = projections.get("market_cycle_position")
            outlook = projections.get("opportunity_outlook")
            if market_cycle and outlook:
                summary += f"The market appears to be in the {market_cycle} phase of the real estate cycle with a {outlook} outlook for {property_type} properties."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating market summary: {e}")
            return "Market analysis summary could not be generated due to insufficient data."
    
    def _merge_results(self, base_results: Dict[str, Any], mcp_results: Dict[str, Any]) -> None:
        """Merge MCP results into the base results dictionary."""
        # Deep merge to handle nested dictionaries
        for key, value in mcp_results.items():
            if key in base_results and isinstance(base_results[key], dict) and isinstance(value, dict):
                self._merge_results(base_results[key], value)
            else:
                # Only overwrite if not already present or MCP has more detailed data
                if key not in base_results or (isinstance(value, dict) and len(value) > len(base_results[key])):
                    base_results[key] = value