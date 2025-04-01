# Acquire Apartments

A comprehensive web application for tracking multifamily property listings in Austin, Texas.

## Project Overview

Acquire Apartments is a web-based application designed to aggregate and display active listings of multifamily properties for sale in Austin, Texas. This tool aims to provide real estate investors, brokers, and other industry professionals with a comprehensive, up-to-date view of the Austin multifamily market.

## Features

- Interactive map showing all active multifamily property listings
- Detailed property information (units, year built, status, etc.)
- Automated data aggregation from broker emails and websites
- Search and filter functionality
- Real-time updates for property status changes
- User accounts and subscription management
- Admin interface for managing data

## Architecture

This project follows a layered architecture with the following components:

- **API Layer**: Handles HTTP requests, authentication, and routing
- **Processing Layer**: Contains business logic and data transformation
- **Storage Layer**: Abstracts database operations using the Repository pattern
- **Collection Layer**: Handles data collection from external sources
- **Scheduled Layer**: Contains scheduled tasks and background jobs

See the [Architecture Migration Plan](./docs/architecture/architecture-migration-plan.md) for details on our architectural vision and implementation.

## Data Access Patterns

We use the Repository pattern to standardize database access. Key patterns include:

- **Repository Interfaces**: Define consistent contracts for data access
- **Repository Implementations**: Concrete implementations for different storage backends
- **Factory Pattern**: Creates appropriate repository instances

See the [Repository Pattern Guide](./docs/architecture/repository-pattern.md) and [Data Access Patterns Guide](./docs/architecture/data-access-patterns.md) for details.

## Tech Stack

### Frontend
- Next.js (React-based framework)
- React Context API for state management
- Tailwind CSS for styling
- react-leaflet for the interactive map
- Socket.IO client for real-time updates

### Backend
- FastAPI (Python)
- Supabase for authentication and database
- Neo4j Aura for graph database
- Celery with Redis for background tasks
- SendGrid for email notifications
- Stripe for payment processing

## Getting Started

### Prerequisites

- Node.js (v16+)
- Python (v3.9+)
- Redis
- PostgreSQL (via Supabase)
- Neo4j (via Neo4j Aura)

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/austin-multifamily-map.git
   cd austin-multifamily-map
   ```

2. Set up the backend:
   ```
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Set up the frontend:
   ```
   cd frontend
   npm install
   ```

4. Create a `.env` file in the root directory based on `.env.example`

5. Start the development servers:
   
   Backend:
   ```
   cd backend
   uvicorn app.main:app --reload
   ```
   
   Frontend:
   ```
   cd frontend
   npm run dev
   ```

6. Open [http://localhost:3000](http://localhost:3000) in your browser

## Project Structure

```
├── backend/                # FastAPI backend
│   ├── app/                # Application code
│   │   ├── api/            # API endpoints
│   │   ├── core/           # Core functionality
│   │   ├── db/             # Database repositories and connections
│   │   ├── interfaces/     # Interface definitions
│   │   ├── models/         # Pydantic models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   ├── adapters/       # Adapters for data conversion
│   │   ├── utils/          # Utilities including architecture helpers
│   │   └── workers/        # Celery tasks
│   ├── scrapers/           # Scraper architecture
│   │   ├── core/           # Shared scraper utilities
│   │   ├── brokers/        # Broker-specific scrapers
│   │   ├── helpers/        # Helper utilities
│   │   └── run_scraper.py  # Command-line interface
│   ├── data_cleaning/      # Data cleaning components
│   ├── data_enrichment/    # Data enrichment components
│   ├── scripts/            # Utility scripts
│   │   ├── architecture/   # Architecture test scripts
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── public/             # Static files
│   ├── src/                # Source code
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts
│   │   ├── pages/          # Next.js pages
│   │   └── styles/         # CSS styles
│   └── package.json        # Node.js dependencies
├── data/                   # Generated data
├── docs/                   # Documentation
│   ├── architecture/       # Architecture documentation
├── .env.example            # Example environment variables
└── README.md               # Project documentation
```

## Documentation

For more detailed documentation, see the [docs](./docs) directory:

- [Project Overview](./docs/project-overview.md)
- [Tech Stack](./docs/tech-stack.md)
- [Sprint Plan](./docs/sprint.md)
- [Architecture Migration Plan](./docs/architecture/architecture-migration-plan.md)
- [Repository Pattern Guide](./docs/architecture/repository-pattern.md)
- [Data Access Patterns](./docs/architecture/data-access-patterns.md)
- [Scraper Architecture](./docs/scraper-architecture.md)
- [Scraper Usage Guide](./docs/scraper-usage-guide.md)

## TypeScript Migration

The codebase is currently in the process of being migrated from JavaScript to TypeScript. Currently, approximately 85% of the codebase has been migrated. The migration uses a feature flag system to allow for graceful transition between JavaScript and TypeScript implementations.

### Development Mode

During development, you can choose which implementation to use:

```bash
# Run with JavaScript implementation (default)
npm run dev

# Run with TypeScript implementation
npm run dev:ts
```

### Testing Both Implementations

To test both implementations side by side, you can use the provided script:

```bash
# From the project root
./scripts/test-ts-migration.sh
```

This will launch both versions in separate terminals and open your browser to both versions for testing.

### Migration Documentation

For more information about the TypeScript migration, see these documents:

- [TypeScript Migration Progress](./docs/ts-migration-progress.md) - Current status and progress tracking
- [TypeScript Migration Guide](./docs/typescript-migration-guide.md) - Comprehensive guide for the migration process
- [TypeScript Migration Tests](./docs/ts-migration-tests.md) - Test cases for verifying TypeScript implementations
- [TypeScript Cleanup Plan](./docs/typescript-cleanup-plan.md) - Process for removing JavaScript files after migration

### Migration Status

The following components have been migrated to TypeScript:
- ✅ Authentication workflow (Login, Signup, Reset Password)
- ✅ All contexts (Auth, Filter, Theme)
- ✅ Map page and MapComponent
- ✅ Index page
- ✅ Property List component
- ✅ UI Components (Button, Card, etc.)
- 🚧 Admin pages (partially completed)
- 🚧 Filter components (in progress)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [OpenStreetMap](https://www.openstreetmap.org/) for map data
- [Leaflet](https://leafletjs.com/) for the interactive map library
- [Supabase](https://supabase.io/) for authentication and database services
- [Neo4j](https://neo4j.com/) for graph database services