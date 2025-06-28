#!/usr/bin/env python3
"""
Cache Manager for LLM Discoveries

This utility helps manage the persistent cache of LLM university discoveries.
"""

import asyncio
import json
import time
from pathlib import Path
from typing import List, Dict, Any
import argparse

def list_cached_discoveries() -> List[Dict[str, Any]]:
    """List all cached discoveries."""
    cache_dir = Path("cache/llm_discoveries")
    
    if not cache_dir.exists():
        print("📂 No cache directory found.")
        return []
    
    discoveries = []
    for cache_file in cache_dir.glob("*.json"):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
            
            # Calculate age
            discovery_time = data.get('discovery_timestamp', 0)
            age_hours = (time.time() - discovery_time) / 3600 if discovery_time else 0
            
            discoveries.append({
                'cache_key': cache_file.stem,
                'file_name': cache_file.name,
                'discovery_date': time.strftime('%Y-%m-%d %H:%M:%S', 
                                               time.localtime(discovery_time)) if discovery_time else 'Unknown',
                'age_hours': age_hours,
                'faculty_paths': data.get('faculty_directory_paths', []),
                'department_paths': data.get('department_paths', []),
                'confidence': data.get('confidence_score', 0),
                'cost': data.get('cost_estimate', 0),
                'reasoning': data.get('reasoning', 'No reasoning provided')
            })
        except Exception as e:
            print(f"⚠️  Failed to read cache file {cache_file}: {e}")
    
    return sorted(discoveries, key=lambda x: x['age_hours'])

def show_cache_summary():
    """Show a summary of cached discoveries."""
    discoveries = list_cached_discoveries()
    
    if not discoveries:
        print("📂 No cached discoveries found.")
        return
    
    print(f"📊 CACHE SUMMARY")
    print("=" * 50)
    print(f"Total cached discoveries: {len(discoveries)}")
    
    total_cost = sum(d['cost'] for d in discoveries)
    print(f"Total LLM cost saved: ${total_cost:.4f}")
    
    # Group by age
    fresh = len([d for d in discoveries if d['age_hours'] < 24])
    old = len([d for d in discoveries if d['age_hours'] >= 24])
    
    print(f"Fresh (< 24h): {fresh}")
    print(f"Old (>= 24h): {old}")
    print()

def show_cache_details():
    """Show detailed information about cached discoveries."""
    discoveries = list_cached_discoveries()
    
    if not discoveries:
        print("📂 No cached discoveries found.")
        return
    
    print(f"📋 CACHED DISCOVERIES")
    print("=" * 50)
    
    for i, discovery in enumerate(discoveries, 1):
        print(f"{i}. 🗂️  {discovery['cache_key']}")
        print(f"   📅 Date: {discovery['discovery_date']}")
        print(f"   ⏰ Age: {discovery['age_hours']:.1f} hours")
        print(f"   🎯 Faculty Paths ({len(discovery['faculty_paths'])}): {discovery['faculty_paths']}")
        if discovery['department_paths']:
            print(f"   🏫 Department Paths: {discovery['department_paths']}")
        print(f"   📊 Confidence: {discovery['confidence']:.2f}")
        print(f"   💰 Cost: ${discovery['cost']:.4f}")
        print(f"   💭 Reasoning: {discovery['reasoning'][:100]}...")
        print()

def clean_expired_cache(hours: float = 24.0):
    """Clean expired cache entries."""
    cache_dir = Path("cache/llm_discoveries")
    
    if not cache_dir.exists():
        print("📂 No cache directory found.")
        return
    
    discoveries = list_cached_discoveries()
    expired = [d for d in discoveries if d['age_hours'] >= hours]
    
    if not expired:
        print(f"🧹 No expired cache entries found (older than {hours} hours).")
        return
    
    print(f"🧹 CLEANING EXPIRED CACHE")
    print(f"Found {len(expired)} expired entries (older than {hours} hours):")
    
    for discovery in expired:
        cache_file = cache_dir / discovery['file_name']
        try:
            cache_file.unlink()
            print(f"   ✅ Deleted: {discovery['cache_key']} (age: {discovery['age_hours']:.1f}h)")
        except Exception as e:
            print(f"   ❌ Failed to delete {discovery['cache_key']}: {e}")
    
    print(f"\n🧹 Cleanup complete!")

def clean_all_cache():
    """Clean all cache entries."""
    cache_dir = Path("cache/llm_discoveries")
    
    if not cache_dir.exists():
        print("📂 No cache directory found.")
        return
    
    cache_files = list(cache_dir.glob("*.json"))
    
    if not cache_files:
        print("🧹 No cache files found.")
        return
    
    print(f"🧹 CLEANING ALL CACHE")
    print(f"Found {len(cache_files)} cache files:")
    
    for cache_file in cache_files:
        try:
            cache_file.unlink()
            print(f"   ✅ Deleted: {cache_file.name}")
        except Exception as e:
            print(f"   ❌ Failed to delete {cache_file.name}: {e}")
    
    print(f"\n🧹 All cache cleared!")

def main():
    """Main CLI interface."""
    parser = argparse.ArgumentParser(description="Manage LLM discovery cache")
    parser.add_argument('action', choices=['list', 'summary', 'clean', 'clean-all'], 
                       help='Action to perform')
    parser.add_argument('--hours', type=float, default=24.0,
                       help='Hours threshold for cleaning expired cache (default: 24)')
    
    args = parser.parse_args()
    
    if args.action == 'list':
        show_cache_details()
    elif args.action == 'summary':
        show_cache_summary()
    elif args.action == 'clean':
        clean_expired_cache(args.hours)
    elif args.action == 'clean-all':
        response = input("⚠️  Are you sure you want to delete ALL cached discoveries? (y/N): ")
        if response.lower() == 'y':
            clean_all_cache()
        else:
            print("❌ Cancelled.")

if __name__ == "__main__":
    main() 