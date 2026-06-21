-- 1. Create a brand new top-level catalog
CREATE CATALOG IF NOT EXISTS portfolio_catalog;

-- 2. Set it as the active catalog
USE CATALOG portfolio_catalog;

-- 3. Create the schema (database) inside your new catalog
CREATE SCHEMA IF NOT EXISTS compliance_project;

-- 4. Create the volume for your raw CSV files
CREATE VOLUME IF NOT EXISTS compliance_project.raw_data;