-- Database Schema for Crop Yield Advisory Analytics
-- College Mini-Project (50-60% Implementation Stage)

CREATE DATABASE IF NOT EXISTS crop_yield_advisory;
USE crop_yield_advisory;

-- 1. Table structure for agricultural_data
DROP TABLE IF EXISTS agricultural_data;

CREATE TABLE agricultural_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    crop_type VARCHAR(50) NOT NULL,
    soil VARCHAR(50) DEFAULT 'Unknown',
    rainfall FLOAT DEFAULT NULL,
    temperature FLOAT DEFAULT NULL,
    fertilizer FLOAT DEFAULT NULL,
    irrigation VARCHAR(50) DEFAULT 'Unknown',
    yield_value FLOAT NOT NULL,
    location VARCHAR(100) DEFAULT 'Unknown',
    season VARCHAR(50) DEFAULT 'Unknown',
    source_dataset VARCHAR(150) DEFAULT 'Sample Dataset',
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Table structure for dataset_sources tracking metadata
DROP TABLE IF EXISTS dataset_sources;

CREATE TABLE dataset_sources (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dataset_name VARCHAR(150) NOT NULL,
    source_name VARCHAR(100) NOT NULL,
    source_url VARCHAR(255),
    import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    record_count INT DEFAULT 0,
    available_fields VARCHAR(255),
    quality_score FLOAT DEFAULT 100.0,
    status VARCHAR(50) DEFAULT 'Imported'
);

