# Austin Multifamily Property Listing Map - Sprint Plan

## Sprint Day 1: Kickoff & Core Setup ✅

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 1.1 | **Finalize Requirements & User Stories**<br>Created user-stories.md with detailed personas, stories, and acceptance criteria | Completed | docs/user-stories.md |
| 1.2 | **Initialize Repo & Heroku Apps**<br>Created basic project structure, requirements.txt, package.json, and core application files | Completed | backend/, frontend/ |
| 1.3 | **Supabase Setup**<br>Created Supabase project, database schema with tables for properties, brokers, and user profiles, and integration code for both backend and frontend | Completed | docs/supabase-setup.md, backend/scripts/supabase_schema.sql |
| 1.4 | **Neo4j Aura Provisioning & Creds**<br>Created Neo4j setup guide, Neo4j client for graph database operations, and Celery tasks for syncing data from Supabase to Neo4j | Completed | docs/neo4j-setup.md, backend/app/db/neo4j_client.py |
| 1.5 | **Basic Env Setup & Dependencies**<br>Created environment setup script, installed Python and Node.js dependencies, and verified environment configuration | Completed | scripts/setup_environment.sh |

## Sprint Day 2: MCP Scraper Foundation 🔄

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 2.1 | **Data Model Draft (Property, Broker, etc.)**<br>Outline fields in code for Supabase & Neo4j synergy | Completed | backend/app/models/data_models.py, backend/app/models/README.md, backend/app/models/data_model_diagram.md |
| 2.2 | **MCP Server Setup & Integration**<br>Set up Firecrawl MCP server (primary), with MCP-Playwright and MCP-Puppeteer as alternatives; create integration with FastAPI backend | Completed | backend/app/services/mcp_client.py, backend/app/services/mcp_scraper.py, scripts/run_mcp_server.sh, scripts/test_mcp_simple.py |
| 2.3 | **LLM-Guided Scraping Prototype**<br>Develop prototype for LLM-guided navigation of broker websites using Firecrawl MCP, test on 2-3 major Austin broker sites | Not Started | |
| 2.4 | **MCP Scraper to Supabase Integration**<br>Hook the Firecrawl MCP scraping & email tasks to store extracted property data in Supabase | Not Started | |
| 2.5 | **Email Retrieval Skeleton (imaplib)**<br>Connect to a test email inbox, retrieve messages; no OCR yet | Not Started | |

## Sprint Day 3: Supabase & CRUD Implementation ✅

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 3.1 | **Implement Supabase Tables & Relationships**<br>Created comprehensive database schema with tables for properties, brokers, brokerages, users, subscriptions, and relationships between them | Completed | backend/schema.sql, backend/scripts/create_brokerages_table.sql |
| 3.2 | **FastAPI CRUD Endpoints**<br>/properties, /properties/{id}, /users, etc. with create/read/update/delete | Completed | backend/app/api/api_v1/endpoints/ |
| 3.3 | **Supabase Auth Integration**<br>Set up email authentication and OAuth with Supabase | Completed | backend/app/services/auth_service.py, backend/app/api/api_v1/endpoints/auth.py, frontend/src/contexts/AuthContext.js |
| 3.4 | **SendGrid Integration & Email Templates**<br>Set up SendGrid API, create email templates for welcome, password reset, and notifications | Completed | backend/app/services/auth_service.py, backend/.env |
| 3.6 | **Basic Testing (pytest)**<br>Simple tests for CRUD endpoints and MCP scraping tasks | Completed | backend/tests/api/api_v1/endpoints/ |

## Sprint Day 4: Neo4j Aura Sync & Graph Queries ✅

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 4.1 | **Neo4j Python Driver & Connection**<br>Store credentials in Heroku config, test Cypher queries from FastAPI | Completed | backend/app/db/neo4j_client.py |
| 4.2 | **Supabase → Neo4j Sync Tasks (Celery)**<br>Created service functions for syncing data from Supabase to Neo4j, implemented in app/services/neo4j_sync.py | Completed | backend/app/services/neo4j_sync.py, backend/app/workers/tasks/neo4j_sync.py |
| 4.3 | **Graph Query Endpoint in FastAPI**<br>Implemented endpoints for related properties and broker networks using Neo4j graph queries | Completed | backend/app/api/api_v1/endpoints/properties.py, backend/app/api/api_v1/endpoints/brokers.py |
| 4.4 | **Validation & Basic Graph Testing**<br>Created test script to validate data consistency across Supabase & Neo4j; successfully tested with sample properties and brokers | Completed | backend/scripts/test_neo4j_sync.py |

## Sprint Day 5: Frontend Scaffold (Next.js) 🔄

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 5.1 | **Next.js Project Initialization**<br>Set up Next.js project with appropriate folder structure | Not Started | |
| 5.2 | **Context API Setup**<br>Implement React Context for state management | Not Started | |
| 5.3 | **Basic UI Layout (Header, Nav, Footer)**<br>Implement Acquire Apartments branding with Tailwind CSS or Material-UI | Not Started | |
| 5.4 | **Supabase Client Integration**<br>Set up client-side data fetching from Supabase | Not Started | |
| 5.5 | **Setup Next.js Routing**<br>Configure routing for Home, MapView, Admin, etc. | Not Started | |
| 5.6 | **Authentication Pages**<br>Create login, register, reset-password, and account pages | Not Started | |

## Sprint Day 6: Map & Sidebar 🔄

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 6.1 | **react-leaflet Integration**<br>Display Austin map, load property markers from Context | Not Started | |
| 6.2 | **Sidebar with Property List**<br>Scrollable list of properties; on marker or list click, show property summary | Not Started | |
| 6.3 | **Marker Info Panels & Basic UI Polish**<br>Hover or click markers for quick summary; refine styling with Acquire Apartments branding | Not Started | |
| 6.4 | **Preliminary End-to-End Testing**<br>Verify data flow: Firecrawl MCP scraper → Supabase → Neo4j → API → Next.js map/list | Not Started | |

## Sprint Day 7: Search, Filter & Real-Time Updates 🔄

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 7.1 | **Search & Filter Implementation**<br>Filter by property status, year built, etc.; refresh map & sidebar | Not Started | |
| 7.2 | **Socket.IO Real-Time Setup**<br>Add Socket.IO server to FastAPI; broadcast property status changes | Not Started | |
| 7.3 | **Socket.IO Client in Next.js**<br>Listen for "property-updated" event; update Context state | Not Started | |
| 7.4 | **Verify Real-Time Flow**<br>Manual test: update property in Supabase → triggers Celery → notifies Socket.IO → Next.js updates | Not Started | |

## Sprint Day 8: MCP Scraper & Email Agents Finalization 🔄

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 8.1 | **MCP Scraping Enhancements**<br>Refine LLM prompts for Firecrawl MCP for more accurate data extraction, implement error handling and recovery strategies | Not Started | |
| 8.2 | **Email Processing w/ OCR**<br>Implement pytesseract for images in emails, parse property details, store in DB | Not Started | |
| 8.3 | **Error Handling & Logging**<br>Sentry or standard logging for Firecrawl MCP scraper errors, queue retries | Not Started | |
| 8.4 | **Testing MCP Scrapers**<br>Test real broker sites to confirm Firecrawl MCP accuracy and resilience | Not Started | |

## Sprint Day 9: Admin & Missing Info 🔄

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 9.1 | **Admin UI & Authentication**<br>Secure admin routes using Supabase auth; manage scraping targets, logs, missing info queue | Not Started | |
| 9.2 | **Missing Info Detection & Emails**<br>Track incomplete fields, weekly Celery job sends broker requests via SendGrid; admin can review & approve updates | Not Started | |
| 9.3 | **Data Corrections Submission**<br>Let users submit corrections, queue for admin review; final updates in Supabase & Neo4j | Not Started | |
| 9.4 | **Integration Testing for Admin Flows**<br>Ensure Firecrawl MCP scraper tasks + admin overrides + property updates flow seamlessly | Not Started | |

## Sprint Day 10: Payment Integration & Final QA 🔄

| Task | Description | Status | File Context |
|------|-------------|--------|--------------|
| 10.1 | **Stripe Integration**<br>Set up Stripe API, create subscription products and prices, implement webhook handling | Not Started | |
| 10.2 | **Subscription UI & User Flow**<br>Create subscription pages, checkout process, and account management for subscriptions | Not Started | |
| 10.3 | **Paywall Implementation**<br>Restrict access to detailed property information based on subscription status | Not Started | |
| 10.4 | **Unit & Integration Tests**<br>Expand coverage (pytest, Jest); ensure Firecrawl MCP scraper concurrency & map rendering are stable | Not Started | |
| 10.5 | **Basic Analytics & CSV Export**<br>Summaries of active listings, average metrics; CSV export from Supabase or Neo4j queries | Not Started | |
| 10.6 | **Deployment**<br>Deploy backend to Heroku (web dyno + Celery worker)<br>Deploy Next.js frontend to Vercel or Heroku | Not Started | |
| 10.7 | **Final Verification & Handover**<br>Confirm Firecrawl MCP scrapers run on schedule, real-time updates flow, data integrity across DBs, final handoff | Not Started | |