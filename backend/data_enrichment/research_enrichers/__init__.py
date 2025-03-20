"""
Research Enrichers Package

This package provides specialized enrichers for deep property research,
focused on different domains of property analysis.
"""

from backend.data_enrichment.research_enrichers.investment_metrics import InvestmentMetricsEnricher
from backend.data_enrichment.research_enrichers.property_profiler import PropertyProfiler

# These will be imported as they are implemented:
# from backend.data_enrichment.research_enrichers.market_analyzer import MarketAnalyzer
# from backend.data_enrichment.research_enrichers.risk_assessor import RiskAssessor

__all__ = [
    'InvestmentMetricsEnricher',
    'PropertyProfiler',
    # 'MarketAnalyzer',
    # 'RiskAssessor',
]
