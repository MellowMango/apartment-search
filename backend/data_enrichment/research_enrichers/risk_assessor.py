import os
import logging
import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
import aiohttp

from backend.data_enrichment.mcp_client import DeepResearchMCPClient

logger = logging.getLogger(__name__)

from backend.app.utils.architecture import layer, ArchitectureLayer

@layer(ArchitectureLayer.PROCESSING)
class RiskAssessor:
    """
    Identifies potential risks and blindspots for properties.
    
    Analyzes legal, environmental, maintenance, tenant, market, and financial risks
    to provide a comprehensive risk assessment and mitigation recommendations.
    """
    
    def __init__(self):
        """Initialize with API keys from environment"""
        self.openai_api_key = os.getenv("OPENAI_API_KEY", "")
        self.property_records_api_key = os.getenv("PROPERTY_RECORDS_API_KEY", "")
        self.building_permits_api_key = os.getenv("BUILDING_PERMITS_API_KEY", "")
        self.environmental_api_key = os.getenv("ENVIRONMENTAL_API_KEY", "")
        self.crime_api_key = os.getenv("CRIME_API_KEY", "")
        self.cache = {}
        
        logger.info("Risk Assessor initialized")
    
    def _generate_risk_summary(self, risk_assessment: Dict[str, Any]) -> str:
        """Generate a summary of identified risks and recommendations."""
        try:
            # Extract risk levels for each category
            risk_categories = ["physical_risks", "environmental_risks", "financial_risks", 
                              "market_risks", "legal_regulatory_risks", "tenant_risks"]
            
            # Count high and moderate risks
            high_risks = []
            moderate_risks = []
            
            for category in risk_categories:
                if category in risk_assessment:
                    cat_data = risk_assessment[category]
                    if cat_data.get("risk_level") == "high":
                        high_risks.append(category.replace("_", " ").replace("risks", ""))
                    elif cat_data.get("risk_level") == "moderate":
                        moderate_risks.append(category.replace("_", " ").replace("risks", ""))
            
            # Get overall risk score
            overall = risk_assessment.get("overall_risk_score", {})
            overall_level = overall.get("risk_level", "unknown")
            overall_score = overall.get("overall_score", 5)
            
            # Generate summary
            summary = f"Overall risk assessment: {overall_level.upper()} ({overall_score}/10). "
            
            if high_risks:
                summary += f"High risk areas include {', '.join(high_risks)}. "
            
            if moderate_risks:
                summary += f"Moderate risk areas include {', '.join(moderate_risks)}. "
            
            # Add key risk factors from each high risk category
            for category in risk_categories:
                if category in risk_assessment and risk_assessment[category].get("risk_level") == "high":
                    cat_data = risk_assessment[category]
                    
                    # Get the specific risks
                    specific_risks = []
                    if "identified_risks" in cat_data:
                        for risk in cat_data["identified_risks"][:2]:  # Get top 2 risks
                            specific_risks.append(risk.get("risk", ""))
                    
                    if specific_risks:
                        cat_name = category.replace("_", " ").replace("risks", "risk")
                        summary += f"Key {cat_name} factors include {' and '.join(specific_risks)}. "
            
            # Add key recommendations
            if "key_recommendations" in risk_assessment and risk_assessment["key_recommendations"]:
                recommendations = risk_assessment["key_recommendations"][:3]  # Top 3 recommendations
                summary += f"Primary recommendations: {'; '.join(recommendations)}."
            
            return summary
            
        except Exception as e:
            logger.error(f"Error generating risk summary: {e}")
            return "Risk assessment completed. Review detailed findings in each risk category."
            
    async def assess_risks(self, property_data: Dict[str, Any], 
                          additional_data: Dict[str, Any] = None,
                          depth: str = "standard") -> Dict[str, Any]:
        """
        Assess risks for a property.
        
        Args:
            property_data: Property details
            additional_data: Optional additional data from other enrichers
            depth: Research depth level (basic, standard, comprehensive, exhaustive)
            
        Returns:
            Dictionary of risk assessment
        """
        # Extract basic property info needed for risk assessment
        address = property_data.get("address", "")
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        zip_code = property_data.get("zip_code", "")
        property_type = property_data.get("property_type", "multifamily")
        year_built = property_data.get("year_built")
        
        # Cache key for this property's risk assessment
        cache_key = f"risk_assessment:{address}:{city}:{state}:{property_type}"
        
        # Check cache first
        cached_result = self.cache.get(cache_key)
        if cached_result and cached_result.get("timestamp"):
            cache_time = datetime.fromisoformat(cached_result.get("timestamp"))
            # Risk assessment cache is valid for 90 days
            if datetime.now() - cache_time < timedelta(days=90):
                logger.info(f"Using cached risk assessment for {address}, {city}, {state}")
                return cached_result.get("data", {})
        
        # Create tasks for parallel API calls
        tasks = []
        
        # Always include basic risk assessments
        tasks.append(self._assess_physical_risks(property_data))
        tasks.append(self._assess_financial_risks(property_data, additional_data))
        
        # Add more detailed analysis based on depth
        if depth in ["standard", "comprehensive", "exhaustive"]:
            tasks.append(self._assess_environmental_risks(property_data))
            tasks.append(self._assess_market_risks(property_data, additional_data))
        
        if depth in ["comprehensive", "exhaustive"]:
            tasks.append(self._assess_legal_regulatory_risks(property_data))
            tasks.append(self._assess_tenant_risks(property_data))
        
        # For exhaustive research, use MCP for advanced risk analysis
        mcp_results = {}
        if depth == "exhaustive":
            try:
                mcp_client = DeepResearchMCPClient()
                mcp_results = await mcp_client.risk_assessment_analysis(property_data)
            except Exception as e:
                logger.error(f"Error using MCP for risk assessment: {e}")
                mcp_results = {"error": str(e)}
        
        # Execute all API tasks in parallel
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Combine results into a single response
        risk_assessment = {
            "overview": {
                "property_address": address,
                "city": city,
                "state": state,
                "property_type": property_type,
                "assessment_date": datetime.now().isoformat(),
            }
        }
        
        # Process results from each API call
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error in risk assessment API call {i}: {result}")
                continue
                
            # Add successful results to the assessment
            risk_assessment.update(result)
        
        # If we have MCP results and no error, integrate them
        if mcp_results and "error" not in mcp_results:
            self._merge_results(risk_assessment, mcp_results)
        
        # Calculate overall risk score
        risk_assessment["overall_risk_score"] = self._calculate_overall_risk_score(risk_assessment)
        
        # Generate executive summary and recommendations
        if len(risk_assessment) > 3:  # More than just overview and a couple data points
            risk_assessment["executive_summary"] = self._generate_risk_summary(risk_assessment)
            risk_assessment["key_recommendations"] = self._suggest_risk_recommendations(risk_assessment)
        
        # Cache the results
        self.cache[cache_key] = {
            "timestamp": datetime.now().isoformat(),
            "data": risk_assessment
        }
        
        return risk_assessment
    
    async def _assess_physical_risks(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess physical and maintenance risks for a property.
        
        Args:
            property_data: Property details
            
        Returns:
            Dictionary of physical risks
        """
        try:
            # Extract relevant property details
            year_built = property_data.get("year_built")
            property_type = property_data.get("property_type", "multifamily")
            description = property_data.get("description", "")
            building_quality = property_data.get("building_quality", "average")
            
            # Determine age-related risks
            age_risks = []
            current_year = datetime.now().year
            
            if year_built:
                property_age = current_year - year_built
                
                # Age-based risk assessment
                if property_age > 50:
                    age_risks.extend([
                        "Potential foundation issues",
                        "Outdated electrical systems",
                        "Outdated plumbing systems",
                        "Potential asbestos or lead paint",
                        "Roof replacement likely needed"
                    ])
                elif property_age > 30:
                    age_risks.extend([
                        "HVAC systems may need replacement",
                        "Plumbing updates may be needed",
                        "Electrical updates may be recommended",
                        "Windows may need replacement"
                    ])
                elif property_age > 15:
                    age_risks.extend([
                        "HVAC systems approaching end of life",
                        "Roof may need maintenance or replacement",
                        "Appliances may need replacement"
                    ])
            else:
                # No year built info, assume moderate age risks
                age_risks.append("Unknown construction date - cannot assess age-related risks")
            
            # Look for maintenance clues in description
            maintenance_clues = {
                "renovated": -2,  # Reduces risk
                "updated": -2,
                "new roof": -3,
                "new hvac": -3,
                "remodeled": -2,
                "upgraded": -1,
                "repairs needed": 3,
                "needs work": 3,
                "as-is": 2,
                "deferred maintenance": 4,
                "fixer": 3
            }
            
            maintenance_risk_score = 0
            maintenance_flags = []
            
            if description:
                description_lower = description.lower()
                for clue, score in maintenance_clues.items():
                    if clue in description_lower:
                        maintenance_risk_score += score
                        if score > 0:
                            maintenance_flags.append(f"Description mentions '{clue}'")
            
            # Building quality adjustments
            quality_adjustments = {
                "luxury": -2,
                "class a": -2,
                "class b": 0,
                "class c": 2,
                "class d": 4,
                "low income": 2,
                "affordable": 1,
                "high-end": -2,
                "poor": 4,
                "excellent": -3,
                "good": -1,
                "average": 0,
                "below average": 2
            }
            
            if building_quality:
                building_quality_lower = building_quality.lower()
                for quality, adjustment in quality_adjustments.items():
                    if quality in building_quality_lower:
                        maintenance_risk_score += adjustment
            
            # Determine risk level based on score
            risk_level = "moderate"
            if maintenance_risk_score <= -4:
                risk_level = "very low"
            elif maintenance_risk_score <= -2:
                risk_level = "low"
            elif maintenance_risk_score >= 4:
                risk_level = "very high"
            elif maintenance_risk_score >= 2:
                risk_level = "high"
            
            # Estimate maintenance costs
            base_cost_per_unit = 1000  # Annual maintenance per unit
            if maintenance_risk_score >= 3:
                base_cost_per_unit *= 1.5
            elif maintenance_risk_score >= 1:
                base_cost_per_unit *= 1.2
            elif maintenance_risk_score <= -3:
                base_cost_per_unit *= 0.7
            
            units = property_data.get("units", 1)
            estimated_annual_maintenance = base_cost_per_unit * units
            
            return {
                "physical_risks": {
                    "risk_level": risk_level,
                    "risk_score": min(10, max(1, maintenance_risk_score + 5)),  # Scale to 1-10
                    "age_related_risks": age_risks,
                    "maintenance_flags": maintenance_flags,
                    "estimated_annual_maintenance": estimated_annual_maintenance,
                    "renovation_needed": maintenance_risk_score > 2,
                    "critical_systems_concerns": [risk for risk in age_risks if "electrical" in risk.lower() or "plumbing" in risk.lower() or "foundation" in risk.lower()],
                    "data_source": "Derived from property details and age-based analysis"
                }
            }
                
        except Exception as e:
            logger.error(f"Error assessing physical risks: {e}")
            return {
                "physical_risks": {
                    "error": f"Failed to assess physical risks: {str(e)}",
                    "risk_level": "unknown",
                    "risk_score": 5,  # Default to medium
                    "age_related_risks": [],
                    "maintenance_flags": []
                }
            }
    
    async def _assess_financial_risks(self, property_data: Dict[str, Any], additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Assess financial risks for a property.
        
        Args:
            property_data: Property details
            additional_data: Optional additional data from other enrichers
            
        Returns:
            Dictionary of financial risks
        """
        try:
            # Extract financial metrics if available
            price = property_data.get("price")
            noi = property_data.get("noi")  # Net Operating Income
            cap_rate = property_data.get("cap_rate")
            mortgage_rate = property_data.get("mortgage_rate", 5.0)  # Default to 5% if not provided
            ltv = property_data.get("loan_to_value", 0.75)  # Default to 75% LTV
            debt_service = property_data.get("debt_service")
            vacancy_rate = property_data.get("vacancy_rate", 0.05)  # Default to 5% vacancy
            
            # Try to get additional metrics from other enrichers
            if additional_data and "investment_metrics" in additional_data:
                inv_metrics = additional_data["investment_metrics"]
                if noi is None:
                    noi = inv_metrics.get("noi")
                if cap_rate is None:
                    cap_rate = inv_metrics.get("cap_rate")
                if debt_service is None:
                    debt_service = inv_metrics.get("debt_service")
                
            # Calculate missing metrics if possible
            financial_metrics = {}
            
            # If we have price and cap rate but no NOI, calculate it
            if price and cap_rate and noi is None:
                noi = price * (cap_rate / 100)
                financial_metrics["noi"] = noi
            
            # If we have NOI and price but no cap rate, calculate it
            elif noi and price and cap_rate is None:
                cap_rate = (noi / price) * 100
                financial_metrics["cap_rate"] = cap_rate
            
            # Calculate debt service if we have price, LTV, and mortgage rate
            if price and ltv and mortgage_rate and debt_service is None:
                loan_amount = price * ltv
                annual_rate = mortgage_rate / 100
                monthly_rate = annual_rate / 12
                term_months = 30 * 12  # Assume 30-year loan
                
                # Calculate monthly payment using mortgage formula
                # P = L[c(1 + c)^n]/[(1 + c)^n - 1]
                # where L = loan amount, c = monthly interest rate, n = number of payments
                monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate) ** term_months) / ((1 + monthly_rate) ** term_months - 1)
                
                debt_service = monthly_payment * 12  # Annual debt service
                financial_metrics["debt_service"] = debt_service
            
            # Calculate debt service coverage ratio if possible
            dscr = None
            if noi and debt_service and debt_service > 0:
                dscr = noi / debt_service
                financial_metrics["dscr"] = dscr
            
            # Assess financial risk level based on metrics
            risk_flags = []
            risk_score = 5  # Start at medium risk
            
            # DSCR assessment
            if dscr is not None:
                if dscr < 1.0:
                    risk_flags.append("Negative cash flow - DSCR below 1.0")
                    risk_score += 3
                elif dscr < 1.2:
                    risk_flags.append("Tight cash flow - DSCR below 1.2")
                    risk_score += 2
                elif dscr < 1.4:
                    risk_flags.append("Moderate cash flow - DSCR below 1.4")
                    risk_score += 1
                elif dscr > 2.0:
                    risk_flags.append("Strong cash flow - DSCR above 2.0")
                    risk_score -= 2
            
            # Cap rate assessment
            if cap_rate is not None:
                market_avg_cap = 5.5  # National average multifamily cap rate (adjust as needed)
                if cap_rate < market_avg_cap - 1:
                    risk_flags.append(f"Below market cap rate ({cap_rate:.1f}% vs {market_avg_cap:.1f}% avg)")
                    risk_score += 2
                elif cap_rate > market_avg_cap + 2:
                    risk_flags.append(f"Above market cap rate ({cap_rate:.1f}% vs {market_avg_cap:.1f}% avg)")
                    risk_score -= 1
            
            # Vacancy assessment
            if vacancy_rate is not None:
                if vacancy_rate > 0.1:  # High vacancy
                    risk_flags.append(f"High vacancy rate ({vacancy_rate*100:.1f}%)")
                    risk_score += 2
                elif vacancy_rate < 0.03:  # Very low vacancy
                    risk_flags.append(f"Low vacancy rate ({vacancy_rate*100:.1f}%) - could indicate underpriced units")
                    risk_score += 0
            
            # LTV assessment
            if ltv is not None:
                if ltv > 0.8:
                    risk_flags.append(f"High leverage (LTV: {ltv*100:.1f}%)")
                    risk_score += 2
                elif ltv < 0.5:
                    risk_flags.append(f"Low leverage (LTV: {ltv*100:.1f}%)")
                    risk_score -= 1
            
            # Market interest rate risk
            current_market_rate = 5.0  # Example current market rate, adjust as needed
            if mortgage_rate < current_market_rate - 1:
                risk_flags.append("Below-market interest rate - refinancing risk if adjustable")
                # No score impact as this could be positive (fixed low rate) or negative (adjustable)
            
            # Risk of interest rate increases
            # Assume higher risk if high LTV and low DSCR
            if ltv and ltv > 0.7 and dscr and dscr < 1.5:
                risk_flags.append("Vulnerable to interest rate increases due to high leverage and tight cash flow")
                risk_score += 1
            
            # Finalize risk assessment
            risk_level = "moderate"
            if risk_score <= 3:
                risk_level = "low"
            elif risk_score >= 8:
                risk_level = "high"
            
            return {
                "financial_risks": {
                    "risk_level": risk_level,
                    "risk_score": min(10, max(1, risk_score)),  # Ensure within 1-10 range
                    "identified_risks": risk_flags,
                    "financial_metrics": financial_metrics,
                    "data_source": "Derived from property financial data and market analysis"
                }
            }
                
        except Exception as e:
            logger.error(f"Error assessing financial risks: {e}")
            return {
                "financial_risks": {
                    "error": f"Failed to assess financial risks: {str(e)}",
                    "risk_level": "unknown",
                    "risk_score": 5
                }
            }
    
    async def _assess_environmental_risks(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess environmental risks for a property.
        
        Args:
            property_data: Property details
            
        Returns:
            Dictionary of environmental risks
        """
        try:
            # Extract relevant property details
            address = property_data.get("address", "")
            city = property_data.get("city", "")
            state = property_data.get("state", "")
            zip_code = property_data.get("zip_code", "")
            property_type = property_data.get("property_type", "multifamily")
            year_built = property_data.get("year_built")
            
            # Placeholder for API call to environmental risk service
            # In a production environment, this would call an actual environmental risk API
            
            # For now, we'll use a combination of state-based risks and age-based risks
            
            # State-based environmental risks
            state_environmental_risks = {
                "CA": ["Earthquake risk", "Wildfire risk", "Drought conditions"],
                "FL": ["Hurricane risk", "Flooding risk", "Sea level rise vulnerability"],
                "TX": ["Hurricane risk", "Flooding risk", "Tornado risk"],
                "LA": ["Hurricane risk", "Flooding risk", "Coastal erosion"],
                "OK": ["Tornado risk", "Extreme weather patterns"],
                "NY": ["Coastal flooding risk", "Winter storm risk"],
                "NJ": ["Coastal flooding risk", "Hurricane risk"],
                "CO": ["Wildfire risk", "Flash flooding risk", "Drought conditions"],
                "AZ": ["Extreme heat", "Drought conditions", "Flash flooding risk"],
                "NV": ["Extreme heat", "Drought conditions", "Flash flooding risk"],
            }
            
            # Default risks for states not in our dictionary
            default_risks = ["Local natural disaster risks may apply"]
            
            # Get risks for this property's state
            state_risks = state_environmental_risks.get(state, default_risks)
            
            # Age-based environmental risks
            age_environmental_risks = []
            current_year = datetime.now().year
            
            if year_built:
                property_age = current_year - year_built
                
                # Age-based environmental risk assessment
                if property_age > 40:  # Pre-1980s construction
                    age_environmental_risks.extend([
                        "Potential asbestos-containing materials",
                        "Potential lead-based paint",
                        "Possible outdated electrical systems",
                        "Potential underground storage tanks"
                    ])
                elif property_age > 20:  # Pre-2000s construction
                    age_environmental_risks.extend([
                        "Potential for some hazardous building materials",
                        "Older HVAC systems may contain R-22 refrigerant (being phased out)"
                    ])
            
            # Combine all identified risks
            identified_risks = []
            risk_score = 5  # Start at medium risk
            
            # Process state risks
            for risk in state_risks:
                severity = "moderate"
                impact = "moderate"
                
                # Increase severity for certain high-risk conditions
                if "Hurricane" in risk and state in ["FL", "LA"]:
                    severity = "high"
                    risk_score += 1
                if "Flooding" in risk and state in ["FL", "LA", "TX"]:
                    severity = "high"
                    risk_score += 1
                if "Earthquake" in risk and state == "CA":
                    severity = "high"
                    risk_score += 1
                if "Wildfire" in risk and state in ["CA", "CO"]:
                    severity = "high"
                    risk_score += 1
                
                identified_risks.append({
                    "type": risk,
                    "severity": severity,
                    "potential_impact": impact,
                    "mitigation_options": self._get_environmental_risk_mitigation(risk)
                })
            
            # Process age risks
            for risk in age_environmental_risks:
                identified_risks.append({
                    "type": risk,
                    "severity": "moderate",
                    "potential_impact": "moderate",
                    "mitigation_options": self._get_environmental_risk_mitigation(risk)
                })
                
                # Adjust risk score for serious age-related issues
                if "asbestos" in risk.lower() or "lead" in risk.lower():
                    risk_score += 1
            
            # Determine overall environmental risk level
            risk_level = "moderate"
            if risk_score <= 3:
                risk_level = "low"
            elif risk_score >= 8:
                risk_level = "high"
            
            # Calculate rough financial impact of environmental risks
            financial_impact = {
                "estimated_insurance_premium_impact": self._estimate_environmental_insurance_impact(identified_risks),
                "estimated_remediation_costs": self._estimate_remediation_costs(identified_risks, property_data),
                "impact_timeframe": "1-5 years"
            }
            
            return {
                "environmental_risks": {
                    "risk_level": risk_level,
                    "risk_score": min(10, max(1, risk_score)),
                    "identified_risks": identified_risks,
                    "financial_impact": financial_impact,
                    "data_source": "Derived from geographic and property age analysis"
                }
            }
                
        except Exception as e:
            logger.error(f"Error assessing environmental risks: {e}")
            return {
                "environmental_risks": {
                    "error": f"Failed to assess environmental risks: {str(e)}",
                    "risk_level": "unknown",
                    "risk_score": 5
                }
            }
    
    def _get_environmental_risk_mitigation(self, risk_type: str) -> List[str]:
        """Get mitigation options for a specific environmental risk."""
        mitigation_options = {
            "Earthquake risk": [
                "Conduct seismic risk assessment",
                "Implement structural reinforcements",
                "Obtain earthquake insurance coverage"
            ],
            "Flooding risk": [
                "Obtain flood insurance coverage",
                "Implement flood barriers and pumps",
                "Elevate critical building systems"
            ],
            "Hurricane risk": [
                "Install impact-resistant windows and doors",
                "Reinforce roof structures",
                "Develop evacuation and emergency plans"
            ],
            "Tornado risk": [
                "Create safe areas or storm shelters",
                "Reinforce structures",
                "Develop emergency response plans"
            ],
            "Wildfire risk": [
                "Create defensible space around the property",
                "Use fire-resistant building materials",
                "Develop evacuation plans"
            ],
            "Potential asbestos-containing materials": [
                "Conduct asbestos inspection",
                "Implement encapsulation or removal by licensed contractors",
                "Develop asbestos management plan"
            ],
            "Potential lead-based paint": [
                "Conduct lead paint inspection",
                "Implement abatement or encapsulation",
                "Regular monitoring and maintenance"
            ],
            "Potential underground storage tanks": [
                "Conduct tank scan and leak testing",
                "Remove or properly maintain tanks",
                "Obtain pollution liability insurance"
            ]
        }
        
        # Generic mitigation options for risks not in our dictionary
        generic_options = [
            "Conduct specific risk assessment",
            "Consult with environmental specialists",
            "Obtain appropriate insurance coverage"
        ]
        
        # Check for partial matches in risk_type
        for known_risk, options in mitigation_options.items():
            if known_risk in risk_type:
                return options
                
        return generic_options
    
    def _estimate_environmental_insurance_impact(self, identified_risks: List[Dict[str, Any]]) -> float:
        """Estimate the impact on insurance premiums from environmental risks."""
        base_increase = 0.0
        
        # Each high severity risk adds to premium
        for risk in identified_risks:
            if risk.get("severity") == "high":
                if "flood" in risk.get("type", "").lower():
                    base_increase += 2000
                elif "earthquake" in risk.get("type", "").lower():
                    base_increase += 1800
                elif "wildfire" in risk.get("type", "").lower():
                    base_increase += 1500
                elif "hurricane" in risk.get("type", "").lower():
                    base_increase += 1700
                elif "asbestos" in risk.get("type", "").lower() or "lead" in risk.get("type", "").lower():
                    base_increase += 1000
                else:
                    base_increase += 500
            elif risk.get("severity") == "moderate":
                base_increase += 300
        
        return base_increase
    
    def _estimate_remediation_costs(self, identified_risks: List[Dict[str, Any]], property_data: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate remediation costs for identified environmental risks."""
        # Extract property details
        units = property_data.get("units", 1)
        square_feet = property_data.get("square_feet", 0)
        
        # If we don't have square feet but have units, estimate
        if square_feet == 0 and units > 0:
            square_feet = units * 1000  # Rough estimate: 1000 sq ft per unit
        
        # If we still don't have square feet, use a fallback
        if square_feet == 0:
            square_feet = 10000  # Reasonable fallback for small property
        
        remediation_costs = {
            "low_estimate": 0,
            "high_estimate": 0,
            "major_cost_drivers": []
        }
        
        # Calculate costs based on risks
        for risk in identified_risks:
            risk_type = risk.get("type", "").lower()
            
            if "asbestos" in risk_type:
                # Asbestos costs scale with property size
                low_cost = square_feet * 15  # $15 per sq ft for minimal remediation
                high_cost = square_feet * 30  # $30 per sq ft for full remediation
                remediation_costs["low_estimate"] += low_cost
                remediation_costs["high_estimate"] += high_cost
                remediation_costs["major_cost_drivers"].append("Asbestos remediation")
                
            elif "lead" in risk_type:
                # Lead paint costs scale with property size
                low_cost = square_feet * 10  # $10 per sq ft for encapsulation
                high_cost = square_feet * 20  # $20 per sq ft for removal
                remediation_costs["low_estimate"] += low_cost
                remediation_costs["high_estimate"] += high_cost
                remediation_costs["major_cost_drivers"].append("Lead paint remediation")
                
            elif "storage tank" in risk_type:
                # Underground storage tank costs are per tank
                remediation_costs["low_estimate"] += 10000  # $10k for testing and minor remediation
                remediation_costs["high_estimate"] += 50000  # $50k if major leak found
                remediation_costs["major_cost_drivers"].append("Underground storage tank removal/remediation")
                
            elif "flood" in risk_type:
                # Flood mitigation costs
                low_cost = square_feet * 2  # $2 per sq ft for basic mitigation
                high_cost = square_feet * 5  # $5 per sq ft for extensive mitigation
                remediation_costs["low_estimate"] += low_cost
                remediation_costs["high_estimate"] += high_cost
                remediation_costs["major_cost_drivers"].append("Flood mitigation measures")
                
            elif "earthquake" in risk_type:
                # Earthquake retrofitting costs
                low_cost = square_feet * 5  # $5 per sq ft for basic retrofitting
                high_cost = square_feet * 15  # $15 per sq ft for extensive retrofitting
                remediation_costs["low_estimate"] += low_cost
                remediation_costs["high_estimate"] += high_cost
                remediation_costs["major_cost_drivers"].append("Seismic retrofitting")
                
            elif "wildfire" in risk_type:
                # Wildfire mitigation costs
                low_cost = square_feet * 1  # $1 per sq ft for basic protection
                high_cost = square_feet * 3  # $3 per sq ft for extensive protection
                remediation_costs["low_estimate"] += low_cost
                remediation_costs["high_estimate"] += high_cost
                remediation_costs["major_cost_drivers"].append("Wildfire protection measures")
        
        # Round and format costs
        remediation_costs["low_estimate"] = round(remediation_costs["low_estimate"], -3)  # Round to nearest 1000
        remediation_costs["high_estimate"] = round(remediation_costs["high_estimate"], -3)  # Round to nearest 1000
        
        # Remove duplicates in major cost drivers
        remediation_costs["major_cost_drivers"] = list(set(remediation_costs["major_cost_drivers"]))
        
        return remediation_costs
    
    async def _assess_market_risks(self, property_data: Dict[str, Any], additional_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Assess market risks for a property.
        
        Args:
            property_data: Property details
            additional_data: Optional additional data from other enrichers
            
        Returns:
            Dictionary of market risks
        """
        try:
            # Extract relevant property details
            city = property_data.get("city", "")
            state = property_data.get("state", "")
            property_type = property_data.get("property_type", "multifamily")
            
            # Use market data from other enrichers if available
            market_data = {}
            if additional_data and "market_analysis" in additional_data:
                market_data = additional_data["market_analysis"]
            
            # Placeholder for real market data API
            # In production, this would call a market data API
            
            # Define common market risk factors
            market_risk_factors = [
                {
                    "factor": "Market saturation",
                    "risk_level": "moderate",
                    "description": "Level of new construction and competition in the market area",
                    "data_point": market_data.get("new_construction_units", "Unknown")
                },
                {
                    "factor": "Rental growth trends",
                    "risk_level": "low" if state in ["FL", "TX", "AZ", "GA", "NC"] else "moderate",
                    "description": "Historical and projected rent growth in the market",
                    "data_point": market_data.get("projected_rent_growth", "3-5% annually (estimated)")
                },
                {
                    "factor": "Employment diversity",
                    "risk_level": self._assess_employment_diversity_risk(city, state),
                    "description": "Diversity of employment sectors in the market",
                    "data_point": market_data.get("employment_diversity", "Unknown")
                },
                {
                    "factor": "Population growth",
                    "risk_level": "low" if state in ["FL", "TX", "AZ", "GA", "NC", "CO", "UT", "ID", "NV"] else "moderate",
                    "description": "Population growth trends in the market",
                    "data_point": market_data.get("population_growth", "1-2% annually (estimated)")
                },
                {
                    "factor": "Affordability ratio",
                    "risk_level": "high" if state in ["CA", "NY", "MA", "HI", "WA"] else "moderate",
                    "description": "Ratio of housing costs to average incomes",
                    "data_point": market_data.get("affordability_ratio", "Unknown")
                }
            ]
            
            # Assess location-specific risks
            local_market_issues = self._assess_local_market_issues(city, state, property_type)
            
            # Calculate overall market risk score
            risk_score = 5  # Start at medium risk
            risk_level_scores = {"low": -1, "moderate": 0, "high": 1, "very high": 2}
            
            for factor in market_risk_factors:
                risk_score += risk_level_scores.get(factor["risk_level"], 0)
            
            # Adjust for local issues
            if len(local_market_issues) >= 3:
                risk_score += 2
            elif len(local_market_issues) >= 1:
                risk_score += 1
            
            # Determine overall risk level
            risk_level = "moderate"
            if risk_score <= 3:
                risk_level = "low"
            elif risk_score >= 8:
                risk_level = "high"
            
            # Suggest market risk mitigation strategies
            mitigation_strategies = self._suggest_market_risk_mitigations(market_risk_factors, local_market_issues)
            
            return {
                "market_risks": {
                    "risk_level": risk_level,
                    "risk_score": min(10, max(1, risk_score)),
                    "risk_factors": market_risk_factors,
                    "local_market_issues": local_market_issues,
                    "mitigation_strategies": mitigation_strategies,
                    "data_source": "Derived from market trend analysis and location assessment"
                }
            }
                
        except Exception as e:
            logger.error(f"Error assessing market risks: {e}")
            return {
                "market_risks": {
                    "error": f"Failed to assess market risks: {str(e)}",
                    "risk_level": "unknown",
                    "risk_score": 5
                }
            }
    
    def _assess_employment_diversity_risk(self, city: str, state: str) -> str:
        """Assess the employment diversity risk for a market."""
        # High-risk markets with concentrated employment sectors
        high_risk_markets = [
            ("Detroit", "MI"),  # Automotive concentration
            ("Houston", "TX"),  # Oil & gas concentration
            ("San Jose", "CA"),  # Tech concentration
            ("Las Vegas", "NV"),  # Tourism concentration
            ("Orlando", "FL"),  # Tourism concentration
            ("Pittsburgh", "PA"),  # Manufacturing concentration
        ]
        
        # Medium-risk markets with moderate employment concentration
        medium_risk_markets = [
            ("Seattle", "WA"),  # Tech and aerospace
            ("San Francisco", "CA"),  # Tech and finance
            ("Nashville", "TN"),  # Healthcare and music
            ("Miami", "FL"),  # Tourism and real estate
            ("Phoenix", "AZ"),  # Construction and tourism
        ]
        
        # Low-risk markets with diverse employment bases
        low_risk_markets = [
            ("New York", "NY"),
            ("Los Angeles", "CA"),
            ("Chicago", "IL"),
            ("Dallas", "TX"),
            ("Atlanta", "GA"),
            ("Washington", "DC"),
            ("Boston", "MA"),
            ("Philadelphia", "PA"),
        ]
        
        # Check for market in our reference lists
        if (city, state) in high_risk_markets:
            return "high"
        elif (city, state) in medium_risk_markets:
            return "moderate"
        elif (city, state) in low_risk_markets:
            return "low"
        
        # Default risk level based on city size (proxy for employment diversity)
        major_cities = ["New York", "Los Angeles", "Chicago", "Houston", "Phoenix", "Philadelphia", 
                      "San Antonio", "San Diego", "Dallas", "Austin", "Jacksonville", "San Jose", 
                      "Fort Worth", "Columbus", "Charlotte", "Indianapolis", "San Francisco", 
                      "Seattle", "Denver", "Washington", "Boston", "El Paso", "Nashville", 
                      "Oklahoma City", "Portland", "Las Vegas", "Memphis", "Louisville", "Baltimore", 
                      "Milwaukee", "Albuquerque", "Tucson", "Sacramento", "Atlanta", "Kansas City"]
        
        mid_sized_cities = ["Omaha", "Raleigh", "Miami", "Cleveland", "Tulsa", "Oakland", "Minneapolis", 
                          "Wichita", "Arlington", "Bakersfield", "Tampa", "Aurora", "New Orleans", 
                          "Cleveland", "Pittsburgh", "Cincinnati", "St. Louis", "Riverside", "Buffalo", 
                          "Lexington", "Richmond", "Corpus Christi", "Anchorage", "Stockton"]
        
        if city in major_cities:
            return "low"
        elif city in mid_sized_cities:
            return "moderate"
        else:
            return "moderate"  # Default to moderate risk for unknown cities
    
    def _assess_local_market_issues(self, city: str, state: str, property_type: str) -> List[Dict[str, str]]:
        """Assess specific local market issues for a location and property type."""
        local_issues = []
        
        # Check for known market-specific issues
        
        # Oversupply issues in specific markets
        oversupply_markets = {
            "multifamily": [
                ("Austin", "TX"),
                ("Nashville", "TN"),
                ("Denver", "CO"),
                ("Charlotte", "NC"),
                ("Orlando", "FL")
            ],
            "office": [
                ("San Francisco", "CA"),
                ("New York", "NY"),
                ("Seattle", "WA"),
                ("Chicago", "IL")
            ],
            "retail": [
                ("Anywhere", "Any")  # Retail generally facing oversupply issues nationally
            ]
        }
        
        # Markets with significant economic concerns
        economic_concern_markets = [
            ("Detroit", "MI"),
            ("Cleveland", "OH"),
            ("Birmingham", "AL"),
            ("St. Louis", "MO"),
            ("Buffalo", "NY")
        ]
        
        # Markets with regulatory challenges
        regulatory_challenge_markets = {
            "multifamily": [
                ("New York", "NY"),  # Rent control
                ("San Francisco", "CA"),  # Rent control
                ("Los Angeles", "CA"),  # Rent control
                ("Portland", "OR"),  # Tenant protections
                ("Seattle", "WA")  # Tenant protections
            ]
        }
        
        # Check for oversupply
        if property_type in oversupply_markets:
            for market_city, market_state in oversupply_markets[property_type]:
                if (market_city == "Anywhere" or city == market_city) and (market_state == "Any" or state == market_state):
                    local_issues.append({
                        "issue": "Market oversupply",
                        "description": f"Potential oversupply of {property_type} properties in this market",
                        "severity": "moderate"
                    })
        
        # Check for economic concerns
        for market_city, market_state in economic_concern_markets:
            if city == market_city and state == market_state:
                local_issues.append({
                    "issue": "Economic challenges",
                    "description": "Market area faces economic challenges including slow job growth",
                    "severity": "high"
                })
        
        # Check for regulatory challenges
        if property_type in regulatory_challenge_markets:
            for market_city, market_state in regulatory_challenge_markets[property_type]:
                if city == market_city and state == market_state:
                    local_issues.append({
                        "issue": "Regulatory challenges",
                        "description": f"Market has significant regulatory challenges for {property_type} properties",
                        "severity": "high"
                    })
        
        # Default risk for states with declining population
        declining_population_states = ["WV", "IL", "MS", "AK", "LA", "CT", "HI"]
        if state in declining_population_states:
            local_issues.append({
                "issue": "Population decline",
                "description": "State experiencing population decline, which may impact property values",
                "severity": "moderate" 
            })
        
        return local_issues
    
    def _suggest_market_risk_mitigations(self, risk_factors: List[Dict[str, Any]], local_issues: List[Dict[str, Any]]) -> List[str]:
        """Suggest strategies to mitigate identified market risks."""
        mitigation_strategies = []
        
        # Check risk factors
        high_risk_factors = [factor for factor in risk_factors if factor["risk_level"] in ["high", "very high"]]
        for factor in high_risk_factors:
            if factor["factor"] == "Market saturation":
                mitigation_strategies.append("Differentiate the property through unique amenities, finishes, or services")
                mitigation_strategies.append("Consider a value-add strategy to stand out from newer competition")
            
            elif factor["factor"] == "Rental growth trends":
                mitigation_strategies.append("Structure longer-term leases with built-in escalations")
                mitigation_strategies.append("Focus on expense reduction to maintain NOI in slow-growth environment")
            
            elif factor["factor"] == "Employment diversity":
                mitigation_strategies.append("Target tenant base from multiple industries")
                mitigation_strategies.append("Consider a more conservative underwriting approach")
                mitigation_strategies.append("Plan for higher vacancy reserves")
            
            elif factor["factor"] == "Population growth":
                mitigation_strategies.append("Focus on property improvements that appeal to long-term residents")
                mitigation_strategies.append("Consider exit strategy timing carefully")
            
            elif factor["factor"] == "Affordability ratio":
                mitigation_strategies.append("Explore affordable housing programs or incentives")
                mitigation_strategies.append("Consider unit layouts and sizes that maximize affordability")
        
        # Check local issues
        for issue in local_issues:
            if issue["issue"] == "Market oversupply":
                mitigation_strategies.append("Focus on tenant retention strategies to minimize turnover")
                mitigation_strategies.append("Budget for increased marketing and concessions")
            
            elif issue["issue"] == "Economic challenges":
                mitigation_strategies.append("Structure more conservative exit cap rates")
                mitigation_strategies.append("Build higher reserves for extended vacancy periods")
            
            elif issue["issue"] == "Regulatory challenges":
                mitigation_strategies.append("Budget for compliance costs with local regulations")
                mitigation_strategies.append("Consult with local landlord associations or legal experts")
                mitigation_strategies.append("Consider property management with expertise in navigating local regulations")
            
            elif issue["issue"] == "Population decline":
                mitigation_strategies.append("Target resilient submarkets within the broader area")
                mitigation_strategies.append("Consider shorter hold periods or alternative exit strategies")
        
        # General mitigation strategies
        general_strategies = [
            "Diversify the tenant base to reduce concentration risk",
            "Build enhanced operating reserves for market downturns",
            "Consider more conservative underwriting assumptions",
            "Develop multiple exit strategies based on market conditions"
        ]
        
        # Add general strategies if we don't have enough specific ones
        if len(mitigation_strategies) < 3:
            mitigation_strategies.extend(general_strategies)
        
        # Remove duplicates and return
        return list(set(mitigation_strategies))
    
    async def _assess_legal_regulatory_risks(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess legal and regulatory risks for a property.
        
        Args:
            property_data: Property details
            
        Returns:
            Dictionary of legal and regulatory risks
        """
        try:
            # Extract relevant property details
            address = property_data.get("address", "")
            city = property_data.get("city", "")
            state = property_data.get("state", "")
            property_type = property_data.get("property_type", "multifamily")
            year_built = property_data.get("year_built")
            
            # Rent control and tenant protection laws by location
            rent_control_locations = [
                ("New York", "NY"),
                ("San Francisco", "CA"),
                ("Los Angeles", "CA"),
                ("Oakland", "CA"),
                ("Berkeley", "CA"),
                ("Washington", "DC"),
                ("Newark", "NJ"),
                ("Portland", "OR"),
                ("Jersey City", "NJ")
            ]
            
            # Locations with strong tenant protections but not traditional rent control
            tenant_protection_locations = [
                ("Seattle", "WA"),
                ("Boston", "MA"),
                ("Chicago", "IL"),
                ("Minneapolis", "MN"),
                ("St. Paul", "MN"),
                ("Philadelphia", "PA"),
                ("San Jose", "CA"),
                ("Boulder", "CO"),
                ("Baltimore", "MD")
            ]
            
            # Identify risks
            legal_risks = []
            risk_score = 5  # Start at medium risk
            
            # Check for rent control
            has_rent_control = False
            for rcity, rstate in rent_control_locations:
                if city == rcity and state == rstate:
                    legal_risks.append({
                        "risk": "Rent control",
                        "description": "Property is subject to rent control ordinances limiting rent increases",
                        "severity": "high",
                        "impact": "Restricted ability to increase rents to market rates"
                    })
                    has_rent_control = True
                    risk_score += 2
                    break
            
            # Check for tenant protections
            has_tenant_protections = False
            if not has_rent_control:  # Only check if not already flagged for rent control
                for tcity, tstate in tenant_protection_locations:
                    if city == tcity and state == tstate:
                        legal_risks.append({
                            "risk": "Strong tenant protections",
                            "description": "Location has significant tenant protection laws",
                            "severity": "moderate",
                            "impact": "May face challenges with problem tenant situations"
                        })
                        has_tenant_protections = True
                        risk_score += 1
                        break
            
            # ADA compliance risk for older properties
            if year_built and year_built < 1992 and property_type not in ["single-family", "duplex"]:
                legal_risks.append({
                    "risk": "ADA compliance",
                    "description": "Property built before ADA requirements, may need accessibility upgrades",
                    "severity": "moderate",
                    "impact": "Potential retrofit costs or liability for non-compliance"
                })
                risk_score += 1
            
            # State-specific landlord-tenant laws
            tenant_friendly_states = ["CA", "NY", "NJ", "MA", "MD", "CT", "OR", "WA", "IL", "DC"]
            landlord_friendly_states = ["TX", "GA", "AL", "NC", "SC", "TN", "IN", "AZ", "CO", "FL"]
            
            if state in tenant_friendly_states and not (has_rent_control or has_tenant_protections):
                legal_risks.append({
                    "risk": "Tenant-friendly state laws",
                    "description": "State generally has laws favoring tenant rights",
                    "severity": "moderate",
                    "impact": "May face challenges with evictions and tenant disputes"
                })
                risk_score += 1
            elif state in landlord_friendly_states:
                # Actually reduces risk
                legal_risks.append({
                    "risk": "Landlord-friendly state laws",
                    "description": "State generally has laws favoring landlord rights",
                    "severity": "low",
                    "impact": "Favorable environment for property operations"
                })
                risk_score -= 1
            
            # Environmental compliance for older properties
            if year_built and year_built < 1980:
                legal_risks.append({
                    "risk": "Environmental compliance",
                    "description": "Older property may have asbestos, lead paint, or other regulated materials",
                    "severity": "moderate",
                    "impact": "Potential remediation costs and disclosure requirements"
                })
                risk_score += 1
            
            # Determine overall legal risk level
            risk_level = "moderate"
            if risk_score <= 3:
                risk_level = "low"
            elif risk_score >= 8:
                risk_level = "high"
            
            # Suggest legal risk mitigation strategies
            mitigation_strategies = self._suggest_legal_risk_mitigations(legal_risks)
            
            return {
                "legal_regulatory_risks": {
                    "risk_level": risk_level,
                    "risk_score": min(10, max(1, risk_score)),
                    "identified_risks": legal_risks,
                    "mitigation_strategies": mitigation_strategies,
                    "data_source": "Derived from location-based regulatory analysis"
                }
            }
                
        except Exception as e:
            logger.error(f"Error assessing legal/regulatory risks: {e}")
            return {
                "legal_regulatory_risks": {
                    "error": f"Failed to assess legal/regulatory risks: {str(e)}",
                    "risk_level": "unknown",
                    "risk_score": 5
                }
            }
    
    def _suggest_legal_risk_mitigations(self, legal_risks: List[Dict[str, Any]]) -> List[str]:
        """Suggest strategies to mitigate identified legal risks."""
        mitigation_strategies = []
        
        for risk in legal_risks:
            risk_type = risk.get("risk", "")
            
            if "Rent control" in risk_type:
                mitigation_strategies.extend([
                    "Consult with an attorney specializing in local rent control ordinances",
                    "Develop a system to track and document all allowable rent increases",
                    "Budget for lower annual rent growth in financial projections",
                    "Create value through non-rent revenue sources (laundry, storage, etc.)"
                ])
            
            elif "tenant protection" in risk_type.lower():
                mitigation_strategies.extend([
                    "Implement thorough tenant screening procedures",
                    "Develop clear, documented property rules and lease terms",
                    "Consider using a property management company familiar with local regulations",
                    "Maintain detailed records of all tenant communications and maintenance requests"
                ])
            
            elif "ADA compliance" in risk_type:
                mitigation_strategies.extend([
                    "Conduct an ADA compliance audit with a qualified specialist",
                    "Develop a prioritized plan for accessibility improvements",
                    "Create a budget for ongoing compliance upgrades",
                    "Consider tax incentives available for ADA improvements"
                ])
            
            elif "Environmental compliance" in risk_type:
                mitigation_strategies.extend([
                    "Conduct environmental testing for asbestos, lead, and other hazards",
                    "Develop an environmental management plan for the property",
                    "Budget for any necessary remediation work",
                    "Ensure proper disclosures to tenants as required by law"
                ])
            
            elif "Tenant-friendly state laws" in risk_type:
                mitigation_strategies.extend([
                    "Ensure all leases and property policies comply with state laws",
                    "Consider more thorough tenant screening processes",
                    "Budget for potentially longer eviction timelines",
                    "Maintain properties to high standards to avoid tenant complaints"
                ])
        
        # Basic strategies that apply to all properties
        if not mitigation_strategies:
            mitigation_strategies = [
                "Conduct a legal compliance review of all property operations",
                "Ensure proper insurance coverage for legal liabilities",
                "Maintain detailed documentation of all property management activities",
                "Consult with local legal counsel familiar with property management law"
            ]
        
        # Remove duplicates
        return list(set(mitigation_strategies))
    
    async def _assess_tenant_risks(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Assess tenant-related risks for a property.
        
        Args:
            property_data: Property details
            
        Returns:
            Dictionary of tenant risks
        """
        try:
            # Extract relevant property details
            property_type = property_data.get("property_type", "multifamily")
            vacancy_rate = property_data.get("vacancy_rate")
            tenant_mix = property_data.get("tenant_mix", [])
            city = property_data.get("city", "")
            state = property_data.get("state", "")
            tenant_turnover = property_data.get("tenant_turnover")
            average_lease_length = property_data.get("average_lease_length")
            
            # Placeholder values if data not available
            if vacancy_rate is None:
                vacancy_rate = 0.05  # Assume 5% vacancy
            
            if not tenant_mix and property_type == "multifamily":
                tenant_mix = [{"type": "residential", "percentage": 100}]
            elif not tenant_mix and property_type in ["office", "retail", "mixed-use"]:
                tenant_mix = [{"type": property_type, "percentage": 100}]
                
            # Identify tenant risks
            tenant_risks = []
            risk_score = 5  # Start at medium risk
            
            # Assess vacancy risk
            if vacancy_rate > 0.1:  # High vacancy
                tenant_risks.append({
                    "risk": "High vacancy",
                    "description": f"Current vacancy rate of {vacancy_rate*100:.1f}% is above average",
                    "severity": "high" if vacancy_rate > 0.15 else "moderate",
                    "impact": "Reduced income and potential negative market perception"
                })
                risk_score += 2 if vacancy_rate > 0.15 else 1
            elif vacancy_rate < 0.02:  # Extremely low vacancy could signal underpricing
                tenant_risks.append({
                    "risk": "Abnormally low vacancy",
                    "description": f"Current vacancy rate of {vacancy_rate*100:.1f}% may indicate underpriced units",
                    "severity": "low",
                    "impact": "Potential missed revenue opportunity"
                })
                # No risk score impact as this is a revenue opportunity rather than risk
            
            # Assess tenant concentration risk for commercial properties
            if property_type in ["office", "retail", "industrial", "mixed-use"]:
                large_tenants = [tenant for tenant in tenant_mix if tenant.get("percentage", 0) > 20]
                if large_tenants:
                    tenant_risks.append({
                        "risk": "Tenant concentration",
                        "description": f"{len(large_tenants)} tenant(s) occupy >20% of the property each",
                        "severity": "high" if len(large_tenants) == 1 else "moderate",
                        "impact": "Significant income loss if a major tenant vacates"
                    })
                    risk_score += 2 if len(large_tenants) == 1 else 1
            
            # Assess lease expiration risk
            if average_lease_length is not None:
                if average_lease_length < 12 and property_type != "multifamily":  # Short lease for commercial
                    tenant_risks.append({
                        "risk": "Short average lease term",
                        "description": f"Average lease length of {average_lease_length} months is short for this property type",
                        "severity": "moderate",
                        "impact": "Increased turnover costs and income volatility"
                    })
                    risk_score += 1
            
            # Assess turnover risk
            if tenant_turnover is not None:
                if tenant_turnover > 0.25:  # Over 25% annual turnover
                    tenant_risks.append({
                        "risk": "High tenant turnover",
                        "description": f"Annual turnover rate of {tenant_turnover*100:.1f}% is above average",
                        "severity": "high" if tenant_turnover > 0.4 else "moderate",
                        "impact": "Increased vacancy and make-ready costs"
                    })
                    risk_score += 2 if tenant_turnover > 0.4 else 1
            
            # Assess market-specific tenant risks
            # Cities with declining population - tenant acquisition risk
            declining_pop_cities = [
                ("Detroit", "MI"),
                ("Cleveland", "OH"),
                ("Buffalo", "NY"),
                ("St. Louis", "MO"),
                ("Toledo", "OH"),
                ("Pittsburgh", "PA")
            ]
            
            for dcity, dstate in declining_pop_cities:
                if city == dcity and state == dstate:
                    tenant_risks.append({
                        "risk": "Declining population base",
                        "description": "Market area has experienced population decline, affecting tenant pool",
                        "severity": "moderate",
                        "impact": "May face challenges filling vacancies"
                    })
                    risk_score += 1
                    break
            
            # Determine overall tenant risk level
            risk_level = "moderate"
            if risk_score <= 3:
                risk_level = "low"
            elif risk_score >= 8:
                risk_level = "high"
            
            # Calculate financial impact of tenant risks
            financial_impact = self._calculate_tenant_risk_financial_impact(property_data, tenant_risks)
            
            # Suggest tenant risk mitigation strategies
            mitigation_strategies = self._suggest_tenant_risk_mitigations(tenant_risks)
            
            return {
                "tenant_risks": {
                    "risk_level": risk_level,
                    "risk_score": min(10, max(1, risk_score)),
                    "identified_risks": tenant_risks,
                    "financial_impact": financial_impact,
                    "mitigation_strategies": mitigation_strategies,
                    "data_source": "Derived from tenant data and market analysis"
                }
            }
                
        except Exception as e:
            logger.error(f"Error assessing tenant risks: {e}")
            return {
                "tenant_risks": {
                    "error": f"Failed to assess tenant risks: {str(e)}",
                    "risk_level": "unknown",
                    "risk_score": 5
                }
            }
    
    def _calculate_tenant_risk_financial_impact(self, property_data: Dict[str, Any], 
                                               tenant_risks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate the financial impact of identified tenant risks."""
        # Extract financial data
        noi = property_data.get("noi")
        units = property_data.get("units", 1)
        avg_rent = property_data.get("average_rent")
        property_type = property_data.get("property_type", "multifamily")
        
        # If we don't have NOI or avg_rent, make a rough estimate
        if noi is None and avg_rent is not None and units:
            # Rough NOI estimate: annual rent * units * 0.6 (accounting for expenses)
            noi = avg_rent * 12 * units * 0.6
        
        # If we still don't have NOI, use a placeholder
        if noi is None:
            noi = units * 12000  # $12k NOI per unit placeholder
        
        financial_impact = {
            "annual_income_at_risk": 0,
            "increased_operating_costs": 0,
            "total_financial_exposure": 0
        }
        
        # Calculate financial impact based on risk types
        for risk in tenant_risks:
            risk_type = risk.get("risk", "")
            severity = risk.get("severity", "moderate")
            severity_factor = 0.15 if severity == "high" else 0.08 if severity == "moderate" else 0.03
            
            if "vacancy" in risk_type.lower():
                # High vacancy directly impacts income
                financial_impact["annual_income_at_risk"] += noi * severity_factor
            elif "turnover" in risk_type.lower():
                # High turnover impacts both income (vacancy during turnover) and costs
                financial_impact["annual_income_at_risk"] += noi * severity_factor * 0.5
                financial_impact["increased_operating_costs"] += units * 500 * severity_factor  # $500 per unit at risk
            elif "concentration" in risk_type.lower():
                # Tenant concentration puts a portion of income at higher risk
                financial_impact["annual_income_at_risk"] += noi * severity_factor * 2
            elif "declining population" in risk_type.lower():
                # Long-term risk to both income and property value
                financial_impact["annual_income_at_risk"] += noi * severity_factor
            elif "Short average lease" in risk_type:
                # Shorter leases increase turnover costs
                financial_impact["increased_operating_costs"] += units * 300 * severity_factor
        
        # Calculate total exposure
        financial_impact["total_financial_exposure"] = (
            financial_impact["annual_income_at_risk"] + 
            financial_impact["increased_operating_costs"]
        )
        
        # Round values for readability
        for key in financial_impact:
            financial_impact[key] = round(financial_impact[key], 2)
        
        return financial_impact
    
    def _suggest_tenant_risk_mitigations(self, tenant_risks: List[Dict[str, Any]]) -> List[str]:
        """Suggest strategies to mitigate identified tenant risks."""
        mitigation_strategies = []
        
        for risk in tenant_risks:
            risk_type = risk.get("risk", "")
            
            if "vacancy" in risk_type.lower():
                mitigation_strategies.extend([
                    "Implement a targeted marketing strategy for vacant units",
                    "Consider offering limited-time rental incentives",
                    "Evaluate current rental rates compared to market",
                    "Upgrade unit finishes or amenities to attract tenants"
                ])
            
            elif "turnover" in risk_type.lower():
                mitigation_strategies.extend([
                    "Develop a tenant retention program with renewal incentives",
                    "Improve property management responsiveness to tenant needs",
                    "Conduct exit interviews to identify improvement opportunities",
                    "Consider longer lease terms with built-in renewal options"
                ])
            
            elif "concentration" in risk_type.lower():
                mitigation_strategies.extend([
                    "Diversify tenant mix when opportunities arise",
                    "Stagger lease expirations to reduce simultaneous vacancy risk",
                    "Build stronger relationships with major tenants",
                    "Consider tenant credit enhancement options like letters of credit"
                ])
            
            elif "declining population" in risk_type.lower():
                mitigation_strategies.extend([
                    "Focus marketing on stable demographic segments",
                    "Consider repositioning to attract tenants from stronger market areas",
                    "Evaluate property for alternative uses or tenant types",
                    "Build a larger marketing budget into property operations"
                ])
            
            elif "Short average lease" in risk_type:
                mitigation_strategies.extend([
                    "Offer incentives for longer lease terms",
                    "Develop a streamlined renewal process to encourage staying",
                    "Create a tenant loyalty program with increasing benefits",
                    "Budget for more frequent turnover costs"
                ])
        
        # Basic strategies that apply to all properties
        if not mitigation_strategies:
            mitigation_strategies = [
                "Implement thorough tenant screening procedures",
                "Develop a tenant satisfaction program",
                "Ensure timely response to maintenance requests",
                "Regularly evaluate rental rates against market"
            ]
        
        # Remove duplicates
        return list(set(mitigation_strategies))
    
    def _calculate_overall_risk_score(self, risk_assessment: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate overall risk score based on all assessed risk categories."""
        # Risk categories and their weights
        risk_categories = [
            {"name": "physical_risks", "weight": 0.2},
            {"name": "environmental_risks", "weight": 0.15},
            {"name": "financial_risks", "weight": 0.25},
            {"name": "market_risks", "weight": 0.15},
            {"name": "legal_regulatory_risks", "weight": 0.15},
            {"name": "tenant_risks", "weight": 0.1}
        ]
        
        weighted_sum = 0
        total_weight = 0
        category_scores = []
        
        # Extract scores from each risk category
        for category in risk_categories:
            category_name = category["name"]
            if category_name in risk_assessment:
                risk_score = risk_assessment[category_name].get("risk_score")
                if risk_score is not None:
                    weight = category["weight"]
                    weighted_sum += risk_score * weight
                    total_weight += weight
                    category_scores.append({
                        "category": category_name.replace("_", " ").title(),
                        "score": risk_score,
                        "weight": weight
                    })
        
        # Calculate overall weighted score
        overall_score = 5  # Default to medium risk
        if total_weight > 0:
            overall_score = weighted_sum / total_weight
        
        # Determine the overall risk level
        risk_level = "moderate"
        if overall_score <= 3.5:
            risk_level = "low"
        elif overall_score >= 7.0:
            risk_level = "high"
        
        # Identify highest risk categories
        sorted_scores = sorted(category_scores, key=lambda x: x["score"], reverse=True)
        highest_risk_categories = [item["category"] for item in sorted_scores[:2] if item["score"] >= 7]
        
        return {
            "overall_score": round(overall_score, 1),
            "risk_level": risk_level,
            "category_scores": category_scores,
            "highest_risk_categories": highest_risk_categories,
            "score_interpretation": "On a scale of 1-10, where 10 is highest risk"
        }
    
    # Additional methods for the RiskAssessor class
    
    def assess_insurance_requirements(self, property_data: Dict[str, Any],
                                risk_assessment: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Assess insurance requirements based on property characteristics and identified risks.
        
        Args:
            property_data: Property details
            risk_assessment: Optional existing risk assessment
            
        Returns:
            Dictionary of insurance recommendations
        """
        try:
            # Extract relevant property details
            property_type = property_data.get("property_type", "multifamily")
            city = property_data.get("city", "")
            state = property_data.get("state", "")
            units = property_data.get("units", 0)
            year_built = property_data.get("year_built")
            
            # Base insurance requirements
            insurance_requirements = [
                {
                    "type": "Property Insurance",
                    "coverage_level": "Full Replacement Value",
                    "description": "Covers physical damage to the property from fire, storms, and other perils",
                    "estimated_annual_cost": self._estimate_property_insurance(property_data)
                },
                {
                    "type": "Liability Insurance",
                    "coverage_level": f"${min(5, max(1, units // 20))}M",
                    "description": "Covers legal and medical expenses if someone is injured on the property",
                    "estimated_annual_cost": self._estimate_liability_insurance(property_data)
                }
            ]
            
            # Consider additional insurance based on risks
            if risk_assessment:
                # Flood insurance
                if "environmental_risks" in risk_assessment:
                    env_risks = risk_assessment["environmental_risks"]
                    for risk in env_risks.get("identified_risks", []):
                        if "flood" in risk.get("type", "").lower():
                            insurance_requirements.append({
                                "type": "Flood Insurance",
                                "coverage_level": "Building Replacement Cost",
                                "description": "Covers damage caused by flooding, which is typically excluded from standard property insurance",
                                "estimated_annual_cost": self._estimate_flood_insurance(property_data)
                            })
                        elif "seismic" in risk.get("type", "").lower() or "earthquake" in risk.get("type", "").lower():
                            insurance_requirements.append({
                                "type": "Earthquake Insurance",
                                "coverage_level": "Building Replacement Cost",
                                "description": "Covers damage caused by earthquakes, which is typically excluded from standard property insurance",
                                "estimated_annual_cost": self._estimate_earthquake_insurance(property_data)
                            })
            
            # Add loss of income insurance for all income properties
            insurance_requirements.append({
                "type": "Loss of Income/Business Interruption",
                "coverage_level": "12 Months Rental Income",
                "description": "Covers lost income if the property becomes uninhabitable due to a covered peril",
                "estimated_annual_cost": self._estimate_loss_of_income_insurance(property_data)
            })
            
            # Calculate total annual premium estimate
            total_annual_premium = sum(ins.get("estimated_annual_cost", 0) for ins in insurance_requirements)
            
            return {
                "insurance_requirements": {
                    "recommended_policies": insurance_requirements,
                    "total_estimated_annual_premium": total_annual_premium,
                    "key_exclusions_to_review": [
                        "Flood damage (if no flood insurance)",
                        "Earthquake damage (if no earthquake insurance)",
                        "Mold and environmental contamination",
                        "Terrorism coverage",
                        "Vacancy clauses"
                    ],
                    "data_source": "Based on property characteristics and risk profile"
                }
            }
                
        except Exception as e:
            logger.error(f"Error assessing insurance requirements: {e}")
            return {
                "insurance_requirements": {
                    "error": f"Failed to assess insurance requirements: {str(e)}",
                    "recommended_policies": []
                }
            }
    
    def _estimate_property_insurance(self, property_data: Dict[str, Any]) -> float:
        """Estimate annual property insurance premium."""
        # Extract relevant property details
        property_type = property_data.get("property_type", "multifamily")
        units = property_data.get("units", 1)
        square_feet = property_data.get("square_feet", 0)
        current_value = property_data.get("current_value")
        state = property_data.get("state", "")
        
        # Base premium per $1000 of value
        base_rates = {
            "multifamily": 3.50,
            "office": 3.00,
            "retail": 3.25,
            "industrial": 2.75,
            "mixed-use": 3.75
        }
        
        # State adjustments (higher for disaster-prone states)
        state_adjustments = {
            "FL": 1.5,  # Hurricane risk
            "CA": 1.3,  # Wildfire and earthquake risk
            "TX": 1.2,  # Hurricane and tornado risk
            "OK": 1.2,  # Tornado risk
            "LA": 1.4,  # Hurricane and flood risk
            "AL": 1.2,  # Hurricane risk
            "MS": 1.2,  # Hurricane risk
            "KS": 1.15  # Tornado risk
        }
        
        # Estimate building value if not provided
        if not current_value:
            if square_feet > 0:
                # Rough replacement cost per square foot
                sq_ft_costs = {
                    "multifamily": 150,
                    "office": 200,
                    "retail": 175,
                    "industrial": 100,
                    "mixed-use": 180
                }
                current_value = square_feet * sq_ft_costs.get(property_type, 150)
            elif units > 0:
                # Rough value per unit
                current_value = units * 150000  # $150k per unit as fallback
            else:
                # Completely unknown, use placeholder
                current_value = 1000000  # $1M as absolute fallback
        
        # Calculate base premium
        base_rate = base_rates.get(property_type, 3.50)
        state_adj = state_adjustments.get(state, 1.0)
        
        # Premium = (Value / 1000) * Rate * State Adjustment
        premium = (current_value / 1000) * base_rate * state_adj
        
        return round(premium, 2)
    
    def _estimate_liability_insurance(self, property_data: Dict[str, Any]) -> float:
        """Estimate annual liability insurance premium."""
        # Extract relevant property details
        property_type = property_data.get("property_type", "multifamily")
        units = property_data.get("units", 1)
        square_feet = property_data.get("square_feet", 0)
        
        # Base premium per unit or per 1000 sq ft
        if property_type == "multifamily":
            # Cost per unit
            return max(1000, units * 35)  # Minimum $1000, otherwise $35 per unit
        else:
            # Cost per 1000 square feet for commercial
            if square_feet > 0:
                return max(1500, (square_feet / 1000) * 40)  # Minimum $1500
            else:
                return 2000  # Default if no square footage data
            
    def _estimate_flood_insurance(self, property_data: Dict[str, Any]) -> float:
        """Estimate annual flood insurance premium."""
        # Very rough estimation - actual flood insurance varies greatly by flood zone
        state = property_data.get("state", "")
        units = property_data.get("units", 1)
        
        # Higher rates for flood-prone states
        high_risk_states = ["FL", "LA", "TX", "MS", "AL", "SC", "NC", "NJ"]
        base_cost = 2500 if state in high_risk_states else 1200
        
        # Scale based on property size
        if units <= 4:
            return base_cost
        elif units <= 20:
            return base_cost * 1.5
        else:
            return base_cost * 2.0
    
    def _estimate_earthquake_insurance(self, property_data: Dict[str, Any]) -> float:
        """Estimate annual earthquake insurance premium."""
        state = property_data.get("state", "")
        current_value = property_data.get("current_value")
        
        # Higher rates for seismic states
        high_risk_states = ["CA", "WA", "OR", "NV", "HI", "AK", "UT"]
        medium_risk_states = ["ID", "MT", "WY", "CO", "MO", "IL", "TN", "KY", "SC"]
        
        if state in high_risk_states:
            rate_per_1000 = 3.0
        elif state in medium_risk_states:
            rate_per_1000 = 1.5
        else:
            rate_per_1000 = 0.75
        
        # Estimate building value if not provided
        if not current_value:
            units = property_data.get("units", 1)
            current_value = units * 150000  # $150k per unit as fallback
        
        # Premium = (Value / 1000) * Rate
        premium = (current_value / 1000) * rate_per_1000
        
        return round(max(1200, premium), 2)  # Minimum $1200
    
    def _estimate_loss_of_income_insurance(self, property_data: Dict[str, Any]) -> float:
        """Estimate annual loss of income insurance premium."""
        # Usually about 10-15% of property insurance
        property_premium = self._estimate_property_insurance(property_data)
        return round(property_premium * 0.12, 2)  # 12% of property premium
    
    def analyze_investment_risk_vs_reward(self, property_data: Dict[str, Any], 
                                    risk_assessment: Dict[str, Any],
                                    investment_metrics: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyze the risk vs. reward profile of the investment.
        
        Args:
            property_data: Property details
            risk_assessment: Existing risk assessment
            investment_metrics: Optional investment metrics
            
        Returns:
            Dictionary of risk vs. reward analysis
        """
        try:
            # Extract relevant metrics
            overall_risk = risk_assessment.get("overall_risk_score", {})
            risk_score = overall_risk.get("overall_score", 5)
            
            # Extract investment metrics if available
            cap_rate = None
            irr = None
            cash_on_cash = None
            roi = None
            
            if investment_metrics:
                cap_rate = investment_metrics.get("cap_rate")
                irr = investment_metrics.get("projected_irr")
                cash_on_cash = investment_metrics.get("cash_on_cash")
                roi = investment_metrics.get("five_year_roi")
            
            # Use property data if metrics not found
            if cap_rate is None:
                cap_rate = property_data.get("cap_rate")
            
            # Use placeholder values if still not available
            if cap_rate is None:
                cap_rate = 5.5  # National average cap rate
            if irr is None:
                irr = 12.0  # Typical target IRR
            if cash_on_cash is None:
                cash_on_cash = 7.0  # Typical target cash on cash
            if roi is None:
                roi = 40.0  # Typical 5-year ROI
            
            # Calculate risk-adjusted returns
            risk_factor = risk_score / 5.0  # Convert to a 1-2 scale (5 is average)
            
            risk_adjusted_metrics = {
                "risk_adjusted_cap_rate": round(cap_rate / risk_factor, 2),
                "risk_adjusted_irr": round(irr / risk_factor, 2),
                "risk_adjusted_cash_on_cash": round(cash_on_cash / risk_factor, 2)
            }
            
            # Evaluate the risk/reward profile
            if risk_score <= 3.5:  # Low risk
                if cap_rate >= 6.0:
                    profile = "Ideal - Low risk with strong returns"
                elif cap_rate >= 4.5:
                    profile = "Conservative - Low risk with moderate returns"
                else:
                    profile = "Preservation - Low risk but minimal returns"
            elif risk_score <= 6.5:  # Moderate risk
                if cap_rate >= 7.0:
                    profile = "Attractive - Moderate risk with strong returns"
                elif cap_rate >= 5.0:
                    profile = "Balanced - Moderate risk with moderate returns"
                else:
                    profile = "Questionable - Moderate risk with below-average returns"
            else:  # High risk
                if cap_rate >= 8.0:
                    profile = "Opportunistic - High risk with high potential returns"
                else:
                    profile = "Unfavorable - High risk without compensating returns"
            
            # Calculate risk premium (additional return demanded for risk)
            # Base cap rate for "risk-free" property investment ~ 4%
            risk_premium = cap_rate - 4.0
            
            # Required risk premium based on risk score
            required_premium = (risk_score - 5) * 0.5 + 1.5  # 1.5% at score=5, +0.5% per point above
            
            # Risk/reward assessment
            if risk_premium >= required_premium:
                assessment = "Favorable - Returns adequately compensate for risk"
            elif risk_premium >= required_premium * 0.7:
                assessment = "Acceptable - Returns mostly compensate for risk"
            else:
                assessment = "Unfavorable - Returns don't adequately compensate for risk"
            
            return {
                "risk_reward_analysis": {
                    "risk_score": risk_score,
                    "return_metrics": {
                        "cap_rate": cap_rate,
                        "projected_irr": irr,
                        "cash_on_cash": cash_on_cash,
                        "five_year_roi": roi
                    },
                    "risk_adjusted_metrics": risk_adjusted_metrics,
                    "risk_premium": round(risk_premium, 2),
                    "required_risk_premium": round(required_premium, 2),
                    "risk_reward_profile": profile,
                    "risk_reward_assessment": assessment,
                    "risk_mitigation_impact": self._analyze_risk_mitigation_impact(risk_assessment, cap_rate)
                }
            }
                
        except Exception as e:
            logger.error(f"Error analyzing risk vs. reward: {e}")
            return {
                "risk_reward_analysis": {
                    "error": f"Failed to analyze risk vs. reward: {str(e)}",
                    "risk_reward_profile": "Unknown"
                }
            }
    
    def _analyze_risk_mitigation_impact(self, risk_assessment: Dict[str, Any], 
                                   cap_rate: float) -> Dict[str, Any]:
        """Analyze the impact of risk mitigation on returns."""
        try:
            # Extract risk categories
            risk_categories = [
                "physical_risks",
                "environmental_risks",
                "financial_risks",
                "market_risks",
                "legal_regulatory_risks",
                "tenant_risks"
            ]
            
            # Collect mitigation opportunities
            mitigation_opportunities = []
            
            for category in risk_categories:
                if category in risk_assessment:
                    category_data = risk_assessment[category]
                    if category_data.get("risk_score", 0) >= 6:
                        # High risk categories offer greater mitigation potential
                        
                        # Readable category name
                        readable_category = category.replace("_", " ").replace("risks", "risk")
                        
                        # Potential improvement based on risk score
                        potential_improvement = (category_data.get("risk_score", 5) - 5) * 0.1
                        
                        # Impact on returns
                        cap_rate_impact = round(potential_improvement * 0.5, 2)
                        irr_impact = round(potential_improvement * 1.5, 2)
                        
                        mitigation_opportunities.append({
                            "risk_category": readable_category,
                            "current_risk_score": category_data.get("risk_score", 5),
                            "mitigation_potential": "high" if category_data.get("risk_score", 5) >= 8 else "moderate",
                            "potential_revised_score": max(3, category_data.get("risk_score", 5) - 2),
                            "cap_rate_impact": cap_rate_impact,
                            "irr_impact": irr_impact,
                            "suggested_actions": self._get_mitigation_actions(category)
                        })
            
            # Calculate aggregate impact
            if mitigation_opportunities:
                total_cap_rate_impact = sum(m["cap_rate_impact"] for m in mitigation_opportunities)
                total_irr_impact = sum(m["irr_impact"] for m in mitigation_opportunities)
                
                mitigated_cap_rate = cap_rate + total_cap_rate_impact
                
                return {
                    "total_cap_rate_impact": round(total_cap_rate_impact, 2),
                    "total_irr_impact": round(total_irr_impact, 2),
                    "mitigated_cap_rate": round(mitigated_cap_rate, 2),
                    "roi_improvement": f"{round(total_cap_rate_impact * 100 / cap_rate, 1)}%",
                    "mitigation_opportunities": mitigation_opportunities
                }
            else:
                return {
                    "total_cap_rate_impact": 0,
                    "total_irr_impact": 0,
                    "mitigated_cap_rate": cap_rate,
                    "roi_improvement": "0%",
                    "mitigation_opportunities": []
                }
                
        except Exception as e:
            logger.error(f"Error analyzing risk mitigation impact: {e}")
            return {
                "total_cap_rate_impact": 0,
                "mitigation_opportunities": []
            }
    
    def _suggest_risk_recommendations(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate recommended actions based on the risk assessment."""
        recommendations = []
        
        # Extract risk categories with high risk levels
        high_risk_categories = []
        for category in ["physical_risks", "environmental_risks", "financial_risks", 
                        "market_risks", "legal_regulatory_risks", "tenant_risks"]:
            if category in risk_assessment and risk_assessment[category].get("risk_level") == "high":
                high_risk_categories.append(category)
        
        # Get recommendations for high risk categories
        for category in high_risk_categories:
            category_recommendations = self._get_mitigation_actions(category)
            if category_recommendations:
                # Add top 2 recommendations from each high risk category
                recommendations.extend(category_recommendations[:2])
        
        # If we don't have enough high risk categories, add some from moderate risk ones
        if len(recommendations) < 3:
            moderate_risk_categories = []
            for category in ["physical_risks", "environmental_risks", "financial_risks", 
                            "market_risks", "legal_regulatory_risks", "tenant_risks"]:
                if category in risk_assessment and risk_assessment[category].get("risk_level") == "moderate":
                    moderate_risk_categories.append(category)
            
            for category in moderate_risk_categories:
                if len(recommendations) >= 5:  # Cap at 5 recommendations
                    break
                Category_recommendations = self._get_mitigation_actions(category)
                if Category_recommendations:
                    recommendations.append(Category_recommendations[0])  # Just add the top recommendation
        
        # Add general recommendation if we still don't have enough
        if not recommendations:
            recommendations = [
                "Conduct thorough due diligence before acquisition",
                "Consider implementing preventative maintenance programs",
                "Establish adequate operational reserves"
            ]
        
        # Remove duplicates and return
        return list(dict.fromkeys(recommendations))  # Preserves order while removing duplicates
    
    def _get_mitigation_actions(self, risk_category: str) -> List[str]:
        """Get specific mitigation actions for a risk category."""
        mitigation_actions = {
            "physical_risks": [
                "Conduct thorough pre-purchase inspections",
                "Develop a capital improvement plan addressing major systems",
                "Establish preventative maintenance programs",
                "Increase maintenance reserves"
            ],
            "environmental_risks": [
                "Complete Phase I and potentially Phase II Environmental Site Assessments",
                "Obtain environmental insurance coverage",
                "Implement remediation plans for identified issues",
                "Conduct regular environmental monitoring"
            ],
            "financial_risks": [
                "Secure long-term, fixed-rate financing",
                "Increase operating reserves",
                "Implement strict expense controls",
                "Diversify tenant base to reduce revenue concentration"
            ],
            "market_risks": [
                "Ensure flexibility in exit strategy",
                "Diversify portfolio across multiple markets",
                "Focus on properties with multiple potential uses",
                "Implement value-add strategies to differentiate from competition"
            ],
            "legal_regulatory_risks": [
                "Conduct thorough legal due diligence with specialized counsel",
                "Obtain proper permits and ensure zoning compliance",
                "Maintain robust compliance documentation",
                "Establish relationships with local regulatory authorities"
            ],
            "tenant_risks": [
                "Enhance tenant screening procedures",
                "Implement tenant retention programs",
                "Diversify tenant mix and lease expiration schedule",
                "Develop contingency plans for major tenant departures"
            ]
        }
        
        return mitigation_actions.get(risk_category, [
            "Conduct additional due diligence",
            "Consult with relevant specialists",
            "Implement risk management strategies"
        ])