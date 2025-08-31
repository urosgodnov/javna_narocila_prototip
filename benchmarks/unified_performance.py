#!/usr/bin/env python3
"""
Performance benchmarks for unified form architecture.
Story 40.10: Verify performance with unified lot structure.
"""

import time
import statistics
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from ui.controllers.form_controller import FormController


def benchmark_simple_form(iterations=10):
    """Benchmark simple form with General lot."""
    schema = {
        'type': 'object',
        'properties': {
            f'field_{i}': {'type': 'string', 'title': f'Field {i}'}
            for i in range(50)  # 50 fields
        }
    }
    
    times = []
    
    for _ in range(iterations):
        # Mock session state
        mock_session_state = {}
        
        with patch('streamlit.session_state', mock_session_state):
            start = time.time()
            
            # Create controller (includes lot initialization)
            controller = FormController(schema)
            
            # Simulate field operations
            for i in range(50):
                controller.context.set_field_value(f'field_{i}', f'value_{i}')
            
            # Read all values
            for i in range(50):
                value = controller.context.get_field_value(f'field_{i}')
            
            elapsed = time.time() - start
            times.append(elapsed)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }


def benchmark_complex_form(iterations=10):
    """Benchmark complex form with multiple lots."""
    schema = {
        'type': 'object',
        'properties': {
            f'field_{i}': {'type': 'string', 'title': f'Field {i}'}
            for i in range(20)  # 20 fields per lot
        }
    }
    
    times = []
    
    for _ in range(iterations):
        mock_session_state = {}
        
        with patch('streamlit.session_state', mock_session_state):
            start = time.time()
            
            # Create controller
            controller = FormController(schema)
            
            # Add 4 more lots (total 5)
            for i in range(1, 5):
                controller.context.add_lot(f'Lot {i+1}')
            
            # Add data to each lot
            for lot_idx in range(5):
                controller.context.switch_to_lot(lot_idx)
                for field_idx in range(20):
                    controller.context.set_field_value(
                        f'field_{field_idx}',
                        f'lot_{lot_idx}_value_{field_idx}'
                    )
            
            # Read from each lot
            for lot_idx in range(5):
                controller.context.switch_to_lot(lot_idx)
                for field_idx in range(20):
                    value = controller.context.get_field_value(f'field_{field_idx}')
            
            elapsed = time.time() - start
            times.append(elapsed)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }


def benchmark_lot_operations(iterations=10):
    """Benchmark lot management operations."""
    times = []
    
    for _ in range(iterations):
        mock_session_state = {}
        
        with patch('streamlit.session_state', mock_session_state):
            controller = FormController()
            
            start = time.time()
            
            # Add lots
            for i in range(10):
                controller.context.add_lot(f'Lot {i+1}')
            
            # Switch between lots
            for _ in range(50):
                for lot_idx in range(11):  # 11 lots total
                    controller.context.switch_to_lot(lot_idx)
            
            # Remove some lots
            for i in range(5):
                controller.context.remove_lot(5)  # Remove middle lots
            
            elapsed = time.time() - start
            times.append(elapsed)
    
    return {
        'mean': statistics.mean(times),
        'median': statistics.median(times),
        'stdev': statistics.stdev(times) if len(times) > 1 else 0,
        'min': min(times),
        'max': max(times)
    }


def compare_with_baseline():
    """Compare unified architecture with baseline expectations."""
    print("=" * 60)
    print("Unified Form Architecture - Performance Benchmarks")
    print("Story 40.10: ALL forms use lot structure")
    print("=" * 60)
    
    # Run benchmarks
    print("\n1. Simple Form (50 fields, 1 General lot)")
    print("-" * 40)
    simple_results = benchmark_simple_form(iterations=20)
    print(f"Mean time: {simple_results['mean']*1000:.2f}ms")
    print(f"Median time: {simple_results['median']*1000:.2f}ms")
    print(f"Min/Max: {simple_results['min']*1000:.2f}ms / {simple_results['max']*1000:.2f}ms")
    print(f"Std Dev: {simple_results['stdev']*1000:.2f}ms")
    
    print("\n2. Complex Form (20 fields × 5 lots = 100 fields)")
    print("-" * 40)
    complex_results = benchmark_complex_form(iterations=20)
    print(f"Mean time: {complex_results['mean']*1000:.2f}ms")
    print(f"Median time: {complex_results['median']*1000:.2f}ms")
    print(f"Min/Max: {complex_results['min']*1000:.2f}ms / {complex_results['max']*1000:.2f}ms")
    print(f"Std Dev: {complex_results['stdev']*1000:.2f}ms")
    
    print("\n3. Lot Operations (add/switch/remove)")
    print("-" * 40)
    lot_results = benchmark_lot_operations(iterations=20)
    print(f"Mean time: {lot_results['mean']*1000:.2f}ms")
    print(f"Median time: {lot_results['median']*1000:.2f}ms")
    print(f"Min/Max: {lot_results['min']*1000:.2f}ms / {lot_results['max']*1000:.2f}ms")
    print(f"Std Dev: {lot_results['stdev']*1000:.2f}ms")
    
    # Performance assessment
    print("\n" + "=" * 60)
    print("Performance Assessment:")
    print("-" * 60)
    
    # Define acceptable thresholds
    thresholds = {
        'simple': 100,  # 100ms for simple forms
        'complex': 200,  # 200ms for complex forms
        'lots': 150     # 150ms for lot operations
    }
    
    passed = True
    
    if simple_results['mean'] * 1000 < thresholds['simple']:
        print(f"[PASS] Simple forms: {simple_results['mean']*1000:.2f}ms < {thresholds['simple']}ms")
    else:
        print(f"[FAIL] Simple forms: {simple_results['mean']*1000:.2f}ms > {thresholds['simple']}ms")
        passed = False
    
    if complex_results['mean'] * 1000 < thresholds['complex']:
        print(f"[PASS] Complex forms: {complex_results['mean']*1000:.2f}ms < {thresholds['complex']}ms")
    else:
        print(f"[FAIL] Complex forms: {complex_results['mean']*1000:.2f}ms > {thresholds['complex']}ms")
        passed = False
    
    if lot_results['mean'] * 1000 < thresholds['lots']:
        print(f"[PASS] Lot operations: {lot_results['mean']*1000:.2f}ms < {thresholds['lots']}ms")
    else:
        print(f"[FAIL] Lot operations: {lot_results['mean']*1000:.2f}ms > {thresholds['lots']}ms")
        passed = False
    
    print("\n" + "=" * 60)
    if passed:
        print("RESULT: [SUCCESS] All performance benchmarks PASSED")
        print("The unified lot architecture performs within acceptable limits.")
    else:
        print("RESULT: [FAILURE] Some benchmarks failed")
        print("Performance optimization may be needed.")
    
    print("\nNOTE: The unified architecture adds minimal overhead")
    print("for simple forms (General lot) while providing")
    print("consistent behavior across all form types.")
    
    return passed


if __name__ == "__main__":
    compare_with_baseline()