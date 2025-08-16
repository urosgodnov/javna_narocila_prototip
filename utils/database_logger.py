"""Database logging handler for Python logging framework."""
import logging
import sqlite3
import json
import traceback
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import sys

# Add parent directory to path to import config and database
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
import database


class DatabaseLogHandler(logging.Handler):
    """Custom logging handler that stores logs in the database."""
    
    def __init__(self, db_connection=None, fallback_file='logs/fallback.log'):
        """Initialize the database log handler.
        
        Args:
            db_connection: Database connection (optional, will use default if None)
            fallback_file: File path for fallback logging if database fails
        """
        super().__init__()
        self.db_connection = db_connection
        self.fallback_file = fallback_file
        self.fallback_handler = None
        self._has_new_columns = None  # Cache schema check result
        
        # Ensure fallback directory exists
        if fallback_file:
            os.makedirs(os.path.dirname(fallback_file), exist_ok=True)
            self.fallback_handler = logging.FileHandler(fallback_file)
            self.fallback_handler.setFormatter(
                logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            )
        
        # Check schema once on initialization
        self._check_schema()
    
    def emit(self, record: logging.LogRecord):
        """Process a log record and store it in the database.
        
        Args:
            record: The log record to process
        """
        try:
            # Format the log message
            message = self._safe_format_message(record)
            
            # Get retention hours
            retention_hours = self._get_retention_hours(record)
            
            # Calculate expiration time
            timestamp = datetime.fromtimestamp(record.created)
            expires_at = timestamp + timedelta(hours=retention_hours)
            
            # Get organization context
            org_id, org_name, session_id = self._get_organization_context()
            
            # Prepare additional context
            additional_context = self._get_additional_context(record)
            
            # Log data to insert - include date/time if new columns exist
            log_data = {
                'timestamp': timestamp.isoformat(),
                'log_date': timestamp.date().isoformat() if self._has_new_columns else None,
                'log_time': timestamp.time().isoformat() if self._has_new_columns else None,
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
            
            # Insert into database
            self._insert_log_entry(log_data)
            
        except Exception as e:
            # Fall back to file logging if database fails
            self.handleError(record)
    
    def _safe_format_message(self, record: logging.LogRecord) -> str:
        """Safely format the log message.
        
        Args:
            record: The log record
            
        Returns:
            Formatted message string
        """
        try:
            return self.format(record) if self.formatter else record.getMessage()
        except Exception:
            return str(record.msg)
    
    def _get_retention_hours(self, record: logging.LogRecord) -> int:
        """Get retention hours based on log level and type.
        
        Args:
            record: The log record
            
        Returns:
            Number of hours to retain the log
        """
        # Check for special log type first
        log_type = getattr(record, 'log_type', None)
        if log_type and log_type in config.SPECIAL_LOG_RETENTION:
            return config.SPECIAL_LOG_RETENTION[log_type]
        
        # Use standard retention based on log level
        level_name = record.levelname
        return config.LOG_RETENTION_HOURS.get(level_name, 24)  # Default 24 hours
    
    def _get_organization_context(self) -> tuple:
        """Get organization context from Streamlit session state.
        
        Returns:
            Tuple of (organization_id, organization_name, session_id)
        """
        # Quick check if we're likely in a Streamlit context
        if 'streamlit' not in sys.modules:
            return None, None, None
            
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
            # Not in Streamlit context or session not available
            pass
        
        return org_id, org_name, session_id
    
    def _get_additional_context(self, record: logging.LogRecord) -> Optional[Dict[str, Any]]:
        """Extract additional context from the log record.
        
        Args:
            record: The log record
            
        Returns:
            Dictionary of additional context or None
        """
        context = {}
        
        # Add extra fields from record
        if hasattr(record, 'extra'):
            context.update(record.extra)
        
        # Add exception info if present
        if record.exc_info:
            context['exception'] = traceback.format_exception(*record.exc_info)
        
        # Add stack info if present
        if record.stack_info:
            context['stack'] = record.stack_info
        
        return context if context else None
    
    def _check_schema(self):
        """Check if new date/time columns exist in the database."""
        try:
            conn = self.db_connection or sqlite3.connect(database.DATABASE_FILE)
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(application_logs)")
            columns = [col[1] for col in cursor.fetchall()]
            self._has_new_columns = 'log_date' in columns and 'log_time' in columns
            if not self.db_connection:
                conn.close()
        except Exception:
            self._has_new_columns = False
    
    def _insert_log_entry(self, log_data: Dict[str, Any]):
        """Insert a log entry into the database.
        
        Args:
            log_data: Dictionary containing log data
        """
        conn = self.db_connection or sqlite3.connect(database.DATABASE_FILE)
        try:
            cursor = conn.cursor()
            
            if self._has_new_columns:
                # Use optimized insert with date/time columns
                cursor.execute("""
                    INSERT INTO application_logs (
                        timestamp, log_date, log_time, organization_id, organization_name, 
                        session_id, log_level, module, function_name, line_number, message,
                        retention_hours, expires_at, additional_context, log_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_data['timestamp'],
                    log_data['log_date'],
                    log_data['log_time'],
                    log_data['organization_id'],
                    log_data['organization_name'],
                    log_data['session_id'],
                    log_data['log_level'],
                    log_data['module'],
                    log_data['function_name'],
                    log_data['line_number'],
                    log_data['message'],
                    log_data['retention_hours'],
                    log_data['expires_at'],
                    log_data['additional_context'],
                    log_data['log_type']
                ))
            else:
                # Fallback to original insert without date/time columns
                cursor.execute("""
                    INSERT INTO application_logs (
                        timestamp, organization_id, organization_name, session_id,
                        log_level, module, function_name, line_number, message,
                        retention_hours, expires_at, additional_context, log_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    log_data['timestamp'],
                    log_data['organization_id'],
                    log_data['organization_name'],
                    log_data['session_id'],
                    log_data['log_level'],
                    log_data['module'],
                    log_data['function_name'],
                    log_data['line_number'],
                    log_data['message'],
                    log_data['retention_hours'],
                    log_data['expires_at'],
                    log_data['additional_context'],
                    log_data['log_type']
                ))
            
            if not self.db_connection:
                conn.commit()
                conn.close()
            else:
                conn.commit()
                
        except Exception as e:
            if not self.db_connection:
                conn.close()
            raise e
    
    def handleError(self, record: logging.LogRecord):
        """Handle errors by falling back to file logging.
        
        Args:
            record: The log record that caused the error
        """
        if self.fallback_handler:
            try:
                self.fallback_handler.emit(record)
            except Exception:
                # Last resort - print to stderr
                import sys
                print(f"LOGGING ERROR: Could not log message: {record.getMessage()}", file=sys.stderr)


def configure_database_logging(logger_name: Optional[str] = None, 
                              level: int = logging.INFO,
                              remove_existing: bool = True) -> logging.Logger:
    """Configure a logger to use database logging.
    
    Args:
        logger_name: Name of the logger (None for root logger)
        level: Logging level
        remove_existing: Whether to remove existing handlers
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(logger_name)
    logger.setLevel(level)
    
    # Remove existing handlers if requested
    if remove_existing:
        logger.handlers.clear()
    
    # Add database handler
    db_handler = DatabaseLogHandler()
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