#!/usr/bin/env python3
"""
Unit tests for BankManager class.
Tests all CRUD operations and edge cases.
"""

import unittest
import sqlite3
import tempfile
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import BankManager


class TestBankManager(unittest.TestCase):
    """Test suite for BankManager class."""
    
    def setUp(self):
        """Set up test database before each test."""
        # Create temporary database
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db_path = self.test_db.name
        self.test_db.close()
        
        # Initialize connection and BankManager
        self.conn = sqlite3.connect(self.test_db_path)
        self.bank_manager = BankManager(self.conn)
        
        # Create bank table
        self.bank_manager.create_bank_table()
        
    def tearDown(self):
        """Clean up test database after each test."""
        self.conn.close()
        os.unlink(self.test_db_path)
    
    def test_create_bank_table(self):
        """Test that bank table is created correctly."""
        cursor = self.conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='bank'")
        result = cursor.fetchone()
        self.assertIsNotNone(result, "Bank table should exist")
        
        # Check table structure
        cursor.execute("PRAGMA table_info(bank)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        expected_columns = [
            'id', 'bank_code', 'name', 'short_name', 'swift',
            'active', 'country', 'created_at', 'updated_at'
        ]
        
        for expected in expected_columns:
            self.assertIn(expected, column_names, f"Column {expected} should exist")
    
    def test_insert_bank(self):
        """Test inserting a new bank."""
        bank_data = {
            'code': '99',
            'name': 'Test Bank',
            'short_name': 'TB',
            'swift': 'TESTSI2X',
            'active': 1,
            'country': 'SI'
        }
        
        bank_id = self.bank_manager.insert_bank(bank_data)
        self.assertIsNotNone(bank_id, "Insert should return bank ID")
        self.assertGreater(bank_id, 0, "Bank ID should be positive")
        
        # Verify bank was inserted
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertIsNotNone(bank, "Bank should be retrievable")
        self.assertEqual(bank['name'], 'Test Bank')
        self.assertEqual(bank['swift'], 'TESTSI2X')
    
    def test_insert_duplicate_bank_code(self):
        """Test that duplicate bank codes are rejected."""
        bank_data = {
            'code': '99',
            'name': 'Test Bank 1',
            'active': 1
        }
        
        # First insert should succeed
        bank_id1 = self.bank_manager.insert_bank(bank_data)
        self.assertIsNotNone(bank_id1)
        
        # Second insert with same code should fail
        bank_data['name'] = 'Test Bank 2'
        bank_id2 = self.bank_manager.insert_bank(bank_data)
        self.assertIsNone(bank_id2, "Duplicate bank code should be rejected")
    
    def test_update_bank(self):
        """Test updating an existing bank."""
        # Insert a bank first
        bank_data = {
            'code': '99',
            'name': 'Original Name',
            'swift': 'ORIGSI2X'
        }
        bank_id = self.bank_manager.insert_bank(bank_data)
        
        # Update the bank
        update_data = {
            'name': 'Updated Name',
            'swift': 'UPDTSI2X',
            'short_name': 'UN'
        }
        success = self.bank_manager.update_bank(bank_id, update_data)
        self.assertTrue(success, "Update should succeed")
        
        # Verify updates
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertEqual(bank['name'], 'Updated Name')
        self.assertEqual(bank['swift'], 'UPDTSI2X')
        self.assertEqual(bank['short_name'], 'UN')
    
    def test_get_bank_by_code(self):
        """Test retrieving bank by code."""
        bank_data = {
            'code': '99',
            'name': 'Test Bank',
            'swift': 'TESTSI2X'
        }
        self.bank_manager.insert_bank(bank_data)
        
        # Retrieve existing bank
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertIsNotNone(bank)
        self.assertEqual(bank['bank_code'], '99')
        self.assertEqual(bank['name'], 'Test Bank')
        
        # Try non-existent code
        bank = self.bank_manager.get_bank_by_code('00')
        self.assertIsNone(bank, "Non-existent bank should return None")
    
    def test_get_bank_by_swift(self):
        """Test retrieving bank by SWIFT code."""
        bank_data = {
            'code': '99',
            'name': 'Test Bank',
            'swift': 'TESTSI2X'
        }
        self.bank_manager.insert_bank(bank_data)
        
        # Retrieve by SWIFT
        bank = self.bank_manager.get_bank_by_swift('TESTSI2X')
        self.assertIsNotNone(bank)
        self.assertEqual(bank['bank_code'], '99')
        
        # Try non-existent SWIFT
        bank = self.bank_manager.get_bank_by_swift('NONESI2X')
        self.assertIsNone(bank, "Non-existent SWIFT should return None")
    
    def test_get_all_banks(self):
        """Test retrieving all banks."""
        # Insert multiple banks
        banks_data = [
            {'code': '01', 'name': 'Bank 1', 'active': 1},
            {'code': '02', 'name': 'Bank 2', 'active': 1},
            {'code': '03', 'name': 'Bank 3', 'active': 0}
        ]
        
        for bank in banks_data:
            self.bank_manager.insert_bank(bank)
        
        # Get all banks
        all_banks = self.bank_manager.get_all_banks()
        self.assertEqual(len(all_banks), 3, "Should return all 3 banks")
        
        # Get only active banks
        active_banks = self.bank_manager.get_all_banks(active_only=True)
        self.assertEqual(len(active_banks), 2, "Should return only 2 active banks")
        
        # Verify active banks
        for bank in active_banks:
            self.assertEqual(bank['active'], 1, "All returned banks should be active")
    
    def test_deactivate_bank(self):
        """Test deactivating a bank."""
        bank_data = {'code': '99', 'name': 'Test Bank', 'active': 1}
        bank_id = self.bank_manager.insert_bank(bank_data)
        
        # Deactivate the bank
        success = self.bank_manager.deactivate_bank(bank_id)
        self.assertTrue(success, "Deactivation should succeed")
        
        # Verify bank is deactivated
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertEqual(bank['active'], 0, "Bank should be inactive")
    
    def test_activate_bank(self):
        """Test activating a bank."""
        bank_data = {'code': '99', 'name': 'Test Bank', 'active': 0}
        bank_id = self.bank_manager.insert_bank(bank_data)
        
        # Activate the bank
        success = self.bank_manager.activate_bank(bank_id)
        self.assertTrue(success, "Activation should succeed")
        
        # Verify bank is activated
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertEqual(bank['active'], 1, "Bank should be active")
    
    def test_toggle_bank_status(self):
        """Test toggling bank active status."""
        bank_data = {'code': '99', 'name': 'Test Bank', 'active': 1}
        bank_id = self.bank_manager.insert_bank(bank_data)
        
        # Toggle to inactive
        success = self.bank_manager.toggle_bank_status(bank_id)
        self.assertTrue(success)
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertEqual(bank['active'], 0, "Bank should be inactive after toggle")
        
        # Toggle back to active
        success = self.bank_manager.toggle_bank_status(bank_id)
        self.assertTrue(success)
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertEqual(bank['active'], 1, "Bank should be active after second toggle")
    
    def test_bank_with_null_swift(self):
        """Test handling banks without SWIFT codes."""
        bank_data = {
            'code': '99',
            'name': 'Bank Without SWIFT',
            'swift': None,
            'active': 1
        }
        
        bank_id = self.bank_manager.insert_bank(bank_data)
        self.assertIsNotNone(bank_id, "Should be able to insert bank without SWIFT")
        
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertIsNone(bank['swift'], "SWIFT should be None")
    
    def test_bank_with_minimal_data(self):
        """Test inserting bank with only required fields."""
        bank_data = {
            'code': '99',
            'name': 'Minimal Bank'
        }
        
        bank_id = self.bank_manager.insert_bank(bank_data)
        self.assertIsNotNone(bank_id, "Should insert with minimal data")
        
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertEqual(bank['active'], 1, "Should default to active")
        self.assertEqual(bank['country'], 'SI', "Should default to SI")
        self.assertIsNone(bank['short_name'], "Short name should be None")
        self.assertIsNone(bank['swift'], "SWIFT should be None")


class TestBankManagerIntegration(unittest.TestCase):
    """Integration tests for BankManager with real-world scenarios."""
    
    def setUp(self):
        """Set up test database before each test."""
        self.test_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.test_db_path = self.test_db.name
        self.test_db.close()
        
        self.conn = sqlite3.connect(self.test_db_path)
        self.bank_manager = BankManager(self.conn)
        self.bank_manager.create_bank_table()
    
    def tearDown(self):
        """Clean up test database after each test."""
        self.conn.close()
        os.unlink(self.test_db_path)
    
    def test_slovenian_banks_scenario(self):
        """Test adding and managing Slovenian banks."""
        slovenian_banks = [
            {'code': '02', 'name': 'Nova Ljubljanska banka', 'swift': 'LJBASI2X'},
            {'code': '03', 'name': 'SKB banka', 'swift': 'SKBASI2X'},
            {'code': '04', 'name': 'Nova KBM', 'swift': 'KBMASI2X'}
        ]
        
        # Add all banks
        for bank_data in slovenian_banks:
            bank_id = self.bank_manager.insert_bank(bank_data)
            self.assertIsNotNone(bank_id, f"Should insert {bank_data['name']}")
        
        # Verify all banks exist
        all_banks = self.bank_manager.get_all_banks()
        self.assertEqual(len(all_banks), 3)
        
        # Test SWIFT lookup
        nlb = self.bank_manager.get_bank_by_swift('LJBASI2X')
        self.assertIsNotNone(nlb)
        self.assertEqual(nlb['name'], 'Nova Ljubljanska banka')
        
        # Deactivate one bank
        skb = self.bank_manager.get_bank_by_code('03')
        self.bank_manager.deactivate_bank(skb['id'])
        
        # Check active banks count
        active_banks = self.bank_manager.get_all_banks(active_only=True)
        self.assertEqual(len(active_banks), 2, "Should have 2 active banks")
    
    def test_update_bank_preserves_unchanged_fields(self):
        """Test that updating specific fields doesn't affect others."""
        bank_data = {
            'code': '99',
            'name': 'Original Name',
            'short_name': 'ON',
            'swift': 'ORIGSI2X',
            'active': 1,
            'country': 'SI'
        }
        
        bank_id = self.bank_manager.insert_bank(bank_data)
        
        # Update only name
        self.bank_manager.update_bank(bank_id, {'name': 'New Name'})
        
        # Check all other fields remain unchanged
        bank = self.bank_manager.get_bank_by_code('99')
        self.assertEqual(bank['name'], 'New Name', "Name should be updated")
        self.assertEqual(bank['short_name'], 'ON', "Short name should be unchanged")
        self.assertEqual(bank['swift'], 'ORIGSI2X', "SWIFT should be unchanged")
        self.assertEqual(bank['active'], 1, "Active status should be unchanged")
        self.assertEqual(bank['country'], 'SI', "Country should be unchanged")


if __name__ == '__main__':
    unittest.main(verbosity=2)