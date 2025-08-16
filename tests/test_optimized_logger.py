#!/usr/bin/env python3
"""Test script for optimized DatabaseLogHandler."""

import logging
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import database
from utils.optimized_database_logger import configure_optimized_logging
from utils.database_logger import configure_database_logging


def benchmark_logging(logger, test_name, count=1000):
    """Benchmark logging performance."""
    start = time.time()
    
    for i in range(count):
        logger.info(f"Performance test {i}")
    
    # For optimized logger, ensure flush
    if hasattr(logger.handlers[0], 'flush'):
        logger.handlers[0].flush()
    
    elapsed = time.time() - start
    per_log = (elapsed / count) * 1000  # ms
    
    print(f"{test_name}:")
    print(f"  Total time: {elapsed:.2f}s")
    print(f"  Per log: {per_log:.2f}ms")
    print(f"  Logs/sec: {count/elapsed:.0f}")
    
    return per_log


def test_performance_comparison():
    """Compare original vs optimized logger performance."""
    print("\n" + "="*60)
    print("PERFORMANCE OPTIMIZATION TEST")
    print("="*60)
    
    # Initialize database
    database.init_db()
    
    # Test original logger
    print("\n[1] Testing Original DatabaseLogHandler...")
    original_logger = configure_database_logging('test_original', logging.INFO)
    original_time = benchmark_logging(original_logger, "Original", count=100)
    
    # Test optimized logger with different configurations
    print("\n[2] Testing Optimized DatabaseLogHandler...")
    
    # Default configuration
    optimized_logger = configure_optimized_logging('test_optimized', logging.INFO)
    optimized_time = benchmark_logging(optimized_logger, "Optimized (default)", count=100)
    
    # Aggressive batching
    aggressive_logger = configure_optimized_logging(
        'test_aggressive', 
        logging.INFO,
        batch_size=100,
        flush_interval=1.0
    )
    aggressive_time = benchmark_logging(aggressive_logger, "Optimized (aggressive)", count=100)
    
    # Calculate improvements
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)
    
    improvement = ((original_time - optimized_time) / original_time) * 100
    aggressive_improvement = ((original_time - aggressive_time) / original_time) * 100
    
    print(f"\nOriginal: {original_time:.2f}ms per log")
    print(f"Optimized (default): {optimized_time:.2f}ms per log ({improvement:.1f}% improvement)")
    print(f"Optimized (aggressive): {aggressive_time:.2f}ms per log ({aggressive_improvement:.1f}% improvement)")
    
    # Check if we meet the target
    target = 10  # ms
    if optimized_time < target:
        print(f"\n✅ SUCCESS: Optimized logger meets <{target}ms target!")
    else:
        print(f"\n⚠️  Optimized logger at {optimized_time:.2f}ms (target: <{target}ms)")
    
    # Test batch writing
    print("\n[3] Testing Batch Writing...")
    test_batch_integrity()
    
    return optimized_time < target


def test_batch_integrity():
    """Test that batch writing doesn't lose logs."""
    import sqlite3
    
    # Clear existing test logs with batch test message
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        conn.execute("DELETE FROM application_logs WHERE message LIKE 'Batch test%'")
        conn.commit()
    
    # Create logger with aggressive batching
    logger = configure_optimized_logging(
        'batch_test',
        logging.INFO,
        batch_size=50,
        flush_interval=0.5
    )
    
    # Write exactly 100 logs
    expected_count = 100
    for i in range(expected_count):
        logger.info(f"Batch test {i}")
    
    # Ensure flush
    logger.handlers[0].flush()
    time.sleep(1.0)  # Wait for async writes to complete
    
    # Check all logs were written (by message content since module is from file)
    with sqlite3.connect(database.DATABASE_FILE) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT COUNT(*) FROM application_logs 
            WHERE message LIKE '%Batch test%'
        """)
        actual_count = cursor.fetchone()[0]
    
    if actual_count == expected_count:
        print(f"  ✓ Batch integrity test passed: {actual_count}/{expected_count} logs")
    else:
        print(f"  ✗ Batch integrity test failed: {actual_count}/{expected_count} logs")
    
    return actual_count == expected_count


def test_concurrent_logging():
    """Test concurrent logging performance."""
    import threading
    
    print("\n[4] Testing Concurrent Logging...")
    
    logger = configure_optimized_logging(
        'concurrent_test',
        logging.INFO,
        batch_size=100,
        flush_interval=0.2
    )
    
    def worker(worker_id, count=100):
        """Worker thread that logs messages."""
        for i in range(count):
            logger.info(f"Worker {worker_id} message {i}")
    
    # Start multiple threads
    threads = []
    thread_count = 5
    logs_per_thread = 100
    
    start = time.time()
    
    for i in range(thread_count):
        t = threading.Thread(target=worker, args=(i, logs_per_thread))
        threads.append(t)
        t.start()
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Flush
    logger.handlers[0].flush()
    
    elapsed = time.time() - start
    total_logs = thread_count * logs_per_thread
    per_log = (elapsed / total_logs) * 1000
    
    print(f"  Concurrent test ({thread_count} threads, {total_logs} logs):")
    print(f"    Total time: {elapsed:.2f}s")
    print(f"    Per log: {per_log:.2f}ms")
    print(f"    Throughput: {total_logs/elapsed:.0f} logs/sec")
    
    return per_log


if __name__ == "__main__":
    success = test_performance_comparison()
    concurrent_time = test_concurrent_logging()
    
    print("\n" + "="*60)
    if success:
        print("✅ OPTIMIZATION SUCCESSFUL - Target performance achieved!")
    else:
        print("⚠️  Further optimization needed")
    print("="*60)