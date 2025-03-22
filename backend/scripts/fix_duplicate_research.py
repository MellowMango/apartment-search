#!/usr/bin/env python3
"""
Fix Duplicate Property Research Entries

This script:
1. Finds properties with duplicate research entries
2. Merges duplicate entries or keeps only the most recent one
3. Updates the property_research table accordingly

Usage:
    python fix_duplicate_research.py [--dry-run] [--limit 100]
    
Options:
    --dry-run: Only report duplicates without modifying the database
    --limit: Maximum number of properties to process
"""

import os
import sys
import asyncio
import logging
import argparse
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

# Add parent directory to path to allow imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import from backend modules
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fix_duplicate_research.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("fix_duplicate_research")

# Supabase setup
try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Supabase client not installed. Run: pip install supabase")
    sys.exit(1)

# Initialize Supabase client
def init_supabase() -> Optional[Client]:
    """Initialize Supabase client from environment variables."""
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    
    if not supabase_url or not supabase_key:
        logger.error("Supabase credentials not found in environment variables")
        return None
    
    try:
        supabase = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return None

async def find_duplicate_research(limit: int = 100) -> List[Dict[str, Any]]:
    """
    Find properties with duplicate research entries.
    
    Args:
        limit: Maximum number of properties to check
        
    Returns:
        List of properties with duplicate research entries
    """
    supabase = init_supabase()
    if not supabase:
        logger.error("Cannot continue without Supabase connection")
        return []
    
    try:
        # Get properties
        properties_result = supabase.table("properties").select("id").limit(limit).execute()
        properties = properties_result.data
        
        duplicates = []
        
        # Check each property for duplicate research entries
        for property_data in properties:
            property_id = property_data.get("id")
            if not property_id:
                continue
                
            # Get research entries for this property
            research_result = supabase.table("property_research").select("*").eq("property_id", property_id).execute()
            research_entries = research_result.data
            
            # Check if duplicates exist
            if len(research_entries) > 1:
                duplicates.append({
                    "property_id": property_id,
                    "research_entries": research_entries
                })
                
        return duplicates
        
    except Exception as e:
        logger.error(f"Error finding duplicate research entries: {str(e)}")
        return []

async def merge_research_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Merge multiple research entries into one.
    
    Strategy:
    1. Keep most recent executive_summary
    2. Merge all modules data
    3. Use most recent research_date
    4. Use deepest research_depth
    
    Args:
        entries: List of research entries to merge
        
    Returns:
        Merged research entry
    """
    if not entries:
        return {}
        
    if len(entries) == 1:
        return entries[0]
    
    # Sort by research_date descending
    sorted_entries = sorted(
        entries, 
        key=lambda e: e.get("research_date", "1970-01-01T00:00:00Z"),
        reverse=True
    )
    
    # Use newest entry as base
    merged = sorted_entries[0].copy()
    
    # Get deepest research depth
    depth_order = {"basic": 0, "standard": 1, "comprehensive": 2, "exhaustive": 3}
    merged["research_depth"] = max(
        [e.get("research_depth", "basic") for e in entries],
        key=lambda d: depth_order.get(d, 0)
    )
    
    # Merge modules
    merged_modules = merged.get("modules", {})
    for entry in sorted_entries[1:]:
        entry_modules = entry.get("modules", {})
        
        # For each module in this entry
        for module_name, module_data in entry_modules.items():
            # If module doesn't exist in merged entry, add it
            if module_name not in merged_modules:
                merged_modules[module_name] = module_data
            # If module exists, merge at deeper level
            elif isinstance(merged_modules[module_name], dict) and isinstance(module_data, dict):
                for key, value in module_data.items():
                    if key not in merged_modules[module_name]:
                        merged_modules[module_name][key] = value
    
    merged["modules"] = merged_modules
    merged["updated_at"] = datetime.now().isoformat()
    
    return merged

async def fix_duplicates(dry_run: bool = True, limit: int = 100) -> Dict[str, Any]:
    """
    Fix duplicate property research entries.
    
    Args:
        dry_run: Only report duplicates without modifying the database
        limit: Maximum number of properties to process
        
    Returns:
        Statistics about the fix process
    """
    supabase = init_supabase()
    if not supabase:
        logger.error("Cannot continue without Supabase connection")
        return {"status": "error", "message": "Cannot connect to Supabase"}
    
    # Find duplicates
    duplicates = await find_duplicate_research(limit)
    
    if not duplicates:
        logger.info("No duplicate research entries found")
        return {
            "status": "success", 
            "message": "No duplicate research entries found",
            "properties_checked": limit
        }
    
    logger.info(f"Found {len(duplicates)} properties with duplicate research entries")
    
    stats = {
        "properties_with_duplicates": len(duplicates),
        "entries_before": sum(len(d["research_entries"]) for d in duplicates),
        "entries_after": len(duplicates),  # One entry per property after fix
        "entries_removed": 0,
        "properties_fixed": 0
    }
    
    if dry_run:
        logger.info("Dry run mode - not modifying database")
        return {
            "status": "success",
            "message": "Dry run completed",
            "stats": stats,
            "duplicates": [
                {
                    "property_id": d["property_id"],
                    "entry_count": len(d["research_entries"])
                }
                for d in duplicates
            ]
        }
    
    # Fix duplicates
    for duplicate in duplicates:
        property_id = duplicate["property_id"]
        entries = duplicate["research_entries"]
        
        try:
            # Merge entries
            merged_entry = await merge_research_entries(entries)
            
            # Keep the first entry ID
            entry_id = entries[0]["id"]
            
            # Update this entry with merged data
            supabase.table("property_research").update(merged_entry).eq("id", entry_id).execute()
            
            # Delete other entries
            for entry in entries[1:]:
                supabase.table("property_research").delete().eq("id", entry["id"]).execute()
            
            stats["properties_fixed"] += 1
            stats["entries_removed"] += len(entries) - 1
            
            logger.info(f"Fixed duplicate entries for property {property_id}: merged {len(entries)} entries")
            
        except Exception as e:
            logger.error(f"Error fixing duplicates for property {property_id}: {str(e)}")
    
    return {
        "status": "success",
        "message": f"Fixed {stats['properties_fixed']} properties with duplicate research entries",
        "stats": stats
    }

async def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Fix duplicate property research entries")
    parser.add_argument("--dry-run", action="store_true", help="Only report duplicates without modifying the database")
    parser.add_argument("--limit", type=int, default=100, help="Maximum number of properties to process")
    args = parser.parse_args()
    
    # Run the fix operation
    result = await fix_duplicates(dry_run=args.dry_run, limit=args.limit)
    
    # Print results
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    asyncio.run(main()) 