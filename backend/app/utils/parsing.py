import re
from datetime import datetime
from typing import Any, Optional, Union
import logging

logger = logging.getLogger(__name__)

def try_parse_float(value: Any) -> Optional[float]:
    """Safely parse a value to float, handling various formats."""
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        # Remove currency symbols, commas, etc.
        cleaned_value = re.sub(r"[$,\s]", "", value)
        # Check for percentage and convert
        if cleaned_value.endswith("%"):
            try:
                return float(cleaned_value[:-1]) / 100.0
            except ValueError:
                return None
        try:
            return float(cleaned_value)
        except ValueError:
            return None
    return None

def try_parse_int(value: Any) -> Optional[int]:
    """Safely parse a value to int."""
    if value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        # Only convert if it's a whole number
        return int(value) if value.is_integer() else None
    if isinstance(value, str):
        # Remove commas and spaces
        cleaned_value = re.sub(r"[,\s]", "", value)
        try:
            # Handle potential float strings like "123.0"
            float_val = float(cleaned_value)
            return int(float_val) if float_val.is_integer() else None
        except ValueError:
            return None
    return None

def safe_parse_date(date_string: Optional[str]) -> Optional[datetime]:
    """Safely parse a date string into a datetime object."""
    if not date_string:
        return None
    
    # List common date formats
    formats = [
        "%Y-%m-%d %H:%M:%S",  # "2023-10-27 15:30:00"
        "%Y-%m-%d",          # "2023-10-27"
        "%m/%d/%Y",          # "10/27/2023"
        "%d-%b-%Y",          # "27-Oct-2023"
        "%B %d, %Y",         # "October 27, 2023"
        "%Y%m%d",            # "20231027"
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
            
    # Try ISO format directly
    try:
        return datetime.fromisoformat(date_string.replace('Z', '+00:00'))
    except ValueError:
        pass
        
    # Add more formats or flexible parsing if needed
    # Example: using dateutil parser (if installed)
    # try:
    #     from dateutil import parser
    #     return parser.parse(date_string)
    # except ImportError:
    #     pass # dateutil not installed
    # except ValueError:
    #     pass

    return None

# ... existing code ... 