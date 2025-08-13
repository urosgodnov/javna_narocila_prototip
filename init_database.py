#!/usr/bin/env python3
"""Database initialization module for CPV seed data."""
import json
import os
import sys
from utils.cpv_manager import get_cpv_count, bulk_insert_cpv_codes
from utils.cpv_importer import import_cpv_from_excel
import streamlit as st


def initialize_cpv_data(force=False):
    """
    Initialize CPV data in the database from seed data.
    
    Args:
        force: Force re-initialization even if data exists
    
    Returns:
        Dict with initialization results
    """
    result = {
        'success': False,
        'imported': 0,
        'skipped': 0,
        'failed': 0,
        'source': None,
        'message': ''
    }
    
    try:
        # Check current CPV count
        current_count = get_cpv_count()
        
        # Check if we need to initialize
        if current_count > 0 and not force:
            result['success'] = True
            result['skipped'] = current_count
            result['message'] = f"CPV data already initialized ({current_count} codes exist)"
            return result
        
        # Try primary source: Excel file
        excel_path = 'miscellanious/cpv.xlsx'
        if os.path.exists(excel_path):
            print(f"Initializing CPV data from {excel_path}...")
            import_result = import_cpv_from_excel(excel_path)
            if import_result['success']:
                result.update(import_result)
                result['source'] = 'Excel'
                result['message'] = f"Initialized {import_result['imported']} CPV codes from Excel"
                return result
        
        # Fallback to JSON seed data
        json_path = 'json_files/cpv_seed_data.json'
        if os.path.exists(json_path):
            print(f"Initializing CPV data from {json_path}...")
            with open(json_path, 'r', encoding='utf-8') as f:
                cpv_data = json.load(f)
            
            # Convert to tuple format for bulk_insert_cpv_codes
            cpv_tuples = [(item['code'], item['description']) for item in cpv_data]
            
            import_result = bulk_insert_cpv_codes(cpv_tuples)
            result.update(import_result)
            result['source'] = 'JSON'
            result['success'] = True
            result['message'] = f"Initialized {import_result['imported']} CPV codes from JSON"
            return result
        
        # No seed data available
        result['message'] = "No CPV seed data found (Excel or JSON)"
        return result
        
    except Exception as e:
        result['message'] = f"Initialization error: {str(e)}"
        return result


def ensure_cpv_data_initialized():
    """
    Ensure CPV data is initialized when admin accesses relevant tabs.
    This should be called before rendering tabs that need CPV data.
    """
    # Use session state to track initialization
    if 'cpv_initialized' not in st.session_state:
        st.session_state.cpv_initialized = False
    
    if not st.session_state.cpv_initialized:
        result = initialize_cpv_data()
        if result['success']:
            st.session_state.cpv_initialized = True
            if result['imported'] > 0:
                st.success(f"✅ CPV podatki inicializirani: {result['imported']} kod uvoženih iz {result['source']}")
        elif result['skipped'] > 0:
            st.session_state.cpv_initialized = True
        else:
            st.error(f"⚠️ {result['message']}")
    
    return st.session_state.cpv_initialized


def check_cpv_data_status():
    """
    Check the status of CPV data in the database.
    
    Returns:
        Dict with status information
    """
    try:
        count = get_cpv_count()
        excel_exists = os.path.exists('miscellanious/cpv.xlsx')
        json_exists = os.path.exists('json_files/cpv_seed_data.json')
        
        return {
            'database_count': count,
            'excel_available': excel_exists,
            'json_available': json_exists,
            'initialized': count > 0
        }
    except Exception as e:
        return {
            'database_count': 0,
            'excel_available': False,
            'json_available': False,
            'initialized': False,
            'error': str(e)
        }


if __name__ == "__main__":
    # Run initialization when script is executed directly
    print("=" * 50)
    print("CPV Database Initialization")
    print("=" * 50)
    
    # Check status
    status = check_cpv_data_status()
    print(f"Current database count: {status['database_count']}")
    print(f"Excel file available: {status['excel_available']}")
    print(f"JSON file available: {status['json_available']}")
    
    if status['database_count'] > 0:
        response = input("\nDatabase already has data. Force re-initialization? (y/N): ")
        force = response.lower() == 'y'
    else:
        force = False
    
    # Initialize
    result = initialize_cpv_data(force=force)
    
    print("\n" + "=" * 50)
    if result['success']:
        print(f"✅ Success! {result['message']}")
        print(f"   Imported: {result['imported']}")
        print(f"   Skipped: {result['skipped']}")
        if result['failed'] > 0:
            print(f"   Failed: {result['failed']}")
    else:
        print(f"❌ Failed! {result['message']}")
    print("=" * 50)