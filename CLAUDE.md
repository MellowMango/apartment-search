# Acquire Project Development Guide

## Build & Test Commands
- Start services: `./run.sh`
- Backend tests: `cd backend && python -m pytest`
- Single test: `cd backend && python -m pytest tests/test_file.py::TestClass::test_method -v`
- Run scraper: `python run_BROKERNAME_scraper.py`
- Development server: `cd backend && uvicorn app.main:app --reload`
- Frontend dev: `cd frontend && npm run dev`

## Code Style Guidelines
- **Formatting**: Black (line length 88), isort for imports, flake8 for linting
- **Naming**: snake_case for variables/functions, PascalCase for classes, UPPER_CASE for constants
- **Imports**: stdlib first, third-party second, local modules last
- **Types**: Use type hints for all functions (parameters and returns)
- **Docstrings**: Google-style (Args, Returns, Examples sections)
- **Error handling**: Use specific exceptions, log errors, return {"success": False, "error": str(e)}
- **Async**: Use asyncio for I/O-bound operations, proper async/await patterns

## Project Organization
- Scrapers in `backend/scrapers/` directory follow base_scraper.py patterns
- Tests mirror the directory structure with "test_" prefix
- Keep functionality modular with clear service boundaries