"""
Log Query Builder - Compatibility layer for optimized log queries
Story 33.2 implementation
"""

import sqlite3
from datetime import datetime, date, time
from typing import Optional, List, Dict, Any, Tuple
import database


class LogQueryBuilder:
    """Build optimized queries based on available database schema."""
    
    def __init__(self, connection: Optional[sqlite3.Connection] = None):
        """Initialize the query builder.
        
        Args:
            connection: Optional database connection, creates new if None
        """
        self.connection = connection
        self._owns_connection = connection is None
        self._has_new_columns = self._detect_schema()
    
    def _detect_schema(self) -> bool:
        """Detect if new date/time columns are available.
        
        Returns:
            True if log_date and log_time columns exist
        """
        try:
            conn = self.connection or sqlite3.connect(database.DATABASE_FILE)
            cursor = conn.cursor()
            
            # First ensure the table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='application_logs'")
            if not cursor.fetchone():
                if self._owns_connection and not self.connection:
                    conn.close()
                return False
            
            cursor.execute("PRAGMA table_info(application_logs)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if self._owns_connection and not self.connection:
                conn.close()
            
            # Only return True if BOTH columns exist
            has_columns = 'log_date' in columns and 'log_time' in columns
            return has_columns
        except Exception as e:
            # Log the error for debugging but don't crash
            print(f"Error detecting schema: {e}")
            return False
    
    def date_range_query(self, 
                        start_date: Optional[date] = None, 
                        end_date: Optional[date] = None,
                        additional_filters: Optional[Dict[str, Any]] = None) -> Tuple[str, List]:
        """Build a date range query.
        
        Args:
            start_date: Start date for filtering
            end_date: End date for filtering
            additional_filters: Additional filter conditions
            
        Returns:
            Tuple of (query_string, parameters)
        """
        params = []
        
        if self._has_new_columns:
            # Use optimized query with indexed date column
            query = "SELECT * FROM application_logs WHERE 1=1"
            
            if start_date and end_date:
                query += " AND log_date BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            elif start_date:
                query += " AND log_date >= ?"
                params.append(start_date)
            elif end_date:
                query += " AND log_date <= ?"
                params.append(end_date)
        else:
            # Fallback to timestamp-based query
            query = "SELECT * FROM application_logs WHERE 1=1"
            
            if start_date and end_date:
                query += " AND DATE(timestamp) BETWEEN ? AND ?"
                params.extend([start_date, end_date])
            elif start_date:
                query += " AND DATE(timestamp) >= ?"
                params.append(start_date)
            elif end_date:
                query += " AND DATE(timestamp) <= ?"
                params.append(end_date)
        
        # Add additional filters
        if additional_filters:
            query, params = self._add_filters(query, params, additional_filters)
        
        # Add ordering
        if self._has_new_columns:
            query += " ORDER BY log_date DESC, log_time DESC"
        else:
            query += " ORDER BY timestamp DESC"
        
        return query, params
    
    def time_range_query(self, 
                        start_time: Optional[time] = None,
                        end_time: Optional[time] = None,
                        date_filter: Optional[date] = None) -> Tuple[str, List]:
        """Build a time range query (only works with new columns).
        
        Args:
            start_time: Start time for filtering
            end_time: End time for filtering
            date_filter: Optional date to filter on
            
        Returns:
            Tuple of (query_string, parameters)
        """
        if not self._has_new_columns:
            # Can't efficiently filter by time without new columns
            return self.date_range_query(date_filter, date_filter)
        
        query = "SELECT * FROM application_logs WHERE 1=1"
        params = []
        
        if date_filter:
            query += " AND log_date = ?"
            params.append(date_filter)
        
        if start_time and end_time:
            query += " AND log_time BETWEEN ? AND ?"
            params.extend([start_time, end_time])
        elif start_time:
            query += " AND log_time >= ?"
            params.append(start_time)
        elif end_time:
            query += " AND log_time <= ?"
            params.append(end_time)
        
        query += " ORDER BY log_date DESC, log_time DESC"
        
        return query, params
    
    def filtered_query(self, filters: Dict[str, Any]) -> Tuple[str, List]:
        """Build a query with multiple filters.
        
        Args:
            filters: Dictionary of filter conditions
            
        Returns:
            Tuple of (query_string, parameters)
        """
        # Extract date/time filters
        start_date = filters.pop('date_from', None)
        end_date = filters.pop('date_to', None)
        start_time = filters.pop('time_from', None)
        end_time = filters.pop('time_to', None)
        
        # Start with date range query
        query, params = self.date_range_query(start_date, end_date)
        
        # Add time filtering if available
        if self._has_new_columns and (start_time or end_time):
            time_conditions = []
            if start_time:
                time_conditions.append("log_time >= ?")
                params.append(start_time)
            if end_time:
                time_conditions.append("log_time <= ?")
                params.append(end_time)
            
            if time_conditions:
                # Remove ORDER BY temporarily
                query = query.replace(" ORDER BY log_date DESC, log_time DESC", "")
                query = query.replace(" ORDER BY timestamp DESC", "")
                query += " AND " + " AND ".join(time_conditions)
                
                # Re-add ORDER BY
                if self._has_new_columns:
                    query += " ORDER BY log_date DESC, log_time DESC"
                else:
                    query += " ORDER BY timestamp DESC"
        
        # Add other filters
        query, params = self._add_filters(query, params, filters)
        
        return query, params
    
    def _add_filters(self, query: str, params: List, filters: Dict[str, Any]) -> Tuple[str, List]:
        """Add additional filter conditions to a query.
        
        Args:
            query: Current query string
            params: Current parameters list
            filters: Additional filters to add
            
        Returns:
            Updated (query, params) tuple
        """
        # Remove ORDER BY temporarily if present
        order_clause = ""
        if "ORDER BY" in query:
            parts = query.split("ORDER BY")
            query = parts[0]
            order_clause = "ORDER BY" + parts[1]
        
        # Add filters
        if filters.get('log_levels'):
            levels = filters['log_levels']
            if isinstance(levels, list) and levels:
                placeholders = ','.join(['?' for _ in levels])
                query += f" AND log_level IN ({placeholders})"
                params.extend(levels)
        
        if filters.get('organization_name'):
            query += " AND organization_name = ?"
            params.append(filters['organization_name'])
        
        if filters.get('organization_id'):
            query += " AND organization_id = ?"
            params.append(filters['organization_id'])
        
        if filters.get('module'):
            query += " AND module = ?"
            params.append(filters['module'])
        
        if filters.get('search_query'):
            search = f"%{filters['search_query']}%"
            query += " AND message LIKE ?"
            params.append(search)
        
        if filters.get('log_type'):
            query += " AND log_type = ?"
            params.append(filters['log_type'])
        
        # Re-add ORDER BY
        query += " " + order_clause if order_clause else ""
        
        return query, params
    
    def recent_logs_query(self, limit: int = 100) -> Tuple[str, List]:
        """Get the most recent logs.
        
        Args:
            limit: Maximum number of logs to return
            
        Returns:
            Tuple of (query_string, parameters)
        """
        if self._has_new_columns:
            query = """
                SELECT * FROM application_logs 
                ORDER BY log_date DESC, log_time DESC 
                LIMIT ?
            """
        else:
            query = """
                SELECT * FROM application_logs 
                ORDER BY timestamp DESC 
                LIMIT ?
            """
        
        return query, [limit]
    
    def statistics_query(self, start_date: Optional[date] = None, end_date: Optional[date] = None) -> Dict[str, Tuple[str, List]]:
        """Get queries for statistics.
        
        Args:
            start_date: Start date for statistics
            end_date: End date for statistics
            
        Returns:
            Dictionary of query names to (query, params) tuples
        """
        queries = {}
        
        # Base date filter
        if self._has_new_columns:
            date_filter = " WHERE log_date BETWEEN ? AND ?" if start_date and end_date else " WHERE 1=1"
        else:
            date_filter = " WHERE DATE(timestamp) BETWEEN ? AND ?" if start_date and end_date else " WHERE 1=1"
        
        date_params = [start_date, end_date] if start_date and end_date else []
        
        # Total count
        queries['total_count'] = (
            f"SELECT COUNT(*) as count FROM application_logs{date_filter}",
            date_params
        )
        
        # Count by level
        queries['by_level'] = (
            f"SELECT log_level, COUNT(*) as count FROM application_logs{date_filter} GROUP BY log_level",
            date_params
        )
        
        # Count by date (if using new columns)
        if self._has_new_columns:
            queries['by_date'] = (
                f"SELECT log_date, COUNT(*) as count FROM application_logs{date_filter} GROUP BY log_date ORDER BY log_date DESC",
                date_params
            )
            
            # Count by hour
            queries['by_hour'] = (
                f"SELECT strftime('%H', log_time) as hour, COUNT(*) as count FROM application_logs{date_filter} GROUP BY hour ORDER BY hour",
                date_params
            )
        
        return queries
    
    def has_optimized_columns(self) -> bool:
        """Check if optimized columns are available.
        
        Returns:
            True if log_date and log_time columns exist
        """
        return self._has_new_columns
    
    def close(self):
        """Close the connection if owned by this builder."""
        if self._owns_connection and self.connection:
            self.connection.close()