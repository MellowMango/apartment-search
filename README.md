# Aquire Apartments

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
│   │   ├── db/             # Database models and connections
│   │   ├── models/         # Pydantic models
│   │   ├── schemas/        # Pydantic schemas
│   │   ├── services/       # Business logic
│   │   └── workers/        # Celery tasks
│   └── requirements.txt    # Python dependencies
├── frontend/               # Next.js frontend
│   ├── public/             # Static files
│   ├── src/                # Source code
│   │   ├── components/     # React components
│   │   ├── contexts/       # React contexts
│   │   ├── pages/          # Next.js pages
│   │   └── styles/         # CSS styles
│   └── package.json        # Node.js dependencies
├── docs/                   # Documentation
├── .env.example            # Example environment variables
└── README.md               # Project documentation
```

## Documentation

For more detailed documentation, see the [docs](./docs) directory:

- [Project Overview](./docs/project-overview.md)
- [Tech Stack](./docs/tech-stack.md)
- [Sprint Plan](./docs/sprint.md)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [OpenStreetMap](https://www.openstreetmap.org/) for map data
- [Leaflet](https://leafletjs.com/) for the interactive map library
- [Supabase](https://supabase.io/) for authentication and database services
- [Neo4j](https://neo4j.com/) for graph database services 