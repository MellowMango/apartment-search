# Property Data Cleaning System

This module provides a comprehensive system for cleaning property data, including deduplication, standardization, and validation.

## Features

- **Deduplication**: Identify and merge duplicate properties across different brokers using fuzzy matching on addresses, names, and other attributes.
- **Standardization**: Normalize property attributes (types, statuses, etc.) into consistent formats.
- **Validation**: Ensure data quality by validating critical fields.
- **Test Property Detection**: Identify and remove test/example properties that don't represent real listings.
- **Database Integration**: Fetch properties from and update properties in the Supabase database.
- **Two-Step Approval Process**: Review and approve data cleaning actions before they are applied to the database.
- **Scheduled Cleaning**: Run cleaning tasks on a schedule using Celery.

## Installation

1. Install the required dependencies:

```bash
pip install -r requirements.txt
```

2. Ensure environment variables are set up for database access:

```
SUPABASE_URL=your_supabase_url
SUPABASE_SERVICE_ROLE_KEY=your_supabase_service_role_key
CELERY_BROKER_URL=your_celery_broker_url
CELERY_RESULT_BACKEND=your_celery_result_backend
```

## Usage

### Two-Step Approval Process

The system implements a two-step approval process to ensure that no write actions occur without explicit approval:

1. **Generate Review Candidates**:
   ```bash
   python -m backend.data_cleaning.test_real_db --test review
   ```
   This identifies properties that need attention (duplicates, invalid properties, test properties) and saves them to a file.

2. **Review and Approve Candidates**:
   ```bash
   python -m backend.data_cleaning.review_and_approve display path/to/candidates.json
   ```
   This displays the candidates for review.

3. **Update Candidate Status**:
   ```bash
   python -m backend.data_cleaning.review_and_approve update path/to/candidates.json candidate_id --approve
   ```
   This approves a candidate for action. Use `--disapprove` to reject a candidate.

4. **Generate Pending Actions**:
   ```bash
   python -m backend.data_cleaning.review_and_approve actions path/to/candidates.json --output path/to/actions.json
   ```
   This generates pending actions for approved candidates.

5. **Execute Pending Actions**:
   ```bash
   python -m backend.data_cleaning.review_and_approve execute path/to/actions.json --confirm
   ```
   This executes the pending actions after explicit confirmation.

### Command-Line Interface

The system also provides a command-line interface for testing and running the data cleaning system:

```bash
# Test database connection
python -m backend.data_cleaning.test_real_db --test connection

# Test property metadata operations
python -m backend.data_cleaning.test_real_db --test metadata

# Test review system
python -m backend.data_cleaning.test_real_db --test review

# Test two-step approval process
python -m backend.data_cleaning.test_real_db --test approval

# Run all tests
python -m backend.data_cleaning.test_real_db --test all
```

### Programmatic Usage

```python
from backend.data_cleaning.database.db_operations import DatabaseOperations
from backend.data_cleaning.review.property_review import PropertyReviewSystem

# Initialize components
db_ops = DatabaseOperations()
review_system = PropertyReviewSystem()

# Fetch properties from the database
properties = db_ops.fetch_all_properties()

# Generate review candidates
candidates = review_system.generate_review_candidates(properties)

# Save candidates to file
filepath = review_system.save_review_candidates(candidates)

# Display candidates
review_system.display_review_candidates(candidates)

# Update candidate status
candidates = review_system.update_candidate_status(candidates, "review_id_123", approved=True, notes="Looks good")

# Generate pending actions
results = review_system.apply_approved_actions(candidates, db_ops)
pending_actions = results["pending_actions"]

# Execute pending actions (after explicit confirmation)
results = review_system.execute_approved_actions(pending_actions, db_ops)
```

### Scheduled Tasks

The system includes Celery tasks for scheduled data cleaning:

- `clean_all_properties`: Cleans all properties in the database (runs daily at 2:00 AM).
- `clean_new_properties`: Cleans new properties added in the last hour (runs hourly).

To start the Celery worker:

```bash
celery -A backend.data_cleaning.scheduled.cleaning_tasks worker --loglevel=info
```

To start the Celery beat scheduler:

```bash
celery -A backend.data_cleaning.scheduled.cleaning_tasks beat --loglevel=info
```

## Module Structure

- `database/db_operations.py`: Database operations for data cleaning.
- `deduplication/property_matcher.py`: Algorithms for identifying duplicate properties.
- `standardization/property_standardizer.py`: Rules for standardizing property attributes.
- `validation/property_validator.py`: Rules for validating property data.
- `review/property_review.py`: System for reviewing and approving data cleaning actions.
- `review_and_approve.py`: Command-line interface for the two-step approval process.
- `test_real_db.py`: Test script for verifying data cleaning functionality.
- `scheduled/`: Modules for scheduled data cleaning tasks.

## Configuration

The system can be configured through various parameters:

- `similarity_threshold`: Threshold for considering properties as duplicates (0.0 to 1.0).
- Validation rules in `PropertyValidator`.
- Standardization mappings in `PropertyStandardizer`.
- Celery task schedules in `cleaning_tasks.py`.

## Logging

The system logs detailed information about the cleaning process, including:

- Properties standardized, validated, and deduplicated.
- Duplicate groups found.
- Test properties removed.
- Database operations performed.
- Review and approval actions.

Logs are written to both the console and a log file (`property_review.log`). 