-- Initialize PostgreSQL database
-- This script is run by Docker when the container starts

-- Create extensions (if not already created)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- The database and user are already created by Docker environment variables
-- POSTGRES_USER=healthtrack
-- POSTGRES_PASSWORD=healthtrack
-- POSTGRES_DB=healthtrack_db

-- Create any additional schemas if needed
CREATE SCHEMA IF NOT EXISTS public;

GRANT ALL PRIVILEGES ON SCHEMA public TO healthtrack;
