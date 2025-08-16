#!/usr/bin/env python3
"""Test logging to database directly."""

import logging
import time
import sqlite3
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from utils.optimized_database_logger import configure_optimized_logging

print("Testing database logging...")

# Initialize database
database.init_db()

# Configure logging with smaller batch for immediate writes
logger = configure_optimized_logging(
    'test_direct',
    level=logging.DEBUG,
    batch_size=1,  # Write immediately
    flush_interval=0.1  # Flush quickly
)

print(f"Logger configured: {logger}")
print(f"Logger handlers: {logger.handlers}")

# Generate test logs
test_messages = [
    ('INFO', 'Test log 1 - Application started'),
    ('WARNING', 'Test log 2 - Warning message'),
    ('ERROR', 'Test log 3 - Error occurred'),
    ('DEBUG', 'Test log 4 - Debug information'),
]

for level, msg in test_messages:
    print(f"Logging {level}: {msg}")
    if level == 'INFO':
        logger.info(msg)
    elif level == 'WARNING':
        logger.warning(msg)
    elif level == 'ERROR':
        logger.error(msg)
    elif level == 'DEBUG':
        logger.debug(msg)
    time.sleep(0.1)

# Force flush
print("\nFlushing logs...")
for handler in logger.handlers:
    if hasattr(handler, 'flush'):
        handler.flush()
        print(f"Flushed handler: {handler}")

# Wait for batch worker
time.sleep(2)

# Check database
print("\nChecking database...")
conn = sqlite3.connect(database.DATABASE_FILE)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM application_logs")
count = cursor.fetchone()[0]
print(f"Total logs in database: {count}")

cursor.execute("""
    SELECT timestamp, log_level, message 
    FROM application_logs 
    ORDER BY timestamp DESC 
    LIMIT 10
""")
logs = cursor.fetchall()

print(f"\nFound {len(logs)} recent logs:")
for ts, level, msg in logs:
    print(f"  [{level}] {msg[:80]}")

conn.close()

print("\nDone!")