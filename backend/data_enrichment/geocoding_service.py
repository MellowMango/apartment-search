#!/usr/bin/env python3
"""
Geocoding Service for Property Data Enrichment

This module provides geocoding functionality to convert property addresses
to precise latitude and longitude coordinates for map integration.
"""

import os
import logging
import asyncio
import aiohttp
import random
import time
import hashlib
from typing import Dict, Any, List, Tuple, Optional, Union
from urllib.parse import quote

logger = logging.getLogger(__name__)

class GeocodingService:
    """
    Service for geocoding property addresses using various providers.
    
    Features:
    - Support for multiple geocoding providers (Google Maps, Mapbox, Nominatim)
    - Fallback mechanisms if primary provider fails
    - Rate limiting to avoid API quota issues
    - Caching to minimize duplicate requests
    - Batch geocoding capabilities
    """
    
    def __init__(self, cache_manager=None):
        """
        Initialize the geocoding service.
        
        Args:
            cache_manager: Cache manager for geocoding results (optional)
        """
        # API keys from environment variables
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
        self.mapbox_access_token = os.getenv("MAPBOX_ACCESS_TOKEN", "")
        self.nominatim_user_agent = os.getenv("NOMINATIM_USER_AGENT", "AcquireApartments/1.0")
        
        # Cache manager (will be injected if provided)
        self.cache_manager = cache_manager
        
        # Rate limiting settings
        self.rate_limits = {
            "google": {
                "requests_per_second": 10,
                "daily_limit": 2500  # Free tier limit
            },
            "mapbox": {
                "requests_per_second": 5,
                "daily_limit": 100000  # Free tier limit
            },
            "nominatim": {
                "requests_per_second": 1,  # Nominatim requires 1 second between requests
                "daily_limit": 1000  # Soft limit to be safe
            }
        }
        
        # Last request timestamps for rate limiting
        self.last_request_time = {
            "google": 0,
            "mapbox": 0,
            "nominatim": 0
        }
        
        # Request counters
        self.request_count = {
            "google": 0,
            "mapbox": 0,
            "nominatim": 0
        }
        
        logger.info("Geocoding Service initialized")
        
        # Check which providers are available
        self.available_providers = []
        if self.google_api_key:
            self.available_providers.append("google")
        if self.mapbox_access_token:
            self.available_providers.append("mapbox")
        if self.nominatim_user_agent:
            self.available_providers.append("nominatim")
            
        if not self.available_providers:
            logger.warning("No geocoding providers are configured with API keys")
        else:
            logger.info(f"Available geocoding providers: {', '.join(self.available_providers)}")
    
    async def geocode_address(self, 
                            address: str,
                            city: str = "",
                            state: str = "",
                            zip_code: str = "",
                            provider: Optional[str] = None,
                            use_cache: bool = True) -> Dict[str, Any]:
        """
        Geocode a single address to latitude and longitude.
        
        Args:
            address: Street address
            city: City name (optional)
            state: State code (optional)
            zip_code: ZIP code (optional)
            provider: Specific provider to use (google, mapbox, nominatim)
            use_cache: Whether to use cached results if available
            
        Returns:
            Dictionary with geocoding results including lat/lng coordinates
        """
        # Format full address
        full_address = self._format_address(address, city, state, zip_code)
        
        # Create cache key
        cache_key = f"geocode:{hashlib.md5(full_address.encode()).hexdigest()}"
        
        # Check cache if enabled
        if use_cache and self.cache_manager:
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Using cached geocoding for '{full_address}'")
                return cached_result
        
        # If specific provider is requested, use it with fallback
        if provider and provider in self.available_providers:
            providers_to_try = [provider] + [p for p in self.available_providers if p != provider]
        else:
            # Default: Try providers in order of precision/reliability
            providers_to_try = self.available_providers
        
        # If no providers are available, use approximate coordinates
        if not providers_to_try:
            logger.warning("No geocoding providers available, using approximate coordinates")
            result = self._generate_approximate_coordinates(city, state)
            
            # Cache result if caching is enabled
            if use_cache and self.cache_manager:
                await self.cache_manager.set(cache_key, result)
                
            return result
        
        # Try each provider in sequence until one succeeds
        errors = {}
        for provider in providers_to_try:
            try:
                # Respect rate limits
                await self._respect_rate_limit(provider)
                
                # Call provider-specific geocoding method
                if provider == "google":
                    result = await self._geocode_with_google(full_address)
                elif provider == "mapbox":
                    result = await self._geocode_with_mapbox(full_address)
                elif provider == "nominatim":
                    result = await self._geocode_with_nominatim(full_address)
                
                # Increment request counter
                self.request_count[provider] += 1
                
                # If result is valid, cache and return it
                if result.get("latitude") and result.get("longitude"):
                    # Add provider information to result
                    result["geocoding_provider"] = provider
                    
                    # Cache result if caching is enabled
                    if use_cache and self.cache_manager:
                        await self.cache_manager.set(cache_key, result)
                    
                    return result
                
                # If we got here, the provider didn't return valid coordinates
                errors[provider] = "No coordinates returned"
                
            except Exception as e:
                logger.error(f"Error geocoding with {provider}: {str(e)}")
                errors[provider] = str(e)
        
        # If all providers failed, log errors and return approximate coordinates
        logger.warning(f"All geocoding providers failed for '{full_address}': {errors}")
        result = self._generate_approximate_coordinates(city, state)
        result["geocoding_errors"] = errors
        
        # Cache result if caching is enabled
        if use_cache and self.cache_manager:
            await self.cache_manager.set(cache_key, result)
            
        return result
    
    async def batch_geocode(self, 
                          properties: List[Dict[str, Any]],
                          concurrency: int = 3,
                          provider: Optional[str] = None,
                          use_cache: bool = True) -> Dict[str, Any]:
        """
        Geocode multiple properties concurrently.
        
        Args:
            properties: List of property dictionaries with address information
            concurrency: Maximum number of concurrent geocoding operations
            provider: Specific provider to use
            use_cache: Whether to use cached results if available
            
        Returns:
            Dictionary with batch geocoding results and statistics
        """
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        # Prepare batch results
        batch_results = {}
        property_count = len(properties)
        
        # Function to geocode a single property with the semaphore
        async def geocode_property_with_semaphore(property_data, index):
            # Add small random delay to avoid thundering herd problem
            if index > 0:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
            async with semaphore:
                property_id = property_data.get("id", f"unknown_{index}")
                address = property_data.get("address", "")
                city = property_data.get("city", "")
                state = property_data.get("state", "")
                zip_code = property_data.get("zip_code", "")
                
                # Skip if no address information
                if not address:
                    return property_id, {
                        "error": "No address provided",
                        "property_data": property_data
                    }
                
                try:
                    # Geocode address
                    geocode_result = await self.geocode_address(
                        address=address,
                        city=city,
                        state=state,
                        zip_code=zip_code,
                        provider=provider,
                        use_cache=use_cache
                    )
                    
                    # Attach property ID for identification
                    geocode_result["property_id"] = property_id
                    
                    return property_id, geocode_result
                    
                except Exception as e:
                    logger.error(f"Error geocoding property {property_id}: {str(e)}")
                    return property_id, {
                        "error": str(e),
                        "property_data": property_data
                    }
        
        # Create tasks for all properties
        tasks = [geocode_property_with_semaphore(prop, i) for i, prop in enumerate(properties)]
        
        # Execute tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        error_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"Geocoding task failed with exception: {result}")
                continue
                
            property_id, geocode_result = result
            batch_results[property_id] = geocode_result
            
            if "error" not in geocode_result:
                success_count += 1
            else:
                error_count += 1
        
        # Return a dictionary with results and statistics
        return {
            "results": batch_results,
            "stats": {
                "total": property_count,
                "success": success_count,
                "errors": error_count,
                "success_rate": round(success_count / property_count * 100 if property_count > 0 else 0, 2),
                "provider_usage": self.request_count
            }
        }
    
    async def update_property_coordinates(self, property_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update property data with geocoded coordinates if missing.
        
        Args:
            property_data: Property dictionary to update
            
        Returns:
            Updated property dictionary with coordinates
        """
        # Check if coordinates are already present and valid
        latitude = property_data.get("latitude")
        longitude = property_data.get("longitude")
        
        if latitude and longitude and -90 <= latitude <= 90 and -180 <= longitude <= 180:
            # Coordinates are already present and valid
            return property_data
        
        # Get address components
        address = property_data.get("address", "")
        city = property_data.get("city", "")
        state = property_data.get("state", "")
        zip_code = property_data.get("zip_code", "")
        
        # Check if we have enough address information
        if not (address and (city or state)):
            logger.warning(f"Insufficient address information for geocoding: {address}, {city}, {state}")
            return property_data
        
        # Geocode address
        try:
            geocode_result = await self.geocode_address(
                address=address,
                city=city,
                state=state,
                zip_code=zip_code
            )
            
            # Update property data with coordinates
            property_data["latitude"] = geocode_result.get("latitude")
            property_data["longitude"] = geocode_result.get("longitude")
            
            # Add additional fields if not already present
            if "formatted_address" in geocode_result and not property_data.get("formatted_address"):
                property_data["formatted_address"] = geocode_result.get("formatted_address")
                
            if "geocoding_provider" in geocode_result:
                property_data["geocoding_provider"] = geocode_result.get("geocoding_provider")
                
            logger.info(f"Updated coordinates for property: {address}, {city}, {state}")
            
        except Exception as e:
            logger.error(f"Error updating coordinates: {str(e)}")
        
        return property_data
            
    async def _geocode_with_google(self, address: str) -> Dict[str, Any]:
        """Geocode using Google Maps API"""
        if not self.google_api_key:
            raise ValueError("Google Maps API key not configured")
            
        # Format URL with API key
        encoded_address = quote(address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={self.google_api_key}"
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
        # Check response status
        if data.get("status") != "OK":
            error_message = data.get("error_message", f"Status: {data.get('status')}")
            raise ValueError(f"Google geocoding failed: {error_message}")
                
        # Extract coordinates from first result
        if data.get("results") and len(data["results"]) > 0:
            location = data["results"][0]["geometry"]["location"]
            
            # Extract formatted address
            formatted_address = data["results"][0].get("formatted_address", address)
            
            # Create result dictionary
            result = {
                "latitude": location["lat"],
                "longitude": location["lng"],
                "formatted_address": formatted_address,
                "confidence": "high",  # Google results are generally high confidence
                "provider_response": {
                    "place_id": data["results"][0].get("place_id"),
                    "types": data["results"][0].get("types", [])
                }
            }
            
            return result
        else:
            raise ValueError("No geocoding results from Google")

    async def _geocode_with_mapbox(self, address: str) -> Dict[str, Any]:
        """Geocode using Mapbox API"""
        if not self.mapbox_access_token:
            raise ValueError("Mapbox access token not configured")
            
        # Format URL with access token
        encoded_address = quote(address)
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json?access_token={self.mapbox_access_token}"
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                
        # Check response
        if not data.get("features") or len(data["features"]) == 0:
            raise ValueError("No geocoding results from Mapbox")
                
        # Extract coordinates from first result
        feature = data["features"][0]
        coordinates = feature["geometry"]["coordinates"]
        
        # Extract formatted address
        formatted_address = feature.get("place_name", address)
        
        # Extract confidence score (relevance is 0-1, convert to low/medium/high)
        relevance = feature.get("relevance", 0)
        confidence = "high" if relevance > 0.8 else "medium" if relevance > 0.5 else "low"
        
        # Create result dictionary
        result = {
            "latitude": coordinates[1],  # Mapbox returns [longitude, latitude]
            "longitude": coordinates[0],
            "formatted_address": formatted_address,
            "confidence": confidence,
            "provider_response": {
                "id": feature.get("id"),
                "place_type": feature.get("place_type", []),
                "relevance": relevance
            }
        }
        
        return result

    async def _geocode_with_nominatim(self, address: str) -> Dict[str, Any]:
        """Geocode using Nominatim (OpenStreetMap)"""
        if not self.nominatim_user_agent:
            raise ValueError("Nominatim user agent not configured")
            
        # Format URL
        encoded_address = quote(address)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"
        
        # Set headers with user agent
        headers = {
            "User-Agent": self.nominatim_user_agent
        }
        
        # Make API request
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                data = await response.json()
                
        # Check response
        if not data or len(data) == 0:
            raise ValueError("No geocoding results from Nominatim")
                
        # Extract coordinates from first result
        result_data = data[0]
        
        # Extract confidence from OSM type and class
        osm_type = result_data.get("osm_type", "")
        importance = float(result_data.get("importance", 0))
        confidence = "high" if importance > 0.8 else "medium" if importance > 0.5 else "low"
        
        # Create result dictionary
        result = {
            "latitude": float(result_data["lat"]),
            "longitude": float(result_data["lon"]),
            "formatted_address": result_data.get("display_name", address),
            "confidence": confidence,
            "provider_response": {
                "osm_id": result_data.get("osm_id"),
                "osm_type": osm_type,
                "importance": importance
            }
        }
        
        return result
    
    def _format_address(self, address: str, city: str = "", state: str = "", zip_code: str = "") -> str:
        """
        Format a complete address string from components.
        
        Args:
            address: Street address
            city: City name
            state: State code
            zip_code: ZIP code
            
        Returns:
            Formatted address string
        """
        components = [c for c in [address, city, state, zip_code] if c]
        return ", ".join(components)
    
    def _generate_approximate_coordinates(self, city: str = "", state: str = "") -> Dict[str, Any]:
        """
        Generate approximate coordinates for a city/state if geocoding fails.
        
        Args:
            city: City name
            state: State code
            
        Returns:
            Dictionary with approximate coordinates
        """
        # Default to Austin, TX
        base_lat = float(os.getenv("DEFAULT_MAP_CENTER_LAT", 30.2672))
        base_lng = float(os.getenv("DEFAULT_MAP_CENTER_LNG", -97.7431))
        
        # Common US city coordinates (very limited set for fallback)
        us_cities = {
            "austin": {"lat": 30.2672, "lng": -97.7431, "state": "TX"},
            "dallas": {"lat": 32.7767, "lng": -96.7970, "state": "TX"},
            "houston": {"lat": 29.7604, "lng": -95.3698, "state": "TX"},
            "new york": {"lat": 40.7128, "lng": -74.0060, "state": "NY"},
            "los angeles": {"lat": 34.0522, "lng": -118.2437, "state": "CA"},
            "chicago": {"lat": 41.8781, "lng": -87.6298, "state": "IL"},
            "san francisco": {"lat": 37.7749, "lng": -122.4194, "state": "CA"}
        }
        
        # Try to find city in our limited database
        if city:
            city_lower = city.lower()
            for known_city, coords in us_cities.items():
                if city_lower == known_city and (not state or state == coords["state"]):
                    lat = coords["lat"]
                    lng = coords["lng"]
                    
                    # Add small random offset to avoid all properties stacking
                    random_lat_offset = random.uniform(-0.01, 0.01)
                    random_lng_offset = random.uniform(-0.01, 0.01)
                    
                    return {
                        "latitude": lat + random_lat_offset,
                        "longitude": lng + random_lng_offset,
                        "formatted_address": f"{city}, {state if state else coords['state']}",
                        "confidence": "low",
                        "approximate": True
                    }
        
        # If city not found, use default coordinates with random offset
        random_lat_offset = random.uniform(-0.1, 0.1)
        random_lng_offset = random.uniform(-0.1, 0.1)
        
        return {
            "latitude": base_lat + random_lat_offset,
            "longitude": base_lng + random_lng_offset,
            "formatted_address": f"{city + ', ' if city else ''}{state if state else 'Unknown Location'}",
            "confidence": "very_low",
            "approximate": True
        }
    
    async def _respect_rate_limit(self, provider: str) -> None:
        """
        Ensure we don't exceed provider rate limits.
        
        Args:
            provider: Geocoding provider name
        """
        provider_limits = self.rate_limits.get(provider, {})
        requests_per_second = provider_limits.get("requests_per_second", 10)
        
        # Calculate minimum time between requests (in seconds)
        min_time_between_requests = 1.0 / requests_per_second
        
        # Get current time
        current_time = time.time()
        
        # Get time since last request
        time_since_last_request = current_time - self.last_request_time[provider]
        
        # If we need to wait, sleep for the required time
        if time_since_last_request < min_time_between_requests:
            wait_time = min_time_between_requests - time_since_last_request
            await asyncio.sleep(wait_time)
        
        # Update last request time
        self.last_request_time[provider] = time.time()
        
        # Check daily limit
        daily_limit = provider_limits.get("daily_limit", float("inf"))
        if self.request_count[provider] >= daily_limit:
            logger.warning(f"Daily limit reached for {provider} geocoding provider")
            raise ValueError(f"Daily geocoding limit reached for {provider}")
            
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get geocoding usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            "request_count": self.request_count,
            "available_providers": self.available_providers
        }

# CLI for testing the geocoding service
if __name__ == "__main__":
    import sys
    import argparse
    from backend.data_enrichment.cache_manager import ResearchCacheManager
    
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Geocode addresses")
    parser.add_argument("--address", help="Address to geocode")
    parser.add_argument("--city", help="City")
    parser.add_argument("--state", help="State")
    parser.add_argument("--zip", help="ZIP code")
    parser.add_argument("--provider", help="Geocoding provider (google, mapbox, nominatim)")
    parser.add_argument("--no-cache", action="store_true", help="Disable cache")
    
    args = parser.parse_args()
    
    # Run geocoding test
    async def test_geocoding():
        cache_manager = ResearchCacheManager()
        geocoder = GeocodingService(cache_manager=cache_manager)
        
        # Use default test address if not provided
        address = args.address or "1234 Red River St"
        city = args.city or "Austin"
        state = args.state or "TX"
        zip_code = args.zip or "78701"
        
        print(f"Geocoding: {address}, {city}, {state} {zip_code}")
        
        result = await geocoder.geocode_address(
            address=address,
            city=city,
            state=state,
            zip_code=zip_code,
            provider=args.provider,
            use_cache=not args.no_cache
        )
        
        print("\nGeocoding Result:")
        for key, value in result.items():
            print(f"{key}: {value}")
        
        print("\nProvider Usage Statistics:")
        stats = geocoder.get_usage_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
    
    # Run the test
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(test_geocoding())