"""
Lynnapse - Adaptive University Faculty Scraper
"""

__version__ = "2.0.0"
__author__ = "Lynnapse Team"
__email__ = "team@lynnapse.com"

# Core exports
from .core import *
from .models import *

# Optional exports (may not be available in all environments)
try:
    from .flows import *
except ImportError:
    pass

try:
    from .web import *
except ImportError:
    pass