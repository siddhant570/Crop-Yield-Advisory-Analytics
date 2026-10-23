"""
Database Configuration & Connection Handler
Provides MySQL connection with automatic fallback to SQLite/CSV for college project execution.
Supports dynamic dataset tracking and environment variable configuration.
"""

import os
import sqlite3
import pandas as pd

# Load credentials from environment variables or use sensible defaults
MYSQL_HOST = os.getenv("DB_HOST", os.getenv("MYSQL_HOST", "localhost"))
MYSQL_USER = os.getenv("DB_USER", os.getenv("MYSQL_USER", "root"))
MYSQL_PASSWORD = os.getenv("DB_PASSWORD", os.getenv("MYSQL_PASSWORD", ""))
MYSQL_DB = os.getenv("DB_NAME", os.getenv("MYSQL_DB", "crop_yield_advisory"))
MYSQL_PORT = int(os.getenv("DB_PORT", "3306"))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CSV_PATH = os.path.join(BASE_DIR, "data", "agricultural_data.csv")
SQLITE_DB_PATH = os.path.join(os.path.dirname(__file__), "crop_yield_advisory.db")

_MYSQL_TESTED = False
_MYSQL_AVAILABLE = False

def get_db_connection():
    """
    Attempts to connect to MySQL. If MySQL is unavailable, returns a connection to SQLite fallback DB.
    Returns: (conn, is_mysql)
    """
    global _MYSQL_TESTED, _MYSQL_AVAILABLE

    # 1. Try MySQL Connection if not previously failed
    if not _MYSQL_TESTED:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                port=MYSQL_PORT,
                connection_timeout=1
            )
            if conn.is_connected():
                _MYSQL_AVAILABLE = True
                _MYSQL_TESTED = True
                return conn, True
        except Exception:
            _MYSQL_AVAILABLE = False
            _MYSQL_TESTED = True
    elif _MYSQL_AVAILABLE:
        try:
            import mysql.connector
            conn = mysql.connector.connect(
                host=MYSQL_HOST,
                user=MYSQL_USER,
                password=MYSQL_PASSWORD,
                database=MYSQL_DB,
                port=MYSQL_PORT,
                connection_timeout=1
            )
            if conn.is_connected():
                return conn, True
        except Exception:
            _MYSQL_AVAILABLE = False

    # 2. SQLite Fallback connection (Instant, zero-latency)
    conn = sqlite3.connect(SQLITE_DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    _ensure_sqlite_tables(conn)
    return conn, False


def _ensure_sqlite_tables(conn):
    """Initializes SQLite database tables and seeds baseline data from CSV if empty."""
    cursor = conn.cursor()
    
    # Create agricultural_data table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agricultural_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            crop_type TEXT NOT NULL,
            soil TEXT DEFAULT 'Unknown',
            rainfall REAL DEFAULT NULL,
            temperature REAL DEFAULT NULL,
            fertilizer REAL DEFAULT NULL,
            irrigation TEXT DEFAULT 'Unknown',
            yield_value REAL NOT NULL,
            location TEXT DEFAULT 'Unknown',
            season TEXT DEFAULT 'Unknown',
            source_dataset TEXT DEFAULT 'Uploaded Dataset',
            import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Column Migration check for existing SQLite databases
    cursor.execute("PRAGMA table_info(agricultural_data)")
    cols = [column[1] for column in cursor.fetchall()]
    if "source_dataset" not in cols:
        cursor.execute("ALTER TABLE agricultural_data ADD COLUMN source_dataset TEXT DEFAULT 'Uploaded Dataset'")
    if "import_date" not in cols:
        cursor.execute("ALTER TABLE agricultural_data ADD COLUMN import_date TIMESTAMP DEFAULT NULL")

    # Create dataset_sources table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dataset_sources (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dataset_name TEXT NOT NULL,
            source_name TEXT NOT NULL,
            source_url TEXT,
            import_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            record_count INTEGER DEFAULT 0,
            available_fields TEXT,
            quality_score REAL DEFAULT 100.0,
            status TEXT DEFAULT 'Imported'
        )
    """)
    conn.commit()


def reset_database_to_baseline():
    """
    Cleans up all datasets and resets the database to empty on application start.
    Nothing is displayed until the user uploads their own dataset file.
    """
    conn, is_mysql = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM agricultural_data")
        cursor.execute("DELETE FROM dataset_sources")
        conn.commit()
    except Exception as e:
        print(f"Reset database notice: {e}")
    finally:
        if hasattr(conn, 'close'):
            conn.close()

    # Clean temporary files in data/raw
    raw_dir = os.path.join(BASE_DIR, "data", "raw")
    if os.path.exists(raw_dir):
        for f in os.listdir(raw_dir):
            if f.startswith("temp_"):
                fpath = os.path.join(raw_dir, f)
                try:
                    if os.path.isfile(fpath):
                        os.remove(fpath)
                except Exception:
                    pass

