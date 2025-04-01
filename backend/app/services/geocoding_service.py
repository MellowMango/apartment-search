"""
Geocoding service for property address processing.

This service provides geocoding functionality for converting property addresses
to geographic coordinates, using various geocoding providers and handling caching,
error handling, and rate limiting.
"""

import os
import logging
import asyncio
import aiohttp
import random
import time
import hashlib
from datetime import datetime
from typing import Dict, Any, List, Tuple, Optional, Union

from backend.app.utils.architecture import layer, ArchitectureLayer, log_cross_layer_call
from backend.app.interfaces.repository import PropertyRepository
from backend.app.interfaces.storage import StorageResult
from backend.app.db.repository_factory import get_repository_factory
from backend.app.db.unit_of_work import get_unit_of_work
from backend.app.core.exceptions import GeocodingError, StorageException, NotFoundException
from backend.app.core.config import settings
from backend.app.utils.monitoring import record_external_api_call

logger = logging.getLogger(__name__)


@layer(ArchitectureLayer.API)
class GeocodingService:
    """
    Service for geocoding property addresses using various providers.
    
    Features:
    - Support for multiple geocoding providers (Google Maps, Mapbox, Nominatim)
    - Fallback mechanisms if primary provider fails
    - Repository pattern for data access
    - Transaction support
    - Rate limiting and caching
    - Metrics collection
    """
    
    def __init__(self, repository_factory=None, cache_manager=None):
        """
        Initialize the geocoding service.
        
        Args:
            repository_factory: Factory for creating repositories
            cache_manager: Cache manager for geocoding results
        """
        # Get repository through factory
        factory = repository_factory or get_repository_factory()
        self.property_repository = factory.create_property_repository()
        
        # Cache manager (will be injected if provided)
        self.cache_manager = cache_manager
        
        # API keys from environment variables
        self.google_api_key = os.getenv("GOOGLE_PLACES_API_KEY", "")
        self.mapbox_access_token = os.getenv("MAPBOX_ACCESS_TOKEN", "")
        self.nominatim_user_agent = os.getenv("NOMINATIM_USER_AGENT", "AcquireApartments/1.0")
        
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
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def update_property_coordinates(self, property_id: str) -> Dict[str, Any]:
        """
        Update property coordinates and save to the repository.
        
        Args:
            property_id: ID of the property to update
            
        Returns:
            Updated property entity
            
        Raises:
            NotFoundException: If the property is not found
            StorageException: If there's an error updating the property
            GeocodingError: If geocoding fails
        """
        async with get_unit_of_work() as uow:
            try:
                # Get property from repository
                property_entity = await uow.property_repository.get(property_id)
                if not property_entity:
                    raise NotFoundException(f"Property with ID {property_id} not found")
                
                # Skip if coordinates are already valid
                if (hasattr(property_entity, 'latitude') and 
                    hasattr(property_entity, 'longitude') and
                    property_entity.latitude is not None and 
                    property_entity.longitude is not None and
                    -90 <= property_entity.latitude <= 90 and 
                    -180 <= property_entity.longitude <= 180):
                    logger.info(f"Property {property_id} already has valid coordinates")
                    return property_entity.dict()
                
                # Extract address components
                address_components = self._extract_address_components(property_entity)
                
                # Geocode the property address
                try:
                    geocode_result = await self.geocode_address(
                        address=address_components.get("street", ""),
                        city=address_components.get("city", ""),
                        state=address_components.get("state", ""),
                        zip_code=address_components.get("zip_code", "")
                    )
                except Exception as e:
                    # Convert all exceptions to GeocodingError
                    raise GeocodingError(
                        message=f"Failed to geocode property {property_id}: {str(e)}",
                        details={
                            "property_id": property_id,
                            "address": address_components
                        }
                    )
                
                # Update the property entity with geocoded coordinates
                property_entity.latitude = geocode_result.get("latitude")
                property_entity.longitude = geocode_result.get("longitude")
                
                # Add additional fields if available
                if "formatted_address" in geocode_result:
                    property_entity.formatted_address = geocode_result.get("formatted_address")
                
                if "geocoding_provider" in geocode_result:
                    property_entity.geocoding_provider = geocode_result.get("geocoding_provider")
                
                if "geocode_verified" in geocode_result:
                    property_entity.geocode_verified = geocode_result.get("geocode_verified", False)
                
                # Save changes through repository
                result = await uow.property_repository.update(property_id, property_entity)
                if not result.success:
                    raise StorageException(
                        message=f"Failed to update property: {result.error}",
                        details={"property_id": property_id}
                    )
                
                # Commit the transaction
                await uow.commit()
                
                logger.info(f"Updated coordinates for property {property_id}")
                return result.entity.dict()
                
            except (NotFoundException, GeocodingError, StorageException) as e:
                # Rollback in case of known exceptions
                await uow.rollback()
                logger.error(f"Error in update_property_coordinates: {str(e)}")
                raise
                
            except Exception as e:
                # Rollback in case of unexpected exceptions
                await uow.rollback()
                logger.exception(f"Unexpected error in update_property_coordinates: {str(e)}")
                raise GeocodingError(
                    message=f"An unexpected error occurred: {str(e)}",
                    details={"property_id": property_id}
                )
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def batch_update_coordinates(
        self,
        property_ids: List[str],
        concurrency: int = 3
    ) -> Dict[str, Any]:
        """
        Update coordinates for multiple properties in batch.
        
        Args:
            property_ids: List of property IDs to update
            concurrency: Maximum number of concurrent operations
            
        Returns:
            Dictionary with batch results and statistics
        """
        # Create a semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        # Prepare batch results
        batch_results = {}
        property_count = len(property_ids)
        
        # Function to update a single property with the semaphore
        async def update_property_with_semaphore(property_id, index):
            # Add small random delay to avoid thundering herd problem
            if index > 0:
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
            async with semaphore:
                try:
                    # Update property coordinates
                    result = await self.update_property_coordinates(property_id)
                    return property_id, {
                        "success": True,
                        "coordinates": {
                            "latitude": result.get("latitude"),
                            "longitude": result.get("longitude")
                        },
                        "provider": result.get("geocoding_provider"),
                        "verified": result.get("geocode_verified", False)
                    }
                except NotFoundException:
                    return property_id, {
                        "success": False,
                        "error": "Property not found"
                    }
                except Exception as e:
                    logger.error(f"Error updating coordinates for property {property_id}: {str(e)}")
                    return property_id, {
                        "success": False,
                        "error": str(e)
                    }
        
        # Create tasks for all properties
        tasks = [update_property_with_semaphore(prop_id, i) for i, prop_id in enumerate(property_ids)]
        
        # Execute tasks and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        success_count = 0
        error_count = 0
        not_found_count = 0
        
        for result in results:
            if isinstance(result, Exception):
                error_count += 1
                logger.error(f"Task failed with exception: {result}")
                continue
                
            property_id, update_result = result
            batch_results[property_id] = update_result
            
            if update_result.get("success"):
                success_count += 1
            elif update_result.get("error") == "Property not found":
                not_found_count += 1
            else:
                error_count += 1
        
        # Return a dictionary with results and statistics
        return {
            "results": batch_results,
            "stats": {
                "total": property_count,
                "success": success_count,
                "errors": error_count,
                "not_found": not_found_count,
                "success_rate": round(success_count / property_count * 100 if property_count > 0 else 0, 2),
                "provider_usage": self.request_count
            }
        }
    
    @log_cross_layer_call(ArchitectureLayer.API, ArchitectureLayer.STORAGE)
    async def verify_property_coordinates(self, property_id: str, verified: bool = True) -> Dict[str, Any]:
        """
        Mark a property's coordinates as verified.
        
        Args:
            property_id: ID of the property to mark
            verified: Whether to mark as verified or not
            
        Returns:
            Updated property entity
            
        Raises:
            NotFoundException: If the property is not found
            StorageException: If there's an error updating the property
        """
        async with get_unit_of_work() as uow:
            try:
                # Use specialized repository method
                result = await uow.property_repository.mark_as_verified(
                    id=property_id,
                    verified=verified
                )
                
                if not result.success:
                    if "not found" in result.error.lower():
                        raise NotFoundException(f"Property with ID {property_id} not found")
                    else:
                        raise StorageException(
                            message=f"Failed to update property: {result.error}",
                            details={"property_id": property_id}
                        )
                
                # Commit the transaction
                await uow.commit()
                
                logger.info(f"Marked property {property_id} coordinates as {'verified' if verified else 'unverified'}")
                return result.entity.dict()
                
            except (NotFoundException, StorageException) as e:
                # Rollback in case of known exceptions
                await uow.rollback()
                logger.error(f"Error in verify_property_coordinates: {str(e)}")
                raise
                
            except Exception as e:
                # Rollback in case of unexpected exceptions
                await uow.rollback()
                logger.exception(f"Unexpected error in verify_property_coordinates: {str(e)}")
                raise StorageException(
                    message=f"An unexpected error occurred: {str(e)}",
                    details={"property_id": property_id}
                )
    
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
            
        Raises:
            GeocodingError: If geocoding fails for all providers
        """
        # Format full address
        full_address = self._format_address(address, city, state, zip_code)
        
        # Create cache key
        cache_key = f"geocode:{hashlib.md5(full_address.encode()).hexdigest()}"
        
        # Check cache if enabled
        if use_cache and self.cache_manager:
            try:
                cached_result = await self.cache_manager.get(cache_key)
                if cached_result:
                    logger.info(f"Using cached geocoding for '{full_address}'")
                    return cached_result
            except Exception as e:
                logger.warning(f"Cache lookup failed: {str(e)}")
        
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
                try:
                    await self.cache_manager.set(cache_key, result)
                except Exception as e:
                    logger.warning(f"Cache storage failed: {str(e)}")
                
            return result
        
        # Try each provider in sequence until one succeeds
        errors = {}
        for provider in providers_to_try:
            try:
                # Track timing for metrics
                start_time = time.time()
                
                # Respect rate limits
                await self._respect_rate_limit(provider)
                
                # Call provider-specific geocoding method
                if provider == "google":
                    result = await self._geocode_with_google(full_address)
                elif provider == "mapbox":
                    result = await self._geocode_with_mapbox(full_address)
                elif provider == "nominatim":
                    result = await self._geocode_with_nominatim(full_address)
                
                # Calculate duration for metrics
                duration_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                record_external_api_call(
                    service=f"geocoding_{provider}",
                    operation="geocode_address",
                    success=True,
                    duration_ms=duration_ms
                )
                
                # Increment request counter
                self.request_count[provider] += 1
                
                # If result is valid, cache and return it
                if result.get("latitude") and result.get("longitude"):
                    # Add provider information to result
                    result["geocoding_provider"] = provider
                    
                    # Cache result if caching is enabled
                    if use_cache and self.cache_manager:
                        try:
                            await self.cache_manager.set(cache_key, result)
                        except Exception as e:
                            logger.warning(f"Cache storage failed: {str(e)}")
                    
                    return result
                
                # If we got here, the provider didn't return valid coordinates
                errors[provider] = "No coordinates returned"
                
            except Exception as e:
                # Calculate duration for metrics
                duration_ms = (time.time() - start_time) * 1000
                
                # Record metrics
                record_external_api_call(
                    service=f"geocoding_{provider}",
                    operation="geocode_address",
                    success=False,
                    duration_ms=duration_ms
                )
                
                logger.error(f"Error geocoding with {provider}: {str(e)}")
                errors[provider] = str(e)
        
        # If all providers failed, log errors and return approximate coordinates
        logger.warning(f"All geocoding providers failed for '{full_address}': {errors}")
        result = self._generate_approximate_coordinates(city, state)
        result["geocoding_errors"] = errors
        
        # Cache result if caching is enabled
        if use_cache and self.cache_manager:
            try:
                await self.cache_manager.set(cache_key, result)
            except Exception as e:
                logger.warning(f"Cache storage failed: {str(e)}")
            
        return result
    
    async def _geocode_with_google(self, address: str) -> Dict[str, Any]:
        """
        Geocode using Google Maps API.
        
        Args:
            address: Address to geocode
            
        Returns:
            Dictionary with geocoding results
            
        Raises:
            GeocodingError: If geocoding fails
        """
        if not self.google_api_key:
            raise GeocodingError(
                message="Google Maps API key not configured",
                details={"provider": "google"}
            )
            
        # Format URL with API key
        from urllib.parse import quote
        encoded_address = quote(address)
        url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={self.google_api_key}"
        
        # Make API request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise GeocodingError(
                            message=f"Google API returned status {response.status}",
                            details={"provider": "google", "status_code": response.status}
                        )
                    
                    data = await response.json()
        except aiohttp.ClientError as e:
            raise GeocodingError(
                message=f"Connection error with Google API: {str(e)}",
                details={"provider": "google"}
            )
                
        # Check response status
        if data.get("status") != "OK":
            error_message = data.get("error_message", f"Status: {data.get('status')}")
            raise GeocodingError(
                message=f"Google geocoding failed: {error_message}",
                details={"provider": "google", "status": data.get("status")}
            )
                
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
            raise GeocodingError(
                message="No geocoding results from Google",
                details={"provider": "google"}
            )
    
    async def _geocode_with_mapbox(self, address: str) -> Dict[str, Any]:
        """
        Geocode using Mapbox API.
        
        Args:
            address: Address to geocode
            
        Returns:
            Dictionary with geocoding results
            
        Raises:
            GeocodingError: If geocoding fails
        """
        if not self.mapbox_access_token:
            raise GeocodingError(
                message="Mapbox access token not configured",
                details={"provider": "mapbox"}
            )
            
        # Format URL with access token
        from urllib.parse import quote
        encoded_address = quote(address)
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{encoded_address}.json?access_token={self.mapbox_access_token}"
        
        # Make API request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise GeocodingError(
                            message=f"Mapbox API returned status {response.status}",
                            details={"provider": "mapbox", "status_code": response.status}
                        )
                    
                    data = await response.json()
        except aiohttp.ClientError as e:
            raise GeocodingError(
                message=f"Connection error with Mapbox API: {str(e)}",
                details={"provider": "mapbox"}
            )
                
        # Check response
        if not data.get("features") or len(data["features"]) == 0:
            raise GeocodingError(
                message="No geocoding results from Mapbox",
                details={"provider": "mapbox"}
            )
                
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
        """
        Geocode using Nominatim (OpenStreetMap).
        
        Args:
            address: Address to geocode
            
        Returns:
            Dictionary with geocoding results
            
        Raises:
            GeocodingError: If geocoding fails
        """
        if not self.nominatim_user_agent:
            raise GeocodingError(
                message="Nominatim user agent not configured",
                details={"provider": "nominatim"}
            )
            
        # Format URL
        from urllib.parse import quote
        encoded_address = quote(address)
        url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=json&limit=1"
        
        # Set headers with user agent
        headers = {
            "User-Agent": self.nominatim_user_agent
        }
        
        # Make API request
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status != 200:
                        raise GeocodingError(
                            message=f"Nominatim API returned status {response.status}",
                            details={"provider": "nominatim", "status_code": response.status}
                        )
                    
                    data = await response.json()
        except aiohttp.ClientError as e:
            raise GeocodingError(
                message=f"Connection error with Nominatim API: {str(e)}",
                details={"provider": "nominatim"}
            )
                
        # Check response
        if not data or len(data) == 0:
            raise GeocodingError(
                message="No geocoding results from Nominatim",
                details={"provider": "nominatim"}
            )
                
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
        # Clean up address components
        # Remove "Location:" prefix from city or address
        if city and city.startswith("Location:"):
            city = city.replace("Location:", "").strip()
            
        if address and address.startswith("Location:"):
            address = address.replace("Location:", "").strip()
            
        # If address doesn't have street info but has city info, don't duplicate
        if address and city and address.lower() == city.lower():
            # Use address only since it duplicates city
            components = [c for c in [address, state, zip_code] if c]
        else:
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
        # Clean city name if it has "Location:" prefix
        if city and city.startswith("Location:"):
            city = city.replace("Location:", "").strip()
            
        # Common US city coordinates (expanded set for better coverage)
        us_cities = {
            "austin": {"lat": 30.2672, "lng": -97.7431, "state": "TX"},
            "dallas": {"lat": 32.7767, "lng": -96.7970, "state": "TX"},
            "houston": {"lat": 29.7604, "lng": -95.3698, "state": "TX"},
            "san antonio": {"lat": 29.4241, "lng": -98.4936, "state": "TX"},
            "fort worth": {"lat": 32.7555, "lng": -97.3308, "state": "TX"},
            "el paso": {"lat": 31.7619, "lng": -106.4850, "state": "TX"},
            "arlington": {"lat": 32.7357, "lng": -97.1081, "state": "TX"},
            "corpus christi": {"lat": 27.8006, "lng": -97.3964, "state": "TX"},
            "plano": {"lat": 33.0198, "lng": -96.6989, "state": "TX"},
            "lubbock": {"lat": 33.5779, "lng": -101.8552, "state": "TX"},
            "irving": {"lat": 32.8140, "lng": -96.9489, "state": "TX"},
            "killeen": {"lat": 31.1171, "lng": -97.6789, "state": "TX"},
            "amarillo": {"lat": 35.2220, "lng": -101.8313, "state": "TX"},
            "longview": {"lat": 32.5007, "lng": -94.7405, "state": "TX"},
            "waco": {"lat": 31.5493, "lng": -97.1467, "state": "TX"},
            "temple": {"lat": 31.0982, "lng": -97.3428, "state": "TX"},
            "san marcos": {"lat": 29.8833, "lng": -97.9414, "state": "TX"},
            "oklahoma city": {"lat": 35.4676, "lng": -97.5164, "state": "OK"},
            "tulsa": {"lat": 36.1540, "lng": -95.9928, "state": "OK"},
            "norman": {"lat": 35.2226, "lng": -97.4395, "state": "OK"},
            "shawnee": {"lat": 35.3272, "lng": -96.9253, "state": "OK"},
            "del city": {"lat": 35.4489, "lng": -97.4406, "state": "OK"},
            "north little rock": {"lat": 34.7695, "lng": -92.2671, "state": "AR"},
            "little rock": {"lat": 34.7465, "lng": -92.2896, "state": "AR"},
            "new york": {"lat": 40.7128, "lng": -74.0060, "state": "NY"},
            "los angeles": {"lat": 34.0522, "lng": -118.2437, "state": "CA"},
            "chicago": {"lat": 41.8781, "lng": -87.6298, "state": "IL"},
            "san francisco": {"lat": 37.7749, "lng": -122.4194, "state": "CA"}
        }
        
        # Try to find city in our expanded database
        if city:
            city_lower = city.lower()
            for known_city, coords in us_cities.items():
                # Check for exact match with state
                if city_lower == known_city and (not state or state == coords["state"]):
                    lat = coords["lat"]
                    lng = coords["lng"]
                    
                    # Add very small random offset to avoid all properties stacking
                    random_lat_offset = random.uniform(-0.005, 0.005)
                    random_lng_offset = random.uniform(-0.005, 0.005)
                    
                    return {
                        "latitude": lat + random_lat_offset,
                        "longitude": lng + random_lng_offset,
                        "formatted_address": f"{city}, {state if state else coords['state']}",
                        "confidence": "medium", # Upgraded from low because it's a known city
                        "approximate": True,
                        "city_match": True
                    }
                # Check for partial match
                elif known_city in city_lower or city_lower in known_city:
                    if not state or state == coords["state"]:
                        lat = coords["lat"]
                        lng = coords["lng"]
                        
                        # Add small random offset
                        random_lat_offset = random.uniform(-0.008, 0.008)
                        random_lng_offset = random.uniform(-0.008, 0.008)
                        
                        return {
                            "latitude": lat + random_lat_offset,
                            "longitude": lng + random_lng_offset,
                            "formatted_address": f"{city}, {state if state else coords['state']}",
                            "confidence": "low",
                            "approximate": True,
                            "city_partial_match": True
                        }
        
        # If state is provided but city matching failed, use a major city in that state
        if state:
            state_upper = state.upper()
            state_cities = [c for c_name, c in us_cities.items() if c["state"] == state_upper]
            
            if state_cities:
                # Pick the first city in the state
                city_data = list(state_cities)[0]
                lat = city_data["lat"]
                lng = city_data["lng"]
                
                # Add larger random offset for state-level approximation
                random_lat_offset = random.uniform(-0.03, 0.03)
                random_lng_offset = random.uniform(-0.03, 0.03)
                
                return {
                    "latitude": lat + random_lat_offset,
                    "longitude": lng + random_lng_offset,
                    "formatted_address": f"Unknown location in {state}",
                    "confidence": "very_low",
                    "approximate": True,
                    "state_approximation": True
                }
        
        # We couldn't match city or state - this is a fallback case
        # Instead of defaulting to Austin coordinates, mark as unknown
        return {
            "latitude": None,
            "longitude": None,
            "formatted_address": f"{city + ', ' if city else ''}{state if state else 'Unknown Location'}",
            "confidence": "none",
            "approximate": False,
            "geocoding_failed": True
        }
    
    async def _respect_rate_limit(self, provider: str) -> None:
        """
        Ensure we don't exceed provider rate limits.
        
        Args:
            provider: Geocoding provider name
            
        Raises:
            GeocodingError: If daily limit is exceeded
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
            raise GeocodingError(
                message=f"Daily geocoding limit reached for {provider}",
                details={"provider": provider, "limit": daily_limit}
            )
            
    def get_usage_statistics(self) -> Dict[str, Any]:
        """
        Get geocoding usage statistics.
        
        Returns:
            Dictionary with usage statistics
        """
        return {
            "request_count": self.request_count,
            "available_providers": self.available_providers,
            "last_request_time": {
                provider: datetime.fromtimestamp(timestamp).isoformat()
                for provider, timestamp in self.last_request_time.items()
                if timestamp > 0
            }
        }
    
    def _extract_address_components(self, property_entity: Any) -> Dict[str, str]:
        """
        Extract address components from a property entity.
        
        The method attempts to accommodate different property entity structures.
        
        Args:
            property_entity: Property entity with address information
            
        Returns:
            Dictionary with address components
        """
        components = {}
        
        # Try different attribute names for each component
        
        # Street address
        if hasattr(property_entity, 'address'):
            components["street"] = property_entity.address
        elif hasattr(property_entity, 'street_address'):
            components["street"] = property_entity.street_address
        elif hasattr(property_entity, 'street'):
            components["street"] = property_entity.street
            
        # City
        if hasattr(property_entity, 'city'):
            components["city"] = property_entity.city
        elif hasattr(property_entity, 'locality'):
            components["city"] = property_entity.locality
            
        # State
        if hasattr(property_entity, 'state'):
            components["state"] = property_entity.state
        elif hasattr(property_entity, 'region'):
            components["state"] = property_entity.region
        elif hasattr(property_entity, 'state_code'):
            components["state"] = property_entity.state_code
            
        # ZIP code
        if hasattr(property_entity, 'zip_code'):
            components["zip_code"] = property_entity.zip_code
        elif hasattr(property_entity, 'postal_code'):
            components["zip_code"] = property_entity.postal_code
        elif hasattr(property_entity, 'zip'):
            components["zip_code"] = property_entity.zip
            
        # Try nested address structure
        if hasattr(property_entity, 'address') and hasattr(property_entity.address, 'street'):
            components["street"] = property_entity.address.street
            
            if hasattr(property_entity.address, 'city'):
                components["city"] = property_entity.address.city
                
            if hasattr(property_entity.address, 'state'):
                components["state"] = property_entity.address.state
                
            if hasattr(property_entity.address, 'zip_code'):
                components["zip_code"] = property_entity.address.zip_code
                
        return components