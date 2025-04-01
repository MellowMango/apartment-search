#!/usr/bin/env python3
"""
Run All Collectors Demo

This script demonstrates how to use the new architecture to run multiple
collectors and compare the results. It provides a convenient way to test
the entire collection layer.
"""

import asyncio
import logging
import os
import sys
import json
from datetime import datetime
from typing import Dict, Any, List

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

# Import collectors
from backend.scrapers.brokers.cbre.collector import CBRECollector
from backend.scrapers.brokers.acrmultifamily.collector import ACRMultifamilyCollector
from backend.scrapers.brokers.cbredealflow.collector import CBREDealFlowCollector
from backend.scrapers.brokers.multifamilygrp.collector import MultifamilyGroupCollector
from backend.scrapers.brokers.marcusmillichap.collector import MarcusMillichapCollector
from backend.scrapers.brokers.walkerdunlop.collector import WalkerDunlopCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("run_all_collectors")

# Define collector configurations
COLLECTORS = [
    {
        "name": "CBRE",
        "id": "cbre",
        "collector_class": CBRECollector,
        "params": {
            "multifamily_only": True,
            "max_items": 10,
            "save_to_disk": True,
            "save_to_db": False  # Set to True to save to database
        }
    },
    {
        "name": "ACR Multifamily",
        "id": "acrmultifamily",
        "collector_class": ACRMultifamilyCollector,
        "params": {
            "max_items": 10,
            "save_to_disk": True,
            "save_to_db": False
        }
    },
    {
        "name": "CBRE Deal Flow",
        "id": "cbredealflow",
        "collector_class": CBREDealFlowCollector,
        "params": {
            "use_auth": True,
            "max_items": 10,
            "save_to_disk": True,
            "save_to_db": False
        }
    },
    {
        "name": "Multifamily Group",
        "id": "multifamilygrp",
        "collector_class": MultifamilyGroupCollector,
        "params": {
            "max_items": 10,
            "save_to_disk": True,
            "save_to_db": False  # Set to True to save to database
        }
    },
    {
        "name": "Marcus & Millichap",
        "id": "marcusmillichap",
        "collector_class": MarcusMillichapCollector,
        "params": {
            "max_items": 10,
            "save_to_disk": True,
            "save_to_db": False  # Set to True to save to database
        }
    },
    {
        "name": "Walker & Dunlop",
        "id": "walkerdunlop",
        "collector_class": WalkerDunlopCollector,
        "params": {
            "max_items": 10,
            "save_to_disk": True,
            "save_to_db": False  # Set to True to save to database
        }
    }
]

async def run_collector(collector_config: Dict[str, Any]) -> Dict[str, Any]:
    """Run a single collector with the provided configuration."""
    name = collector_config["name"]
    source_id = collector_config["id"]
    params = collector_config["params"]
    
    logger.info(f"Running collector: {name}")
    
    try:
        # Initialize collector
        collector = collector_config["collector_class"]()
        
        # Validate source
        logger.info(f"Validating source: {source_id}")
        is_valid = await collector.validate_source(source_id)
        
        if not is_valid:
            logger.warning(f"Source validation failed for {name}")
            # Continue anyway for demo purposes
        
        # Collect data
        logger.info(f"Collecting data from {name} with params: {params}")
        result = await collector.collect_data(source_id, params)
        
        # Process result
        if result.success:
            properties = result.data.get("properties", [])
            logger.info(f"Successfully collected {len(properties)} properties from {name}")
            
            # Return summary
            return {
                "name": name,
                "source_id": source_id,
                "success": True,
                "property_count": len(properties),
                "time_taken": result.metadata.get("time_taken_seconds", "N/A"),
                "timestamp": result.metadata.get("timestamp", datetime.utcnow().isoformat())
            }
        else:
            logger.error(f"Failed to collect data from {name}: {result.error}")
            return {
                "name": name,
                "source_id": source_id,
                "success": False,
                "error": result.error,
                "timestamp": result.metadata.get("timestamp", datetime.utcnow().isoformat()) if result.metadata else datetime.utcnow().isoformat()
            }
    
    except Exception as e:
        logger.error(f"Error running collector {name}: {str(e)}")
        return {
            "name": name,
            "source_id": source_id,
            "success": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }

async def run_all_collectors():
    """Run all collectors and compare results."""
    logger.info("=== Running All Collectors Demo ===")
    
    # Run collectors
    tasks = []
    for collector_config in COLLECTORS:
        task = asyncio.create_task(run_collector(collector_config))
        tasks.append(task)
    
    # Wait for all collectors to complete
    results = await asyncio.gather(*tasks)
    
    # Print summary
    logger.info("\n=== Collection Results Summary ===")
    total_properties = 0
    successful_collectors = 0
    
    for result in results:
        status = "SUCCESS ✓" if result.get("success") else "FAILED ✗"
        name = result.get("name")
        
        if result.get("success"):
            property_count = result.get("property_count", 0)
            time_taken = result.get("time_taken", "N/A")
            logger.info(f"{name}: {status} - {property_count} properties in {time_taken}s")
            total_properties += property_count
            successful_collectors += 1
        else:
            error = result.get("error", "Unknown error")
            logger.info(f"{name}: {status} - Error: {error}")
    
    # Overall statistics
    logger.info("\n=== Overall Statistics ===")
    logger.info(f"Total collectors: {len(COLLECTORS)}")
    logger.info(f"Successful collectors: {successful_collectors}")
    logger.info(f"Total properties collected: {total_properties}")
    
    # Save results to a file
    output_file = os.path.join("test_output", f"collector_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_file}")
    return results

if __name__ == "__main__":
    asyncio.run(run_all_collectors())