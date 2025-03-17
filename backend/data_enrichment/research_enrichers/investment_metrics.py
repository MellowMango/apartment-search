# backend/data_enrichment/research_enrichers/investment_metrics.py
import os
import logging
import asyncio
from typing import Dict, Any, List, Optional, Tuple
import aiohttp
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class InvestmentMetricsEnricher:
    """
    Enriches property data with investment metrics.
    
    Uses financial APIs to calculate key investment metrics like cap rates,
    potential returns, and value-add opportunities.
    """
    
    def __init__(self):
        """Initialize with API keys from environment"""
        self.fmp_api_key = os.getenv("FMP_API_KEY", "")
        self.fred_api_key = os.getenv("FRED_API_KEY", "")
        self.polygon_api_key = os.getenv("POLYGON_API_KEY", "")
        self.alpha_vantage_key = os.getenv("ALPHA_VANTAGE_API_KEY", "")
        self.cache = {}
        
        logger.info("Investment Metrics Enricher initialized")
    
    async def calculate_metrics(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate investment metrics for a property.
        
        Args:
            property_data: Property details
            
        Returns:
            Dictionary of investment metrics
        """
        # Basic property info needed for calculations
        address = property_data.get("address", "")
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        year_built = property_data.get("year_built")
        units = property_data.get("units")
        square_feet = property_data.get("square_feet")
        
        # Get market data asynchronously
        market_data_task = self._get_market_data(city, state)
        
        # Calculate basic metrics
        noi = self._calculate_noi(property_data)
        property_value = self._estimate_property_value(property_data)
        
        # Calculate cap rate if we have NOI and property value
        cap_rate = None
        if noi and property_value:
            cap_rate = (noi / property_value) * 100  # as percentage
        
        # Get market data for comparative analysis
        market_data = await market_data_task
        
        # Calculate potential value-add opportunities
        value_add_opportunities = self._identify_value_add(
            property_data, market_data
        )
        
        # Calculate potential returns under different scenarios
        scenarios = await self._calculate_investment_scenarios(
            property_data, market_data
        )
        
        return {
            "property_metrics": {
                "estimated_value": property_value,
                "estimated_noi": noi,
                "cap_rate": cap_rate,
                "price_per_unit": property_value / units if units and property_value else None,
                "price_per_sqft": property_value / square_feet if square_feet and property_value else None
            },
            "market_data": market_data,
            "market_comparison": {
                "cap_rate_difference": cap_rate - market_data.get("avg_cap_rate", 0) 
                                       if cap_rate and market_data.get("avg_cap_rate") else None,
                "price_per_unit_difference": (property_value / units if units and property_value else 0) - 
                                            market_data.get("avg_price_per_unit", 0)
                                            if units and property_value and market_data.get("avg_price_per_unit") else None
            },
            "value_add_opportunities": value_add_opportunities,
            "investment_scenarios": scenarios
        }
    
    async def _get_market_data(self, city: str, state: str) -> Dict[str, Any]:
        """Get market data for a location"""
        # Cache key based on city and state
        cache_key = f"{city.lower()}_{state.lower()}"
        
        # Check cache
        if cache_key in self.cache:
            cache_entry = self.cache[cache_key]
            # Cache valid for 7 days
            cache_age = (datetime.now() - cache_entry["timestamp"]).days
            if cache_age < 7:
                return cache_entry["data"]
        
        # If we have FMP API key, use it to get market data
        if self.fmp_api_key:
            try:
                # Make up to 3 API calls in parallel
                tasks = [
                    self._get_real_estate_market_data(city, state),
                    self._get_economic_indicators(state),
                    self._get_interest_rate_data()
                ]
                
                real_estate_data, economic_data, interest_rate_data = await asyncio.gather(*tasks)
                
                market_data = {
                    "avg_cap_rate": real_estate_data.get("average_cap_rate"),
                    "avg_price_per_unit": real_estate_data.get("average_price_per_unit"),
                    "avg_price_per_sqft": real_estate_data.get("average_price_per_sqft"),
                    "vacancy_rate": real_estate_data.get("vacancy_rate"),
                    "rent_growth": real_estate_data.get("rent_growth"),
                    "economic_indicators": economic_data,
                    "interest_rates": interest_rate_data
                }
                
                # Cache the result
                self.cache[cache_key] = {
                    "data": market_data,
                    "timestamp": datetime.now()
                }
                
                return market_data
                
            except Exception as e:
                logger.error(f"Error fetching market data: {e}")
        
        # Fallback to default values
        return {
            "avg_cap_rate": 5.0,  # typical multifamily cap rate
            "avg_price_per_unit": 150000,  # typical price per unit
            "avg_price_per_sqft": 200,  # typical price per sqft
            "vacancy_rate": 5.0,  # typical vacancy rate
            "rent_growth": 3.0,  # typical annual rent growth
            "interest_rates": {
                "30yr_fixed": 4.5,  # typical 30-year fixed rate
                "10yr_treasury": 2.0  # typical 10-year treasury
            }
        }
    
    async def _get_real_estate_market_data(self, city: str, state: str) -> Dict[str, Any]:
        """Get real estate market data for a location"""
        # For now, return simulated data
        # In production, this would call a real estate data API
        return {
            "average_cap_rate": 5.0,
            "average_price_per_unit": 150000,
            "average_price_per_sqft": 200,
            "vacancy_rate": 5.0,
            "rent_growth": 3.0
        }
    
    async def _get_economic_indicators(self, state: str) -> Dict[str, Any]:
        """Get economic indicators for a state"""
        # If we have FRED API key, use it to get economic indicators
        if self.fred_api_key:
            try:
                # Implement FRED API call here
                pass
            except Exception as e:
                logger.error(f"Error fetching economic indicators: {e}")
        
        # Return simulated data
        return {
            "unemployment_rate": 5.0,
            "gdp_growth": 2.5,
            "population_growth": 1.2,
            "median_income": 65000
        }
    
    async def _get_interest_rate_data(self) -> Dict[str, Any]:
        """Get current interest rate data"""
        # If we have Alpha Vantage API key, use it to get interest rate data
        if self.alpha_vantage_key:
            try:
                # Implement Alpha Vantage API call here
                pass
            except Exception as e:
                logger.error(f"Error fetching interest rate data: {e}")
        
        # Return simulated data
        return {
            "30yr_fixed": 4.5,
            "15yr_fixed": 3.75,
            "10yr_treasury": 2.0,
            "prime_rate": 3.25
        }
    
    def _calculate_noi(self, property_data: Dict[str, Any]) -> Optional[float]:
        """Calculate Net Operating Income based on property data"""
        # If we have income data, use it
        if property_data.get("annual_income") and property_data.get("annual_expenses"):
            return property_data["annual_income"] - property_data["annual_expenses"]
        
        # Otherwise, estimate based on property characteristics
        units = property_data.get("units")
        if not units:
            return None
        
        # Estimate monthly rent per unit based on market data
        estimated_rent = 1500  # fallback value
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        
        # Adjust estimated rent based on location
        # This would be more sophisticated in production
        if city and state:
            key_locations = {
                "austin_tx": 1800,
                "houston_tx": 1200,
                "dallas_tx": 1500,
                "san_antonio_tx": 1100,
                "fort_worth_tx": 1300
            }
            location_key = f"{city.lower()}_{state.lower()}"
            estimated_rent = key_locations.get(location_key, estimated_rent)
        
        # Calculate annual income
        annual_income = units * estimated_rent * 12
        
        # Estimate expenses (typically 40% of income for multifamily)
        annual_expenses = annual_income * 0.4
        
        # NOI
        return annual_income - annual_expenses
    
    def _estimate_property_value(self, property_data: Dict[str, Any]) -> Optional[float]:
        """Estimate property value based on available data"""
        # If we have a price, use it
        if property_data.get("price"):
            return property_data["price"]
        
        # Otherwise, estimate based on NOI and cap rate
        noi = self._calculate_noi(property_data)
        if not noi:
            return None
        
        # Use default cap rate of 5%
        cap_rate = 0.05
        
        # Adjust cap rate based on property characteristics
        year_built = property_data.get("year_built")
        if year_built:
            # Newer properties generally have lower cap rates
            current_year = datetime.now().year
            age = current_year - year_built
            if age < 5:
                cap_rate = 0.045
            elif age < 10:
                cap_rate = 0.048
            elif age < 20:
                cap_rate = 0.052
            elif age < 40:
                cap_rate = 0.055
            else:
                cap_rate = 0.06
        
        # Calculate value using direct capitalization
        return noi / cap_rate
    
    def _identify_value_add(self, 
                          property_data: Dict[str, Any], 
                          market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify potential value-add opportunities"""
        opportunities = []
        
        # Check for renovation opportunity
        year_built = property_data.get("year_built")
        if year_built and (datetime.now().year - year_built) > 15:
            opportunities.append({
                "type": "renovation",
                "description": "Property is over 15 years old and may benefit from renovation",
                "potential_roi": "15-25%",
                "implementation_cost": "Medium to High"
            })
        
        # Check for rent increase opportunity
        if property_data.get("average_rent") and market_data.get("avg_rent"):
            if property_data["average_rent"] < market_data["avg_rent"] * 0.9:
                opportunities.append({
                    "type": "rent_increase",
                    "description": "Current rents are below market rates",
                    "potential_roi": "10-20%",
                    "implementation_cost": "Low"
                })
        
        # Check for amenity addition opportunity
        if "amenities" in property_data:
            missing_amenities = []
            common_amenities = ["pool", "fitness center", "business center", "dog park"]
            
            for amenity in common_amenities:
                if amenity not in property_data["amenities"]:
                    missing_amenities.append(amenity)
            
            if missing_amenities:
                opportunities.append({
                    "type": "amenity_addition",
                    "description": f"Consider adding missing amenities: {', '.join(missing_amenities)}",
                    "potential_roi": "5-15%",
                    "implementation_cost": "Medium"
                })
        
        # Check for operational efficiency opportunity
        if property_data.get("annual_expenses") and property_data.get("annual_income"):
            expense_ratio = property_data["annual_expenses"] / property_data["annual_income"]
            if expense_ratio > 0.45:  # Industry standard is around 40%
                opportunities.append({
                    "type": "operational_efficiency",
                    "description": "Expense ratio is above industry standard",
                    "potential_roi": "5-10%",
                    "implementation_cost": "Low to Medium"
                })
        
        return opportunities
    
    async def _calculate_investment_scenarios(self, 
                                           property_data: Dict[str, Any],
                                           market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Calculate different investment scenarios"""
        estimated_value = self._estimate_property_value(property_data)
        noi = self._calculate_noi(property_data)
        
        if not estimated_value or not noi:
            return []
        
        scenarios = []
        
        # Basic hold scenario
        scenarios.append({
            "name": "Hold for 5 years",
            "strategy_description": "Hold property with minimal improvements",
            "initial_investment": estimated_value * 0.25,  # 25% down payment
            "financing": {
                "loan_amount": estimated_value * 0.75,
                "interest_rate": market_data.get("interest_rates", {}).get("30yr_fixed", 4.5),
                "term_years": 30,
                "amortization_years": 30
            },
            "projections": {
                "annual_noi_growth": 0.03,  # 3% per year
                "projected_sale_price": estimated_value * 1.15,  # 15% appreciation
                "projected_irr": 0.12,  # 12% IRR
                "projected_cash_on_cash": 0.08  # 8% cash-on-cash
            }
        })
        
        # Value-add scenario
        scenarios.append({
            "name": "Value-Add Renovation",
            "strategy_description": "Implement renovations to increase rents",
            "initial_investment": estimated_value * 0.25 + (estimated_value * 0.1),  # 25% down + 10% renovation
            "financing": {
                "loan_amount": estimated_value * 0.75,
                "interest_rate": market_data.get("interest_rates", {}).get("30yr_fixed", 4.5),
                "term_years": 30,
                "amortization_years": 30
            },
            "projections": {
                "annual_noi_growth": 0.05,  # 5% per year
                "projected_sale_price": estimated_value * 1.3,  # 30% appreciation
                "projected_irr": 0.18,  # 18% IRR
                "projected_cash_on_cash": 0.1  # 10% cash-on-cash
            }
        })
        
        # Repositioning scenario
        scenarios.appen