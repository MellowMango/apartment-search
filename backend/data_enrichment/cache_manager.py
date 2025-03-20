#!/usr/bin/env python3
"""
Cache Manager for Deep Property Research

This module provides caching functionality for research results,
with support for both memory and disk-based caching.
"""

import os
import json
import time
import logging
import hashlib
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class ResearchCacheManager:
    """
    Manages caching of property research results.
    
    Features:
    - Two-tier caching (memory and disk)
    - Time-based cache invalidation
    - Different TTLs for different data types
    - Thread-safe cache access
    """
    
    def __init__(self, cache_dir: str = None, max_memory_entries: int = 1000, 
                 cleanup_interval: int = 3600):
        """
        Initialize the cache manager.
        
        Args:
            cache_dir: Directory for disk cache (optional)
            max_memory_entries: Maximum number of entries to keep in memory cache (default: 1000)
            cleanup_interval: Interval in seconds for automatic cache cleanup (default: 1 hour)
        """
        # Memory cache with LRU functionality
        self.memory_cache = {}
        self.cache_access_times = {}  # For LRU eviction
        self.max_memory_entries = max_memory_entries
        
        # Disk cache
        self.cache_dir = cache_dir or os.path.join("data", "research_cache")
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Default TTLs (in days)
        self.default_ttls = {
            "property_details": 30,        # Property details change infrequently
            "investment_potential": 7,     # Financial metrics change more often
            "market_conditions": 7,        # Market data changes frequently
            "risks": 90,                   # Risk assessments are more stable
            "research": 14,                # Complete research results
            "default": 7                   # Default for unspecified types
        }
        
        # Set last cleanup time
        self.last_cleanup_time = time.time()
        self.cleanup_interval = cleanup_interval  # In seconds
        
        logger.info(f"Research cache initialized with cache directory: {self.cache_dir}, "
                   f"max memory entries: {self.max_memory_entries}, "
                   f"cleanup interval: {cleanup_interval}s")
    
    async def get(self, key: str, data_type: str = "default") -> Optional[Dict[str, Any]]:
        """
        Get cached data if it exists and is valid.
        
        Args:
            key: Cache key
            data_type: Type of data (for TTL determination)
            
        Returns:
            Cached data or None if not found or expired
        """
        # Check if it's time for auto cleanup
        self._check_auto_cleanup()
        
        # First check memory cache
        if key in self.memory_cache:
            cache_entry = self.memory_cache[key]
            if not self._is_expired(cache_entry, data_type):
                # Update access time for LRU functionality
                self.cache_access_times[key] = time.time()
                logger.debug(f"Memory cache hit for key: {key}")
                return cache_entry["data"]
        
        # If not in memory, check disk cache
        disk_key = self._hash_key(key)
        cache_file = os.path.join(self.cache_dir, f"{disk_key}.json")
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)
                
                if not self._is_expired(cache_entry, data_type):
                    # Add to memory cache for faster access next time, with LRU check
                    self._add_to_memory_cache(key, cache_entry)
                    logger.debug(f"Disk cache hit for key: {key}")
                    return cache_entry["data"]
                else:
                    logger.debug(f"Expired disk cache for key: {key}")
                    # Remove expired disk cache
                    os.remove(cache_file)
            except Exception as e:
                logger.error(f"Error reading cache file {cache_file}: {e}")
                # Try to recover by removing corrupted file
                try:
                    os.remove(cache_file)
                    logger.info(f"Removed corrupted cache file {cache_file}")
                except Exception:
                    pass
        
        logger.debug(f"Cache miss for key: {key}")
        return None
    
    async def set(self, key: str, data: Dict[str, Any], data_type: str = "default") -> None:
        """
        Set data in cache.
        
        Args:
            key: Cache key
            data: Data to cache
            data_type: Type of data (for TTL determination)
        """
        # Create cache entry with timestamp
        cache_entry = {
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "data_type": data_type
        }
        
        # Store in memory cache with LRU management
        self._add_to_memory_cache(key, cache_entry)
        
        # Store in disk cache
        disk_key = self._hash_key(key)
        cache_file = os.path.join(self.cache_dir, f"{disk_key}.json")
        
        try:
            # Write to a temporary file first to avoid corruption during crashes
            temp_file = f"{cache_file}.tmp"
            with open(temp_file, 'w') as f:
                json.dump(cache_entry, f, indent=2)
            
            # Replace the original file atomically
            os.replace(temp_file, cache_file)
            logger.debug(f"Cached data for key: {key}")
        except Exception as e:
            logger.error(f"Error writing cache file {cache_file}: {e}")
            # Try to clean up temp file if it exists
            try:
                if os.path.exists(f"{cache_file}.tmp"):
                    os.remove(f"{cache_file}.tmp")
            except Exception:
                pass
    
    def invalidate(self, key: str) -> bool:
        """
        Invalidate a specific cache entry.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was found and invalidated, False otherwise
        """
        # Remove from memory cache
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # Remove from disk cache
        disk_key = self._hash_key(key)
        cache_file = os.path.join(self.cache_dir, f"{disk_key}.json")
        
        if os.path.exists(cache_file):
            try:
                os.remove(cache_file)
                logger.debug(f"Invalidated cache for key: {key}")
                return True
            except Exception as e:
                logger.error(f"Error removing cache file {cache_file}: {e}")
        
        return False
    
    def clear(self, data_type: str = None) -> int:
        """
        Clear all cache entries or entries of a specific type.
        
        Args:
            data_type: Type of data to clear (or all if None)
            
        Returns:
            Number of entries cleared
        """
        count = 0
        
        # Clear memory cache
        if data_type:
            keys_to_remove = []
            for key, entry in self.memory_cache.items():
                if entry.get("data_type") == data_type:
                    keys_to_remove.append(key)
            
            for key in keys_to_remove:
                del self.memory_cache[key]
                count += 1
        else:
            count += len(self.memory_cache)
            self.memory_cache = {}
        
        # Clear disk cache
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
                
            cache_file = os.path.join(self.cache_dir, filename)
            
            if data_type:
                try:
                    with open(cache_file, 'r') as f:
                        cache_entry = json.load(f)
                    
                    if cache_entry.get("data_type") == data_type:
                        os.remove(cache_file)
                        count += 1
                except Exception as e:
                    logger.error(f"Error processing cache file {cache_file}: {e}")
            else:
                try:
                    os.remove(cache_file)
                    count += 1
                except Exception as e:
                    logger.error(f"Error removing cache file {cache_file}: {e}")
        
        logger.info(f"Cleared {count} cache entries" + 
                  (f" of type '{data_type}'" if data_type else ""))
        
        return count
    
    def purge_expired(self) -> int:
        """
        Purge all expired cache entries.
        
        Returns:
            Number of expired entries purged
        """
        count = 0
        
        # Purge memory cache
        keys_to_remove = []
        for key, entry in self.memory_cache.items():
            data_type = entry.get("data_type", "default")
            if self._is_expired(entry, data_type):
                keys_to_remove.append(key)
        
        for key in keys_to_remove:
            del self.memory_cache[key]
            count += 1
        
        # Purge disk cache
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
                
            cache_file = os.path.join(self.cache_dir, filename)
            
            try:
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)
                
                data_type = cache_entry.get("data_type", "default")
                if self._is_expired(cache_entry, data_type):
                    os.remove(cache_file)
                    count += 1
            except Exception as e:
                logger.error(f"Error processing cache file {cache_file}: {e}")
                # Remove corrupted cache files
                try:
                    os.remove(cache_file)
                    count += 1
                except:
                    pass
        
        logger.info(f"Purged {count} expired cache entries")
        return count
    
    def _is_expired(self, cache_entry: Dict[str, Any], data_type: str) -> bool:
        """
        Check if a cache entry is expired.
        
        Args:
            cache_entry: Cache entry to check
            data_type: Type of data
            
        Returns:
            True if expired, False otherwise
        """
        if not cache_entry.get("timestamp"):
            return True
        
        # Get TTL for data type
        ttl_days = self.default_ttls.get(data_type, self.default_ttls["default"])
        
        # Parse timestamp
        try:
            timestamp = datetime.fromisoformat(cache_entry["timestamp"])
        except (ValueError, TypeError):
            return True
        
        # Check if expired
        expiration = timestamp + timedelta(days=ttl_days)
        return datetime.now() > expiration
    
    def _add_to_memory_cache(self, key: str, cache_entry: Dict[str, Any]) -> None:
        """
        Add an entry to the memory cache with LRU management.
        
        Args:
            key: Cache key
            cache_entry: Cache entry to store
        """
        # Update or add to memory cache
        self.memory_cache[key] = cache_entry
        self.cache_access_times[key] = time.time()
        
        # Check if we need to evict entries
        if len(self.memory_cache) > self.max_memory_entries:
            # Evict least recently used entries
            entries_to_evict = len(self.memory_cache) - self.max_memory_entries
            
            # Get sorted keys by access time
            sorted_keys = sorted(
                self.cache_access_times.keys(), 
                key=lambda k: self.cache_access_times.get(k, 0)
            )
            
            # Remove oldest entries
            for old_key in sorted_keys[:entries_to_evict]:
                if old_key in self.memory_cache:
                    del self.memory_cache[old_key]
                if old_key in self.cache_access_times:
                    del self.cache_access_times[old_key]
            
            logger.debug(f"Evicted {entries_to_evict} entries from memory cache (LRU policy)")
    
    def _check_auto_cleanup(self) -> None:
        """
        Check if it's time to perform automatic cache cleanup.
        """
        current_time = time.time()
        
        # If cleanup interval has passed since last cleanup
        if current_time - self.last_cleanup_time > self.cleanup_interval:
            # Run cleanup in background so it doesn't block the current operation
            import threading
            cleanup_thread = threading.Thread(target=self._background_cleanup)
            cleanup_thread.daemon = True
            cleanup_thread.start()
            
            # Update last cleanup time
            self.last_cleanup_time = current_time
    
    def _background_cleanup(self) -> None:
        """
        Perform cleanup operations in background thread.
        """
        try:
            cleaned_count = self.purge_expired()
            logger.info(f"Background cleanup removed {cleaned_count} expired cache entries")
        except Exception as e:
            logger.error(f"Error during background cache cleanup: {e}")
    
    def _hash_key(self, key: str) -> str:
        """
        Hash a key for disk cache.
        
        Args:
            key: Cache key
            
        Returns:
            Hashed key
        """
        return hashlib.md5(key.encode()).hexdigest()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary of cache statistics
        """
        stats = {
            "memory_cache_entries": len(self.memory_cache),
            "memory_cache_max": self.max_memory_entries,
            "memory_usage_percent": (len(self.memory_cache) / self.max_memory_entries * 100) if self.max_memory_entries else 0,
            "disk_cache_entries": 0,
            "disk_cache_size_bytes": 0,
            "disk_cache_size_mb": 0,
            "by_data_type": {},
            "auto_cleanup_interval_seconds": self.cleanup_interval,
            "time_since_last_cleanup_seconds": int(time.time() - self.last_cleanup_time)
        }
        
        # Count disk cache entries and calculate size
        for filename in os.listdir(self.cache_dir):
            if not filename.endswith('.json'):
                continue
                
            cache_file = os.path.join(self.cache_dir, filename)
            
            file_size = os.path.getsize(cache_file)
            stats["disk_cache_entries"] += 1
            stats["disk_cache_size_bytes"] += file_size
            
            try:
                with open(cache_file, 'r') as f:
                    cache_entry = json.load(f)
                
                data_type = cache_entry.get("data_type", "default")
                if data_type not in stats["by_data_type"]:
                    stats["by_data_type"][data_type] = {
                        "count": 0,
                        "size_bytes": 0
                    }
                stats["by_data_type"][data_type]["count"] += 1
                stats["by_data_type"][data_type]["size_bytes"] += file_size
            except Exception:
                # Count corrupted files separately
                if "corrupted" not in stats["by_data_type"]:
                    stats["by_data_type"]["corrupted"] = {
                        "count": 0,
                        "size_bytes": 0
                    }
                stats["by_data_type"]["corrupted"]["count"] += 1
                stats["by_data_type"]["corrupted"]["size_bytes"] += file_size
        
        # Convert bytes to MB for easier reading
        stats["disk_cache_size_mb"] = round(stats["disk_cache_size_bytes"] / (1024 * 1024), 2)
        
        return stats
