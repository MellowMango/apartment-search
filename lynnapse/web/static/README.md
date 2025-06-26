# Lynnapse Web Interface Static Files

This directory contains static files for the Lynnapse web interface.

## Structure

- `css/` - Custom CSS files (if any)
- `js/` - Custom JavaScript files (if any)  
- `images/` - Images and icons
- `downloads/` - Downloaded scraping result files

## Note

This web interface is designed to be easily removable. To remove it:

1. Delete the entire `lynnapse/web/` directory
2. Remove web-related dependencies from `requirements.txt` if desired:
   - `fastapi`
   - `jinja2`
   - `python-multipart`

The core scraping functionality will remain unaffected. 