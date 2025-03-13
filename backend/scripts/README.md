# Database Scripts

This directory contains utility scripts for managing the Acquire Apartments database.

## Main Scripts

### `db_utils.py`

A comprehensive utility script for database management with the following commands:

- `check-connection`: Verify connections to Supabase and Neo4j
- `apply-schema`: Apply the schema to Supabase
- `verify-schema`: Verify the schema structure in Supabase
- `test-neo4j-sync`: Test Neo4j synchronization

Usage:
```bash
python db_utils.py check-connection
python db_utils.py apply-schema
python db_utils.py verify-schema
python db_utils.py test-neo4j-sync
```

### `check_schema.sql`

SQL script to check the database schema in Supabase. Run this in the Supabase SQL editor to verify:

- Tables in the public schema
- Primary keys
- Foreign key constraints
- Row Level Security policies
- Triggers
- Function existence
- Record counts

## Legacy Scripts

The following scripts are kept for reference but are superseded by `db_utils.py`:

- `test_neo4j_sync.py`: Original Neo4j sync test script
- `test_neo4j_sync_simple.py`: Simplified Neo4j sync test script
- `test_neo4j_client.py`: Test Neo4j client connection
- `test_neo4j_connection.py`: Test Neo4j connection
- `check_supabase_tables.py`: Check Supabase tables
- `apply_supabase_schema.py`: Apply Supabase schema
- `test_supabase_connection.py`: Test Supabase connection

## Schema Files

- `../schema.sql`: Main schema file for the Acquire Apartments database 