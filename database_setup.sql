-- Create the database if it doesn't already exist
CREATE DATABASE IF NOT EXISTS sentinel_db;
USE sentinel_db;

-- Create the emergency reports table mapping the Gemini extraction keys
CREATE TABLE IF NOT EXISTS emergency_reports (
    id VARCHAR(255) PRIMARY KEY,
    situation_id VARCHAR(255),
    report_date VARCHAR(50),
    report_time VARCHAR(50),
    emergency_category VARCHAR(100),
    emergency_sub_type VARCHAR(100),
    incident_description TEXT,
    reporter_type VARCHAR(100),
    caller_name VARCHAR(255),
    caller_contact_number VARCHAR(50),
    caller_gender VARCHAR(50),
    state VARCHAR(100),
    district_city VARCHAR(100),
    locality_area VARCHAR(255),
    pin_code VARCHAR(50),
    latitude FLOAT,
    longitude FLOAT,
    severity_level VARCHAR(50),
    threat_to_human_life VARCHAR(50),
    number_of_casualties INT,
    number_of_injuries INT,
    weapon_hazard_involved VARCHAR(255),
    dispatch_needed BOOLEAN,
    dispatch_reason TEXT,
    conversation_history JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
