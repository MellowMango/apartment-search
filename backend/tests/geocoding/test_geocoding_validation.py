#!/usr/bin/env python3
"""
Geocoding Validation Tests

This module provides comprehensive validation tests for the geocoding system.
It ensures that:
1. Coordinates are correctly assigned to properties
2. Coordinates are within valid ranges and close to the actual property location
3. No suspicious patterns exist in the geocoded data
4. The system can handle edge cases properly

The tests can be run manually or as part of an automated schedule.
"""

import os
import sys
import asyncio
import logging
import argparse
import json
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional
from math import radians, sin, cos, sqrt, atan2

# Add root directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Import required modules
from backend.data_enrichment.database_extensions import EnrichmentDatabaseOps
from backend.data_enrichment.geocoding_service import GeocodingService
from backend.data_enrichment.cache_manager import ResearchCacheManager
from backend.data_enrichment.property_researcher import PropertyResearcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("geocoding_validation.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("geocoding_validation")

class GeocodingValidator:
    """
    Validator for geocoding results.
    
    This class provides methods to validate geocoded properties and
    identify potential issues with the geocoding system.
    """
    
    def __init__(self):
        """Initialize the geocoding validator."""
        self.cache_manager = ResearchCacheManager()
        self.db_ops = EnrichmentDatabaseOps()
        self.geocoder = GeocodingService(cache_manager=self.cache_manager)
        self.researcher = PropertyResearcher(
            cache_manager=self.cache_manager,
            db_ops=self.db_ops,
            geocoding_service=self.geocoder
        )
        logger.info("Geocoding validator initialized")
    
    async def validate_property_coordinates(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate a property's coordinates using multiple methods.
        
        Args:
            property_data: Property data dictionary
            
        Returns:
            Dictionary with validation results
        """
        validation_result = {
            "property_id": property_data.get("id"),
            "address": property_data.get("address"),
            "city": property_data.get("city"),
            "state": property_data.get("state"),
            "existing_coordinates": {
                "latitude": property_data.get("latitude"),
                "longitude": property_data.get("longitude")
            },
            "tests": {},
            "passed_all_tests": True
        }
        
        # Test 1: Check if coordinates exist
        has_coords = property_data.get("latitude") is not None and property_data.get("longitude") is not None
        validation_result["tests"]["has_coordinates"] = has_coords
        
        if not has_coords:
            validation_result["passed_all_tests"] = False
            return validation_result
        
        # Test 2: Check if coordinates are in valid ranges
        try:
            lat = float(property_data.get("latitude"))
            lng = float(property_data.get("longitude"))
            valid_range = (-90 <= lat <= 90) and (-180 <= lng <= 180) and not (lat == 0 and lng == 0)
            validation_result["tests"]["valid_coordinate_range"] = valid_range
            
            if not valid_range:
                validation_result["passed_all_tests"] = False
        except (ValueError, TypeError):
            validation_result["tests"]["valid_coordinate_range"] = False
            validation_result["passed_all_tests"] = False
            return validation_result
        
        # Test 3: Re-geocode the property and check if coordinates are similar
        try:
            # Create a copy of property data without coordinates to force fresh geocoding
            property_copy = property_data.copy()
            property_copy.pop("latitude", None)
            property_copy.pop("longitude", None)
            
            # Get new coordinates
            geocode_result = await self.geocoder.geocode_address(
                address=property_data.get("address", ""),
                city=property_data.get("city", ""),
                state=property_data.get("state", ""),
                zip_code=property_data.get("zip_code", ""),
                use_cache=False  # Force fresh geocoding
            )
            
            # Record new coordinates
            validation_result["fresh_coordinates"] = {
                "latitude": geocode_result.get("latitude"),
                "longitude": geocode_result.get("longitude"),
                "provider": geocode_result.get("geocoding_provider")
            }
            
            # Calculate distance between existing and new coordinates
            if geocode_result.get("latitude") and geocode_result.get("longitude"):
                distance_km = self.calculate_distance(
                    lat1=lat,
                    lon1=lng,
                    lat2=float(geocode_result.get("latitude")),
                    lon2=float(geocode_result.get("longitude"))
                )
                
                validation_result["tests"]["coordinates_distance_km"] = distance_km
                
                # Check if coordinates are close enough (within 1 km)
                validation_result["tests"]["coordinates_match"] = distance_km < 1.0
                
                if distance_km >= 1.0:
                    validation_result["passed_all_tests"] = False
            else:
                validation_result["tests"]["coordinates_match"] = False
                validation_result["passed_all_tests"] = False
        
        except Exception as e:
            logger.error(f"Error re-geocoding property {property_data.get('id')}: {e}")
            validation_result["tests"]["geocoding_error"] = str(e)
            validation_result["passed_all_tests"] = False
        
        # Test 4: Check for suspicious patterns
        suspicious_result = await self.check_suspicious_patterns(property_data)
        validation_result["tests"]["suspicious_patterns"] = suspicious_result
        
        if suspicious_result.get("is_suspicious"):
            validation_result["passed_all_tests"] = False
        
        return validation_result
    
    async def check_suspicious_patterns(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check for suspicious patterns in geocoded data.
        
        Args:
            property_data: Property data dictionary
            
        Returns:
            Dictionary with suspicious pattern check results
        """
        result = {
            "is_suspicious": False,
            "suspicious_patterns": []
        }
        
        # Get coordinates
        try:
            lat = float(property_data.get("latitude"))
            lng = float(property_data.get("longitude"))
        except (ValueError, TypeError):
            result["is_suspicious"] = True
            result["suspicious_patterns"].append("invalid_coordinates")
            return result
        
        # Check 1: Default city coordinates
        # Many geocoding services return city center coordinates if they can't find exact address
        
        # Check for Austin area coordinates on non-Austin properties
        is_austin_area = (30.1 <= lat <= 30.5) and (-97.9 <= lng <= -97.6)
        
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        
        if is_austin_area:
            # Clean up city name if it has "Location:" prefix
            if city and city.startswith("Location:"):
                city = city.replace("Location:", "").strip()
            
            # Check if property is actually in Austin area
            is_austin_property = False
            if city:
                city_lower = city.lower()
                austin_keywords = ["austin", "round rock", "cedar park", "pflugerville", "georgetown"]
                is_austin_property = any(keyword in city_lower for keyword in austin_keywords)
                
            # If it's showing Austin coordinates but property is not in Austin
            # and not in Texas at all, consider it suspicious
            if not is_austin_property and state and state.upper() != "TX":
                result["is_suspicious"] = True
                result["suspicious_patterns"].append("mismatched_city_coordinates_austin")
        
        # Check 2: Exact latitude/longitude values
        # Exact values like 35.0, -97.0 are often approximations
        if lat == round(lat) and lng == round(lng):
            result["is_suspicious"] = True
            result["suspicious_patterns"].append("exact_round_coordinates")
        
        # Check 3: Check for duplicate coordinates
        # If many properties share the exact same coordinates, they might be city/zip centroids
        try:
            if lat and lng:
                duplicate_query = """
                SELECT COUNT(*) FROM properties 
                WHERE latitude = $1 AND longitude = $2
                """
                duplicate_count = await self.db_ops.execute_raw_query(duplicate_query, [lat, lng])
                
                if duplicate_count and duplicate_count[0][0] > 3:  # If more than 3 properties share exact coordinates
                    result["is_suspicious"] = True
                    result["suspicious_patterns"].append(f"duplicate_coordinates_{duplicate_count[0][0]}")
        except Exception as e:
            logger.error(f"Error checking for duplicate coordinates: {e}")
        
        return result
    
    def calculate_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate the Haversine distance between two points in kilometers.
        
        Args:
            lat1: Latitude of point 1
            lon1: Longitude of point 1
            lat2: Latitude of point 2
            lon2: Longitude of point 2
            
        Returns:
            Distance in kilometers
        """
        # Radius of the Earth in kilometers
        R = 6371.0
        
        # Convert coordinates to radians
        lat1_rad = radians(lat1)
        lon1_rad = radians(lon1)
        lat2_rad = radians(lat2)
        lon2_rad = radians(lon2)
        
        # Differences
        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        
        # Haversine formula
        a = sin(dlat / 2)**2 + cos(lat1_rad) * cos(lat2_rad) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        distance = R * c
        
        return distance
    
    async def batch_validate_properties(self, limit: int = 100, 
                                       include_recently_verified: bool = False) -> Dict[str, Any]:
        """
        Validate multiple properties' geocoding.
        
        Args:
            limit: Maximum number of properties to validate
            include_recently_verified: Whether to include recently verified properties
            
        Returns:
            Dictionary with validation results and statistics
        """
        # Build query based on parameters
        if include_recently_verified:
            query = """
            SELECT id, address, city, state, zip_code, latitude, longitude, property_type, units, geocode_verified
            FROM properties
            WHERE address IS NOT NULL AND address != ''
            AND city IS NOT NULL AND city != ''
            AND state IS NOT NULL AND state != ''
            ORDER BY RANDOM()
            LIMIT $1
            """
        else:
            query = """
            SELECT id, address, city, state, zip_code, latitude, longitude, property_type, units, geocode_verified
            FROM properties
            WHERE address IS NOT NULL AND address != ''
            AND city IS NOT NULL AND city != ''
            AND state IS NOT NULL AND state != ''
            AND (geocode_verified IS NULL OR geocode_verified = false)
            ORDER BY RANDOM()
            LIMIT $1
            """
        
        properties = await self.db_ops.execute_raw_query(query, [limit])
        properties = [dict(p) for p in properties] if properties else []
        
        if not properties:
            return {
                "status": "success",
                "message": "No properties found for validation",
                "properties_count": 0,
                "results": []
            }
        
        # Validate each property
        validation_results = []
        
        for prop in properties:
            try:
                result = await self.validate_property_coordinates(prop)
                validation_results.append(result)
            except Exception as e:
                logger.error(f"Error validating property {prop.get('id')}: {e}")
                validation_results.append({
                    "property_id": prop.get("id"),
                    "error": str(e),
                    "passed_all_tests": False
                })
        
        # Calculate statistics
        passed_count = sum(1 for r in validation_results if r.get("passed_all_tests", False))
        failed_count = len(validation_results) - passed_count
        
        # Group failures by test type
        failure_types = {}
        for result in validation_results:
            if not result.get("passed_all_tests", False):
                for test_name, test_result in result.get("tests", {}).items():
                    if test_name == "suspicious_patterns" and test_result.get("is_suspicious"):
                        patterns = test_result.get("suspicious_patterns", [])
                        for pattern in patterns:
                            failure_types[pattern] = failure_types.get(pattern, 0) + 1
                    elif test_name != "suspicious_patterns" and test_result is False:
                        failure_types[test_name] = failure_types.get(test_name, 0) + 1
        
        return {
            "status": "completed",
            "timestamp": datetime.now().isoformat(),
            "properties_count": len(validation_results),
            "passed_count": passed_count,
            "failed_count": failed_count,
            "success_rate": (passed_count / len(validation_results)) * 100 if validation_results else 0,
            "failure_types": failure_types,
            "results": validation_results
        }
    
    async def write_report_to_database(self, validation_results: Dict[str, Any]) -> None:
        """
        Write validation results to the database.
        
        Args:
            validation_results: Results from batch validation
        """
        try:
            # Check if geocoding_validation_reports table exists
            check_table_query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'geocoding_validation_reports'
            )
            """
            
            table_exists = await self.db_ops.execute_raw_query(check_table_query)
            
            # Create table if it doesn't exist
            if not table_exists or not table_exists[0][0]:
                create_table_query = """
                CREATE TABLE geocoding_validation_reports (
                    id SERIAL PRIMARY KEY,
                    report_date TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                    properties_count INTEGER,
                    passed_count INTEGER,
                    failed_count INTEGER,
                    success_rate NUMERIC,
                    failure_types JSONB,
                    full_report JSONB
                );
                """
                await self.db_ops.execute_raw_query(create_table_query)
                logger.info("Created geocoding_validation_reports table")
            
            # Insert report
            insert_query = """
            INSERT INTO geocoding_validation_reports 
            (report_date, properties_count, passed_count, failed_count, success_rate, failure_types, full_report)
            VALUES (NOW(), $1, $2, $3, $4, $5, $6)
            RETURNING id;
            """
            
            report_id = await self.db_ops.execute_raw_query(
                insert_query, 
                [
                    validation_results.get("properties_count", 0),
                    validation_results.get("passed_count", 0),
                    validation_results.get("failed_count", 0),
                    validation_results.get("success_rate", 0),
                    json.dumps(validation_results.get("failure_types", {})),
                    json.dumps(validation_results)
                ]
            )
            
            logger.info(f"Saved validation report to database with ID {report_id[0][0] if report_id else 'unknown'}")
            
        except Exception as e:
            logger.error(f"Error writing validation report to database: {e}")


async def main():
    """Run geocoding validation tests."""
    parser = argparse.ArgumentParser(description="Geocoding Validation Tests")
    parser.add_argument("--limit", type=int, default=100, help="Number of properties to validate")
    parser.add_argument("--include-verified", action="store_true", help="Include recently verified properties")
    parser.add_argument("--output", type=str, default="geocoding_validation_report.json", help="Output file for full report")
    parser.add_argument("--save-to-db", action="store_true", help="Save report to database")
    args = parser.parse_args()
    
    logger.info(f"Starting geocoding validation with limit={args.limit}")
    
    validator = GeocodingValidator()
    
    try:
        # Run batch validation
        results = await validator.batch_validate_properties(
            limit=args.limit,
            include_recently_verified=args.include_verified
        )
        
        # Print summary to console
        print(f"Validation completed: {results['passed_count']}/{results['properties_count']} passed ({results['success_rate']:.2f}%)")
        
        if results.get("failure_types"):
            print("\nFailure types:")
            for failure_type, count in results.get("failure_types", {}).items():
                print(f"  - {failure_type}: {count}")
        
        # Save full report to file
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Saved full report to {args.output}")
        
        # Save to database if requested
        if args.save_to_db:
            await validator.write_report_to_database(results)
        
        return results
        
    except Exception as e:
        logger.error(f"Error during geocoding validation: {e}")
        return {"status": "error", "error": str(e)}
    finally:
        # Close database connections
        await validator.db_ops.close()


if __name__ == "__main__":
    asyncio.run(main()) 