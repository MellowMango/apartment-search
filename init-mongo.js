// MongoDB initialization script for Lynnapse
db = db.getSiblingDB('lynnapse');

// Create collections
db.createCollection('programs');
db.createCollection('faculty');
db.createCollection('lab_sites');
db.createCollection('scrape_jobs');

// Create indexes for better performance

// Program indexes
db.programs.createIndex({ "university_name": 1, "program_name": 1 }, { unique: true });
db.programs.createIndex({ "program_url": 1 });
db.programs.createIndex({ "scraped_at": 1 });

// Faculty indexes
db.faculty.createIndex({ "program_id": 1, "name": 1 });
db.faculty.createIndex({ "email": 1 });
db.faculty.createIndex({ "profile_url": 1 });
db.faculty.createIndex({ "scraped_at": 1 });

// Lab site indexes
db.lab_sites.createIndex({ "faculty_id": 1, "lab_url": 1 }, { unique: true });
db.lab_sites.createIndex({ "program_id": 1 });
db.lab_sites.createIndex({ "scraped_at": 1 });

// Scrape job indexes
db.scrape_jobs.createIndex({ "job_name": 1 });
db.scrape_jobs.createIndex({ "status": 1 });
db.scrape_jobs.createIndex({ "created_at": 1 });
db.scrape_jobs.createIndex({ "target_url": 1 });

print('Lynnapse database initialized with collections and indexes'); 