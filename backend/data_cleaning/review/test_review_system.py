#!/usr/bin/env python3
"""
Test Review System

This script demonstrates the property review system with sample data.
"""

import json
import os
import sys
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent.parent))

from backend.data_cleaning.review.property_review import PropertyReviewSystem

def create_sample_properties():
    """Create sample properties for testing."""
    properties = [
        # Regular property
        {
            "id": 1,
            "name": "Sunset Apartments",
            "address": "123 Main Street",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "units": 50,
            "year_built": 2005,
            "price": 5000000,
            "property_status": "ACTIVE",
            "property_type": "MULTIFAMILY",
            "broker_id": 1
        },
        # Duplicate of property 1 with slight variations
        {
            "id": 2,
            "name": "Sunset Apts",
            "address": "123 Main St",
            "city": "Austin",
            "state": "TX",
            "zip_code": "78701",
            "units": 52,
            "year_built": 2006,
            "price": 5100000,
            "property_status": "ACTIVE",
            "property_type": "MULTIFAMILY",
            "broker_id": 2
        },
        # Another regular property
        {
            "id": 3,
            "name": "Oak Ridge Office Building",
            "address": "456 Oak Avenue",
            "city": "Dallas",
            "state": "TX",
            "zip_code": "75201",
            "units": 0,
            "year_built": 1998,
            "price": 8000000,
            "property_status": "ACTIVE",
            "property_type": "OFFICE",
            "broker_id": 1
        },
        # Test property
        {
            "id": 4,
            "name": "Test Property",
            "address": "789 Test Street",
            "city": "Houston",
            "state": "TX",
            "zip_code": "77001",
            "units": 0,
            "year_built": 2020,
            "price": 1,
            "property_status": "ACTIVE",
            "property_type": "RETAIL",
            "broker_id": 3
        },
        # Invalid property (missing required fields)
        {
            "id": 5,
            "name": "Incomplete Property",
            "address": "",
            "city": "",
            "state": "",
            "zip_code": "",
            "units": 0,
            "year_built": 0,
            "price": 0,
            "property_status": "UNKNOWN",
            "property_type": "UNKNOWN",
            "broker_id": 3
        },
        # Another duplicate (of property 3)
        {
            "id": 6,
            "name": "Oak Ridge Offices",
            "address": "456 Oak Ave",
            "city": "Dallas",
            "state": "TX",
            "zip_code": "75201",
            "units": 0,
            "year_built": 1999,
            "price": 7900000,
            "property_status": "ACTIVE",
            "property_type": "OFFICE",
            "broker_id": 2
        }
    ]
    
    return properties

def main():
    """Main function to demonstrate the review system."""
    print("Property Review System Demonstration")
    print("===================================")
    
    # Create sample properties
    properties = create_sample_properties()
    print(f"Created {len(properties)} sample properties")
    
    # Save sample properties to file
    sample_dir = Path("data/sample")
    sample_dir.mkdir(parents=True, exist_ok=True)
    sample_file = sample_dir / "sample_properties.json"
    
    with open(sample_file, "w", encoding="utf-8") as f:
        json.dump(properties, f, indent=2)
    
    print(f"Saved sample properties to {sample_file}")
    
    # Initialize property review system
    review_system = PropertyReviewSystem(similarity_threshold=0.8)
    
    # Generate review candidates
    candidates = review_system.generate_review_candidates(properties)
    print(f"Generated {len(candidates)} review candidates")
    
    # Save review candidates to file
    review_dir = Path("data/review")
    review_dir.mkdir(parents=True, exist_ok=True)
    review_file = review_dir / "sample_review_candidates.json"
    
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)
    
    print(f"Saved review candidates to {review_file}")
    
    # Display review candidates
    review_system.display_review_candidates(candidates)
    
    # Simulate approving some candidates
    print("\nSimulating approval of some candidates...")
    
    # Find a duplicate candidate
    duplicate_candidate = None
    for candidate in candidates:
        if candidate["review_type"] == "duplicate":
            duplicate_candidate = candidate
            break
    
    if duplicate_candidate:
        # Approve the duplicate candidate
        candidates = review_system.update_candidate_status(
            candidates, 
            duplicate_candidate["review_id"], 
            True, 
            "Confirmed duplicate"
        )
        print(f"Approved duplicate candidate: {duplicate_candidate['review_id']}")
    
    # Find a test property candidate
    test_candidate = None
    for candidate in candidates:
        if candidate["review_type"] == "test_property":
            test_candidate = candidate
            break
    
    if test_candidate:
        # Approve the test property candidate
        candidates = review_system.update_candidate_status(
            candidates, 
            test_candidate["review_id"], 
            True, 
            "Confirmed test property"
        )
        print(f"Approved test property candidate: {test_candidate['review_id']}")
    
    # Find an invalid property candidate
    invalid_candidate = None
    for candidate in candidates:
        if candidate["review_type"] == "invalid_property":
            invalid_candidate = candidate
            break
    
    if invalid_candidate:
        # Disapprove the invalid property candidate
        candidates = review_system.update_candidate_status(
            candidates, 
            invalid_candidate["review_id"], 
            False, 
            "Will fix manually"
        )
        print(f"Disapproved invalid property candidate: {invalid_candidate['review_id']}")
    
    # Save updated candidates
    with open(review_file, "w", encoding="utf-8") as f:
        json.dump(candidates, f, indent=2)
    
    print(f"Saved updated candidates to {review_file}")
    
    # Display updated candidates
    print("\nUpdated review candidates:")
    review_system.display_review_candidates(candidates)
    
    # Display instructions for using the CLI
    print("\nTo use the review system CLI:")
    print(f"1. Generate candidates: python -m backend.data_cleaning.review.review_cli generate --file {sample_file}")
    print(f"2. Display candidates: python -m backend.data_cleaning.review.review_cli display --file {review_file}")
    print(f"3. Update candidate status: python -m backend.data_cleaning.review.review_cli update --file {review_file} --review-id <review_id> --approve")
    print(f"4. Apply approved actions: python -m backend.data_cleaning.review.review_cli apply --file {review_file}")

if __name__ == "__main__":
    main() 