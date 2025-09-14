-- Database initialization script for PostgreSQL
-- This script creates the initial database structure for the hockey pickup manager

-- Create database if it doesn't exist (handled by Docker environment variables)
-- CREATE DATABASE IF NOT EXISTS hockey_pickup_dev;

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Note: The actual table creation will be handled by Flask-Migrate
-- This file is for any initial data or database-level configurations

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- This function will be used by triggers on tables with updated_at columns
