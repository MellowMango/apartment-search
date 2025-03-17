# Using the Data Cleaning System with a Real Database

This guide explains how to use the data cleaning system with a real Supabase database for the Acquire Apartments platform.

## Prerequisites

1. Supabase project with the required tables (properties, brokers, etc.)
2. Environment variables set up with Supabase credentials:
   - `SUPABASE_URL`
   - `SUPABASE_SERVICE_ROLE_KEY`

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Apply the database schema updates to create the necessary tables for the data cleaning system:

```bash
python -m backend.data_cleaning.database.apply_schema_updates
```

This will create the following tables:
- `cleaning_logs`: For storing logs of cleaning operations
- `property_review_candidates`: For storing property review candidates
- `property_metadata`: For storing metadata about properties

## Testing the Connection

To test the connection to the database and verify that everything is set up correctly:

```bash
python -m backend.data_cleaning.test_real_db --test connection
```

## Data Cleaning Workflow

The data cleaning system follows a human-in-the-loop approach, where potential issues are identified and presented for review before any actions are taken.

### 1. Generate Review Candidates

First, generate review candidates by analyzing properties in the database:

```bash
# Generate candidates for all properties
python -m backend.data_cleaning.review.review_cli generate

# Generate candidates for a specific broker
python -m backend.data_cleaning.review.review_cli generate --broker-id <broker_id>

# Generate candidates from a JSON file
python -m backend.data_cleaning.review.review_cli generate --file <path_to_properties.json>
```

This will:
1. Analyze properties for duplicates, test properties, and validation issues
2. Generate review candidates
3. Save the candidates to a JSON file in the `data/review/` directory
4. Also save the candidates to the `property_review_candidates` table in the database

### 2. Display Review Candidates

To view the generated candidates:

```bash
python -m backend.data_cleaning.review.review_cli display --file <path_to_candidates.json>
```

This will display the candidates in a tabular format, grouped by type (duplicate, test, invalid).

### 3. Review and Approve/Disapprove Candidates

Review each candidate and decide whether to approve or disapprove the proposed action:

```bash
# Approve a candidate
python -m backend.data_cleaning.review.review_cli update --file <path_to_candidates.json> --review-id <review_id> --approve --notes "Reason for approval"

# Disapprove a candidate
python -m backend.data_cleaning.review.review_cli update --file <path_to_candidates.json> --review-id <review_id> --disapprove --notes "Reason for disapproval"
```

This will:
1. Update the candidate's status in the JSON file
2. Update the candidate's status in the `property_review_candidates` table

### 4. Apply Approved Actions

Once you've reviewed all candidates, apply the approved actions to the database:

```bash
python -m backend.data_cleaning.review.review_cli apply --file <path_to_candidates.json>
```

This will:
1. Apply the approved actions to the database (merge duplicates, delete test properties, flag invalid properties)
2. Mark the candidates as applied in the `property_review_candidates` table
3. Log the actions in the `cleaning_logs` table

## Property Metadata

The system uses the `property_metadata` table to store additional information about properties, such as:

- `flagged`: Whether the property has been flagged for review
- `flag_reason`: The reason the property was flagged
- `deletion_reason`: The reason the property was deleted
- `source_broker_ids`: The broker IDs that provided the property (for merged properties)

This metadata can be accessed programmatically:

```python
from backend.data_cleaning.database.db_operations import DatabaseOperations

db_ops = DatabaseOperations()
is_flagged = db_ops.get_property_metadata(property_id, "flagged")
flag_reason = db_ops.get_property_metadata(property_id, "flag_reason")
```

## Scheduled Cleaning

You can set up scheduled cleaning tasks using Celery:

1. Create a Celery task that generates review candidates
2. Schedule the task to run periodically
3. Notify administrators when new candidates are available for review

## Troubleshooting

If you encounter issues:

1. Check that your environment variables are set correctly
2. Verify that the database schema updates were applied successfully
3. Check the logs for error messages
4. Run the test script to verify the connection and functionality:

```bash
python -m backend.data_cleaning.test_real_db
``` 