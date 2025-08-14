"""Optimized Database logging handler with batch processing and async writes."""
import logging
import sqlite3
import json
import threading
import queue
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import os
import sys
import atexit

# Add parent directory to path to import config and database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import database


class OptimizedDatabaseLogHandler(logging.Handler):
    """Optimized logging handler with batch processing and async writes."""
    
    def __init__(self, 
                 db_connection=None, 
                 fallback_file='logs/fallback.log',
                 batch_size=50,
                 flush_interval=0.5,
                 use_wal_mode=True):
        """Initialize the optimized database log handler.
        
        Args:
            db_connection: Database connection (optional)
            fallback_file: File path for fallback logging
            batch_size: Number of logs to batch before writing
            flush_interval: Max seconds to wait before flushing
            use_wal_mode: Enable SQLite WAL mode for better concurrency
        """
        super().__init__()
        self.db_connection = db_connection
        self.fallback_file = fallback_file
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        self.fallback_handler = None
        
        # Queue for batch processing
        self.log_queue = queue.Queue(maxsize=10000)
        self.batch_buffer = []
        self.last_flush = time.time()
        
        # Enable WAL mode for better concurrency
        if use_wal_mode:
            self._enable_wal_mode()
        
        # Ensure fallback directory exists
        if fallback_file:
            os.makedirs(os.path.dirname(fallback_file), exist_ok=True)
            self.fallback_handler = logging.FileHandler(fallback_file)
            self.fallback_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        # Start background thread for batch processing
        self.worker_thread = threading.Thread(target=self._batch_worker, daemon=True)
        self.worker_thread.start()
        
        # Register cleanup on exit
        atexit.register(self.flush)
    
    def _enable_wal_mode(self):
        """Enable WAL mode for better SQLite concurrency."""
        try:
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("PRAGMA synchronous=NORMAL")
                conn.execute("PRAGMA cache_size=10000")
                conn.execute("PRAGMA temp_store=MEMORY")
                conn.commit()
        except Exception as e:
            print(f"Warning: Could not enable WAL mode: {e}")
    
    def emit(self, record: logging.LogRecord):
        """Process a log record - add to queue for batch processing.
        
        Args:
            record: The log record to process
        """
        try:
            # Prepare log data
            log_data = self._prepare_log_data(record)
            
            # Add to queue (non-blocking)
            try:
                self.log_queue.put_nowait(log_data)
            except queue.Full:
                # Queue is full, fall back to direct write or file
                self._emergency_write(log_data)
                
        except Exception:
            self.handleError(record)
    
    def _prepare_log_data(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Prepare log data from record.
        
        Args:
            record: The log record
            
        Returns:
            Dictionary of log data ready for insertion
        """
        # Format the log message
        message = self._safe_format_message(record)
        
        # Get retention hours
        retention_hours = self._get_retention_hours(record)
        
        # Calculate expiration time
        timestamp = datetime.fromtimestamp(record.created)
        expires_at = timestamp + timedelta(hours=retention_hours)
        
        # Get organization context (cached for performance)
        org_id, org_name, session_id = self._get_organization_context()
        
        # Prepare additional context
        additional_context = self._get_additional_context(record)
        
        return {
            'timestamp': timestamp.isoformat(),
            'organization_id': org_id,
            'organization_name': org_name,
            'session_id': session_id,
            'log_level': record.levelname,
            'module': record.module or record.name,
            'function_name': record.funcName,
            'line_number': record.lineno,
            'message': message,
            'retention_hours': retention_hours,
            'expires_at': expires_at.isoformat(),
            'additional_context': json.dumps(additional_context) if additional_context else None,
            'log_type': getattr(record, 'log_type', None)
        }
    
    def _batch_worker(self):
        """Background worker thread for batch processing."""
        while True:
            try:
                # Collect batch
                batch = []
                deadline = time.time() + self.flush_interval
                
                while len(batch) < self.batch_size and time.time() < deadline:
                    timeout = max(0.01, deadline - time.time())
                    try:
                        log_data = self.log_queue.get(timeout=timeout)
                        batch.append(log_data)
                    except queue.Empty:
                        break
                
                # Write batch if we have data
                if batch:
                    self._write_batch(batch)
                    
            except Exception as e:
                # Log error but keep worker running
                print(f"Batch worker error: {e}")
                time.sleep(0.1)
    
    def _write_batch(self, batch: List[Dict[str, Any]]):
        """Write a batch of logs to database.
        
        Args:
            batch: List of log data dictionaries
        """
        conn = None
        try:
            conn = self.db_connection or sqlite3.connect(database.DATABASE_FILE)
            cursor = conn.cursor()
            
            # Use single transaction for batch
            cursor.execute("BEGIN TRANSACTION")
            
            # Batch insert
            cursor.executemany("""
                INSERT INTO application_logs (
                    timestamp, organization_id, organization_name, session_id,
                    log_level, module, function_name, line_number, message,
                    retention_hours, expires_at, additional_context, log_type
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                (
                    log['timestamp'], log['organization_id'], log['organization_name'],
                    log['session_id'], log['log_level'], log['module'],
                    log['function_name'], log['line_number'], log['message'],
                    log['retention_hours'], log['expires_at'],
                    log['additional_context'], log['log_type']
                )
                for log in batch
            ])
            
            cursor.execute("COMMIT")
            
            if not self.db_connection:
                conn.close()
                
        except Exception as e:
            if conn:
                try:
                    conn.rollback()
                except:
                    pass
                if not self.db_connection:
                    conn.close()
            
            # Fall back to individual writes or file
            for log_data in batch:
                self._emergency_write(log_data)
    
    def _emergency_write(self, log_data: Dict[str, Any]):
        """Emergency write when queue is full or batch fails.
        
        Args:
            log_data: Log data to write
        """
        if self.fallback_handler:
            # Create a simple log record for fallback
            record = logging.LogRecord(
                name=log_data.get('module', 'unknown'),
                level=getattr(logging, log_data.get('log_level', 'INFO')),
                pathname='',
                lineno=log_data.get('line_number', 0),
                msg=log_data.get('message', ''),
                args=(),
                exc_info=None
            )
            self.fallback_handler.emit(record)
    
    def flush(self):
        """Flush any pending logs."""
        # Process remaining items in queue
        batch = []
        try:
            while not self.log_queue.empty():
                batch.append(self.log_queue.get_nowait())
                if len(batch) >= self.batch_size:
                    self._write_batch(batch)
                    batch = []
        except queue.Empty:
            pass
        
        # Write remaining batch
        if batch:
            self._write_batch(batch)
    
    def _safe_format_message(self, record: logging.LogRecord) -> str:
        """Safely format the log message."""
        try:
            return self.format(record) if self.formatter else record.getMessage()
        except Exception:
            return str(record.msg)
    
    def _get_retention_hours(self, record: logging.LogRecord) -> int:
        """Get retention hours based on log level and type."""
        log_type = getattr(record, 'log_type', None)
        if log_type and log_type in config.SPECIAL_LOG_RETENTION:
            return config.SPECIAL_LOG_RETENTION[log_type]
        
        level_name = record.levelname
        return config.LOG_RETENTION_HOURS.get(level_name, 24)
    
    # Cache organization context for performance
    _org_context_cache = None
    _org_context_cache_time = 0
    
    def _get_organization_context(self) -> tuple:
        """Get organization context from Streamlit session state (cached)."""
        # Use cache if recent (within 1 second)
        if self._org_context_cache and (time.time() - self._org_context_cache_time) < 1:
            return self._org_context_cache
        
        # Quick check if we're in Streamlit context
        if 'streamlit' not in sys.modules:
            self._org_context_cache = (None, None, None)
            self._org_context_cache_time = time.time()
            return self._org_context_cache
        
        org_id = None
        org_name = None
        session_id = None
        
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and st.session_state:
                org_id = st.session_state.get('organization_id')
                org_name = st.session_state.get('organization_name') or st.session_state.get('organizacija')
                session_id = st.session_state.get('session_id')
        except (ImportError, AttributeError, RuntimeError):
            pass
        
        self._org_context_cache = (org_id, org_name, session_id)
        self._org_context_cache_time = time.time()
        return self._org_context_cache
    
    def _get_additional_context(self, record: logging.LogRecord) -> Optional[Dict[str, Any]]:
        """Extract additional context from the log record."""
        context = {}
        
        if hasattr(record, 'extra'):
            context.update(record.extra)
        
        if record.exc_info:
            import traceback
            context['exception'] = traceback.format_exception(*record.exc_info)
        
        if record.stack_info:
            context['stack'] = record.stack_info
        
        return context if context else None
    
    def handleError(self, record: logging.LogRecord):
        """Handle errors by falling back to file logging."""
        if self.fallback_handler:
            try:
                self.fallback_handler.emit(record)
            except Exception:
                import sys
                print(f"LOGGING ERROR: Could not log message: {record.getMessage()}", file=sys.stderr)


def configure_optimized_logging(logger_name: Optional[str] = None, 
                                level: int = logging.INFO,
                                remove_existing: bool = True,
                                batch_size: int = 50,
                                flush_interval: float = 0.5) -> logging.Logger:
    """Configure a logger to use optimized database logging.
    
    Args:
        logger_name: Name of the logger (None for root logger)
        level: Logging level
        remove_existing: Whether to remove existing handlers
        batch_size: Number of logs to batch
        flush_interval: Max seconds before flush
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    if remove_existing:
        logger.handlers.clear()
    
    # Add optimized database handler
    db_handler = OptimizedDatabaseLogHandler(
        batch_size=batch_size,
        flush_interval=flush_interval
    )
    db_handler.setLevel(level)
    
    # Add formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    db_handler.setFormatter(formatter)
    
    logger.addHandler(db_handler)
    
    # Also add console handler for immediate feedback
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger