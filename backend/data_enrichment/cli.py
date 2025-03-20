#!/usr/bin/env python3
# backend/data_enrichment/cli.py
import os
import sys
import json
import asyncio
import argparse
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='deep_research_cli.log'
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)
logger = logging.getLogger(__name__)

# Import required modules
from backend.data_enrichment.property_researcher import PropertyResearcher
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
from backend.data_enrichment.geocoding_service import GeocodingService
from backend.data_enrichment.cache_manager import ResearchCacheManager
from backend.data_enrichment.config import TEST_PROPERTIES

class DeepResearchCLI:
    """Command Line Interface for Property Deep Research operations."""
    
    def __init__(self):
        """Initialize the CLI with required services."""
        self.cache_manager = ResearchCacheManager()
        self.db_ops = EnrichmentDatabaseOps()
        self.geocoding_service = GeocodingService(cache_manager=self.cache_manager)
        self.researcher = PropertyResearcher(
            cache_manager=self.cache_manager,
            db_ops=self.db_ops,
            geocoding_service=self.geocoding_service
        )
    
    async def research_property(self, args):
        """Research a single property."""
        try:
            property_data = None
            
            # Load property data from database
            if args.property_id:
                logger.info(f"Loading property {args.property_id} from database")
                # TODO: Implement database lookup once schema is finalized
                # For now, use test data
                property_data = TEST_PROPERTIES[0].copy()
                property_data["id"] = args.property_id
            
            # Load property data from file
            elif args.input_file:
                logger.info(f"Loading property from file: {args.input_file}")
                with open(args.input_file, 'r') as f:
                    property_data = json.load(f)
            
            # Exit if no property data
            if not property_data:
                logger.error("No property data provided")
                print("Error: Please provide a property ID or input file")
                return
            
            # Research the property
            logger.info(f"Researching property {property_data.get('name', 'unknown')} at depth {args.depth}")
            
            # First geocode the property if needed
            if not self._has_valid_coordinates(property_data):
                logger.info("Property missing coordinates, geocoding first...")
                property_data = await self.researcher.geocode_property(property_data)
            
            # Then conduct deep research
            result = await self.researcher.research_property(
                property_data=property_data,
                research_depth=args.depth,
                force_refresh=args.force_refresh
            )
            
            # Output results
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Research results saved to {args.output_file}")
            else:
                # Print a brief summary
                print("\nResearch Summary:")
                print(f"Property: {property_data.get('name', 'Unknown')}")
                print(f"Address: {property_data.get('address', 'Unknown')}, "
                      f"{property_data.get('city', '')}, {property_data.get('state', '')}")
                print(f"Research Depth: {args.depth}")
                print(f"Coordinates: {property_data.get('latitude', 'Unknown')}, {property_data.get('longitude', 'Unknown')}")
                print("\nExecutive Summary:")
                print(result.get("executive_summary", "No executive summary available"))
                
                # Print module summary
                if "modules" in result:
                    print("\nModule Coverage:")
                    for module_name in result["modules"]:
                        module_data = result["modules"][module_name]
                        if isinstance(module_data, dict) and "error" in module_data:
                            print(f"  - {module_name}: ERROR - {module_data['error']}")
                        else:
                            print(f"  - {module_name}: OK")
                
        except Exception as e:
            logger.error(f"Error researching property: {e}")
            print(f"Error: {e}")
    
    async def batch_research_properties(self, args):
        """Research multiple properties in batch."""
        try:
            # Get properties from database
            logger.info(f"Loading up to {args.limit} properties from database")
            properties = await self.db_ops.get_properties_needing_research(
                limit=args.limit,
                research_depth=args.depth
            )
            
            if not properties:
                logger.warning("No properties found for research")
                print("No properties found that need research")
                return
            
            logger.info(f"Loaded {len(properties)} properties for batch research")
            print(f"Researching {len(properties)} properties at depth {args.depth}...")
            
            # Track progress
            processed = 0
            start_time = datetime.now()
            
            # Define progress callback
            async def progress_callback(completed, total, latest_result):
                nonlocal processed
                processed = completed
                print(f"Progress: {completed}/{total} properties processed ({(completed/total)*100:.1f}%)")
            
            # First batch geocode all properties that need coordinates
            properties_needing_geocoding = [p for p in properties if not self._has_valid_coordinates(p)]
            if properties_needing_geocoding:
                print(f"Geocoding {len(properties_needing_geocoding)} properties without coordinates...")
                geocoding_results = await self.researcher.batch_geocode_properties(
                    properties=properties_needing_geocoding,
                    concurrency=args.concurrency
                )
                
                # Update the properties list with geocoded properties
                geocoded_properties = {p.get("id"): p for p in geocoding_results["properties"]}
                for i, prop in enumerate(properties):
                    if prop.get("id") in geocoded_properties:
                        properties[i] = geocoded_properties[prop.get("id")]
                
                print(f"Geocoding complete. Success rate: {geocoding_results['stats']['success_rate']}%")
            
            # Now run research on all properties
            result = await self.researcher.batch_research_properties(
                properties=properties,
                research_depth=args.depth,
                concurrency=args.concurrency,
                force_refresh=args.force_refresh,
                on_progress=progress_callback
            )
            
            # Calculate duration
            duration = datetime.now() - start_time
            duration_seconds = duration.total_seconds()
            avg_time = duration_seconds / len(properties) if properties else 0
            
            # Print batch results
            print("\nBatch Research Complete!")
            print(f"Total properties: {len(properties)}")
            print(f"Success: {result['stats']['success']}")
            print(f"Errors: {result['stats']['errors']}")
            print(f"Success rate: {result['stats']['success_rate']}")
            print(f"Duration: {duration_seconds:.1f} seconds")
            print(f"Average time per property: {avg_time:.1f} seconds")
            
            # Save detailed results to file if requested
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Detailed results saved to {args.output_file}")
                
        except Exception as e:
            logger.error(f"Error in batch research: {e}")
            print(f"Error: {e}")
    
    async def geocode_property(self, args):
        """Geocode a single property."""
        try:
            property_data = None
            
            # Load property data from database
            if args.property_id:
                logger.info(f"Loading property {args.property_id} from database")
                # TODO: Implement database lookup once schema is finalized
                # For now, use test data
                property_data = TEST_PROPERTIES[0].copy()
                property_data["id"] = args.property_id
            
            # Load property data from file
            elif args.input_file:
                logger.info(f"Loading property from file: {args.input_file}")
                with open(args.input_file, 'r') as f:
                    property_data = json.load(f)
            
            # Exit if no property data
            if not property_data:
                logger.error("No property data provided")
                print("Error: Please provide a property ID or input file")
                return
            
            # Geocode the property
            logger.info(f"Geocoding property {property_data.get('name', 'unknown')}")
            
            # Geocode with specific provider if specified
            geocoded_property = await self.researcher.geocode_property(
                property_data=property_data,
                force_refresh=args.force_refresh
            )
            
            # Output results
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    json.dump(geocoded_property, f, indent=2)
                print(f"Geocoding results saved to {args.output_file}")
            else:
                # Print a brief summary
                print("\nGeocoding Results:")
                print(f"Property: {geocoded_property.get('name', 'Unknown')}")
                print(f"Address: {geocoded_property.get('address', 'Unknown')}, "
                      f"{geocoded_property.get('city', '')}, {geocoded_property.get('state', '')}")
                print(f"Coordinates: {geocoded_property.get('latitude', 'Unknown')}, {geocoded_property.get('longitude', 'Unknown')}")
                if "formatted_address" in geocoded_property:
                    print(f"Formatted Address: {geocoded_property.get('formatted_address')}")
                if "geocoding_provider" in geocoded_property:
                    print(f"Geocoding Provider: {geocoded_property.get('geocoding_provider')}")
                
        except Exception as e:
            logger.error(f"Error geocoding property: {e}")
            print(f"Error: {e}")
    
    async def batch_geocode_properties(self, args):
        """Geocode multiple properties in batch."""
        try:
            # Get properties from database
            logger.info(f"Loading up to {args.limit} properties from database")
            properties = await self.db_ops.get_properties_needing_research(
                limit=args.limit
            )
            
            if not properties:
                logger.warning("No properties found for geocoding")
                print("No properties found in the database")
                return
            
            # Filter properties that need geocoding
            if not args.force_refresh:
                properties_to_geocode = [p for p in properties if not self._has_valid_coordinates(p)]
                if not properties_to_geocode:
                    print("All properties already have valid coordinates")
                    return
                properties = properties_to_geocode
            
            logger.info(f"Geocoding {len(properties)} properties")
            print(f"Geocoding {len(properties)} properties...")
            
            # Track progress
            start_time = datetime.now()
            
            # Batch geocode properties
            result = await self.researcher.batch_geocode_properties(
                properties=properties,
                concurrency=args.concurrency,
                force_refresh=args.force_refresh
            )
            
            # Calculate duration
            duration = datetime.now() - start_time
            duration_seconds = duration.total_seconds()
            avg_time = duration_seconds / len(properties) if properties else 0
            
            # Print batch results
            print("\nBatch Geocoding Complete!")
            print(f"Total properties: {len(properties)}")
            print(f"Success: {result['stats']['success']}")
            print(f"Errors: {result['stats']['errors']}")
            print(f"Success rate: {result['stats']['success_rate']}%")
            print(f"Duration: {duration_seconds:.1f} seconds")
            print(f"Average time per property: {avg_time:.1f} seconds")
            
            # Save detailed results to file if requested
            if args.output_file:
                with open(args.output_file, 'w') as f:
                    json.dump(result, f, indent=2)
                print(f"Detailed results saved to {args.output_file}")
                
        except Exception as e:
            logger.error(f"Error in batch geocoding: {e}")
            print(f"Error: {e}")
    
    async def clear_cache(self, args):
        """Clear the research cache."""
        try:
            if args.all:
                self.cache_manager.clear_all()
                print("All cache cleared")
            elif args.type:
                self.cache_manager.clear_by_type(args.type)
                print(f"Cache cleared for type: {args.type}")
            else:
                print("Please specify --all or --type")
                
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            print(f"Error: {e}")
    
    async def run_scheduled_tasks(self, args):
        """Run scheduled research tasks manually."""
        from backend.data_enrichment.scheduled_tasks import (
            research_new_properties_task,
            refresh_outdated_research_task
        )
        
        try:
            if args.task == "all" or args.task == "new":
                print("Running task: research_new_properties_task")
                await research_new_properties_task()
                
            if args.task == "all" or args.task == "refresh":
                print("Running task: refresh_outdated_research_task")
                await refresh_outdated_research_task()
                
            print("Scheduled tasks complete")
                
        except Exception as e:
            logger.error(f"Error running scheduled tasks: {e}")
            print(f"Error: {e}")
    
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

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Property Deep Research CLI")
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Geocode a single property
    geocode_parser = subparsers.add_parser("geocode", help="Geocode a single property")
    geocode_parser.add_argument("--property-id", help="Property ID to geocode")
    geocode_parser.add_argument("--input-file", help="Input file with property data (JSON)")
    geocode_parser.add_argument("--output-file", help="Output file for geocoding results (JSON)")
    geocode_parser.add_argument("--provider", help="Geocoding provider (google, mapbox, nominatim)")
    geocode_parser.add_argument("--force-refresh", action="store_true", help="Force refresh any existing geocoding")
    
    # Batch geocode properties
    batch_geocode_parser = subparsers.add_parser("batch-geocode", help="Geocode multiple properties")
    batch_geocode_parser.add_argument("--limit", type=int, default=20, help="Maximum number of properties to geocode")
    batch_geocode_parser.add_argument("--concurrency", type=int, default=3, help="Maximum concurrent geocoding operations")
    batch_geocode_parser.add_argument("--output-file", help="Output file for geocoding results (JSON)")
    batch_geocode_parser.add_argument("--force-refresh", action="store_true", help="Force refresh any existing geocoding")
    
    # Research a single property
    research_parser = subparsers.add_parser("research", help="Research a single property")
    research_parser.add_argument("--property-id", help="Property ID to research")
    research_parser.add_argument("--input-file", help="Input file with property data (JSON)")
    research_parser.add_argument("--output-file", help="Output file for research results (JSON)")
    research_parser.add_argument("--depth", default="standard", 
                              choices=["basic", "standard", "comprehensive", "exhaustive"],
                              help="Research depth level")
    research_parser.add_argument("--force-refresh", action="store_true", help="Force refresh cached data")
    
    # Batch research properties
    batch_research_parser = subparsers.add_parser("batch-research", help="Research multiple properties")
    batch_research_parser.add_argument("--limit", type=int, default=10, help="Maximum number of properties to research")
    batch_research_parser.add_argument("--concurrency", type=int, default=3, help="Maximum concurrent research operations")
    batch_research_parser.add_argument("--depth", default="standard",
                                    choices=["basic", "standard", "comprehensive", "exhaustive"],
                                    help="Research depth level")
    batch_research_parser.add_argument("--output-file", help="Output file for research results (JSON)")
    batch_research_parser.add_argument("--force-refresh", action="store_true", help="Force refresh cached data")
    
    # Clear cache
    clear_cache_parser = subparsers.add_parser("clear-cache", help="Clear research cache")
    clear_cache_parser.add_argument("--all", action="store_true", help="Clear all cache")
    clear_cache_parser.add_argument("--type", help="Clear cache for specific type")
    
    # Run scheduled tasks
    scheduled_tasks_parser = subparsers.add_parser("run-scheduled-tasks", help="Run scheduled research tasks")
    scheduled_tasks_parser.add_argument("--task", default="all", choices=["all", "new", "refresh"],
                                     help="Specific task to run")
    
    return parser.parse_args()

async def main():
    """Main entry point for the CLI."""
    args = parse_args()
    cli = DeepResearchCLI()
    
    if args.command == "research":
        await cli.research_property(args)
    elif args.command == "batch-research":
        await cli.batch_research_properties(args)
    elif args.command == "geocode":
        await cli.geocode_property(args)
    elif args.command == "batch-geocode":
        await cli.batch_geocode_properties(args)
    elif args.command == "clear-cache":
        await cli.clear_cache(args)
    elif args.command == "run-scheduled-tasks":
        await cli.run_scheduled_tasks(args)
    else:
        print("Please specify a valid command")
        print("Use --help for more information")

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(main())