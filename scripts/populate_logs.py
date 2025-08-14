#!/usr/bin/env python3
"""Populate database with diverse logging records for testing the admin panel."""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import logging
import time
import random
from datetime import datetime, timedelta
from utils.optimized_database_logger import configure_optimized_logging

def generate_realistic_logs():
    """Generate realistic log entries for testing."""
    
    # Configure logger
    logger = configure_optimized_logging('javna_narocila_app', logging.DEBUG)
    
    print("Generating realistic log entries...")
    
    # Define realistic log scenarios
    scenarios = [
        # System startup logs
        ('INFO', 'Application starting up...'),
        ('INFO', 'Database connection established'),
        ('INFO', 'CPV codes loaded: 9454 codes'),
        ('INFO', 'Admin panel initialized'),
        ('DEBUG', 'Session state initialized'),
        
        # User activity logs
        ('INFO', 'User admin@demo.si logged in'),
        ('INFO', 'New procurement created: JN-2024-001'),
        ('INFO', 'Form data saved for step 3'),
        ('DEBUG', 'Validation passed for projectInfo section'),
        ('INFO', 'Document generated: razpisna_dokumentacija_2024_001.docx'),
        
        # Warning scenarios
        ('WARNING', 'High memory usage detected: 85% of available RAM'),
        ('WARNING', 'Slow query detected: get_procurements_for_customer took 2.3s'),
        ('WARNING', 'Session timeout approaching for user marko.novak@podjetje.si'),
        ('WARNING', 'CPV code 45000000 deprecated, consider using 45100000'),
        ('WARNING', 'Template file modified outside application'),
        
        # Error scenarios
        ('ERROR', 'Failed to connect to email server: smtp.gmail.com:587'),
        ('ERROR', 'Document generation failed: Template not found'),
        ('ERROR', 'Database lock timeout after 5 seconds'),
        ('ERROR', 'Invalid CPV code entered: 99999999'),
        ('ERROR', 'User authentication failed for jana.kranjc@org.si'),
        
        # Business logic logs
        ('INFO', 'Procurement JN-2024-002 published to portal'),
        ('INFO', 'Email notification sent to 5 subscribers'),
        ('INFO', 'Backup completed: 145 procurements exported'),
        ('INFO', 'Criteria validation completed: 3 price, 2 social criteria'),
        ('DEBUG', 'Cache hit for CPV search: "gradbena dela"'),
        
        # Data operations
        ('INFO', 'Imported 15 new CPV codes from update'),
        ('INFO', 'Organization "Občina Ljubljana" created'),
        ('INFO', 'User permissions updated for role: administrator'),
        ('DEBUG', 'Form autosave triggered for procurement_id: 42'),
        ('INFO', 'Export completed: procurement_report_2024.csv'),
        
        # System monitoring
        ('INFO', 'Daily cleanup: removed 0 expired logs'),
        ('DEBUG', 'Health check passed: all services operational'),
        ('WARNING', 'Disk space low: 15% remaining on /var/log'),
        ('INFO', 'Performance metrics: avg response time 145ms'),
        ('DEBUG', 'Background job completed: email_queue_processor'),
        
        # Validation and compliance
        ('INFO', 'ESPD validation successful for supplier "Gradnje d.o.o."'),
        ('WARNING', 'Missing required field: technicalCapacity.references'),
        ('ERROR', 'Deadline validation failed: submission date before publication'),
        ('INFO', 'Compliance check passed for EU directives'),
        ('DEBUG', 'Schema validation: all fields match JSON schema v2.1'),
        
        # Integration logs
        ('INFO', 'Successfully synced with e-Naročanje portal'),
        ('WARNING', 'API rate limit approaching: 950/1000 requests today'),
        ('ERROR', 'External service unavailable: TED Europa API'),
        ('INFO', 'Webhook delivered to https://partner.api/notifications'),
        ('DEBUG', 'OAuth token refreshed for portal integration'),
        
        # Audit logs
        ('INFO', 'Audit: User peter.kovac@ministrstvo.si viewed procurement JN-2024-003'),
        ('INFO', 'Audit: Document downloaded: tehnicne_specifikacije.pdf'),
        ('INFO', 'Audit: Procurement status changed from Draft to Published'),
        ('WARNING', 'Audit: Unusual activity detected - 50 exports in 1 minute'),
        ('INFO', 'Audit: Administrator changed system settings: criteria_weights'),
    ]
    
    # Generate logs with some time variation
    for i, (level, message) in enumerate(scenarios):
        # Add some variety to timestamps (spread over last few hours)
        time_offset = random.randint(0, 180)  # Up to 3 hours ago
        
        # Log the message
        if level == 'DEBUG':
            logger.debug(message)
        elif level == 'INFO':
            logger.info(message)
        elif level == 'WARNING':
            logger.warning(message)
        elif level == 'ERROR':
            logger.error(message)
        
        # Small delay to ensure different timestamps
        time.sleep(0.05)
        
        # Progress indicator
        if (i + 1) % 10 == 0:
            print(f"  Generated {i + 1}/{len(scenarios)} log entries...")
    
    # Flush all logs
    logger.handlers[0].flush()
    time.sleep(1)  # Wait for batch write to complete
    
    print(f"\n✅ Successfully generated {len(scenarios)} log entries!")
    print("\nLog level distribution:")
    print(f"  - DEBUG: {sum(1 for l, _ in scenarios if l == 'DEBUG')} entries")
    print(f"  - INFO: {sum(1 for l, _ in scenarios if l == 'INFO')} entries")
    print(f"  - WARNING: {sum(1 for l, _ in scenarios if l == 'WARNING')} entries")
    print(f"  - ERROR: {sum(1 for l, _ in scenarios if l == 'ERROR')} entries")
    print("\nYou can now view these logs in the Admin Panel → Dnevnik tab")

if __name__ == "__main__":
    generate_realistic_logs()