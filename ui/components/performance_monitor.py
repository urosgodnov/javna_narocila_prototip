"""
Performance monitoring and optimization for admin UI
Tracks metrics and provides performance insights
"""

import streamlit as st
import time
from typing import Dict, List, Optional, Any
from functools import wraps
import psutil
import sys


class PerformanceMonitor:
    """Monitor and track performance metrics"""
    
    def __init__(self):
        """Initialize performance monitor"""
        if 'performance_metrics' not in st.session_state:
            st.session_state.performance_metrics = {
                'page_loads': [],
                'component_renders': {},
                'api_calls': [],
                'memory_usage': []
            }
    
    @staticmethod
    def track_page_load(page_name: str):
        """
        Track page load time
        
        Args:
            page_name: Name of the page being loaded
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                load_time = time.time() - start_time
                
                # Store metric
                if 'performance_metrics' in st.session_state:
                    st.session_state.performance_metrics['page_loads'].append({
                        'page': page_name,
                        'load_time': load_time,
                        'timestamp': time.time()
                    })
                
                # Show warning if slow
                if load_time > 2.0:
                    st.warning(f"Slow page load detected: {load_time:.2f}s")
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def track_component_render(component_name: str):
        """
        Track component render time
        
        Args:
            component_name: Name of the component
        """
        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                result = func(*args, **kwargs)
                render_time = time.time() - start_time
                
                # Store metric
                if 'performance_metrics' in st.session_state:
                    if component_name not in st.session_state.performance_metrics['component_renders']:
                        st.session_state.performance_metrics['component_renders'][component_name] = []
                    
                    st.session_state.performance_metrics['component_renders'][component_name].append({
                        'render_time': render_time,
                        'timestamp': time.time()
                    })
                
                return result
            return wrapper
        return decorator
    
    @staticmethod
    def get_memory_usage() -> Dict[str, float]:
        """
        Get current memory usage
        
        Returns:
            Dictionary with memory metrics
        """
        process = psutil.Process()
        memory_info = process.memory_info()
        
        return {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size in MB
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size in MB
            'percent': process.memory_percent()
        }
    
    @staticmethod
    def get_performance_summary() -> Dict[str, Any]:
        """
        Get performance summary
        
        Returns:
            Performance metrics summary
        """
        if 'performance_metrics' not in st.session_state:
            return {}
        
        metrics = st.session_state.performance_metrics
        
        # Calculate averages
        avg_page_load = 0
        if metrics['page_loads']:
            avg_page_load = sum(p['load_time'] for p in metrics['page_loads']) / len(metrics['page_loads'])
        
        component_avgs = {}
        for component, renders in metrics['component_renders'].items():
            if renders:
                component_avgs[component] = sum(r['render_time'] for r in renders) / len(renders)
        
        return {
            'avg_page_load': avg_page_load,
            'total_page_loads': len(metrics['page_loads']),
            'component_averages': component_avgs,
            'memory_usage': PerformanceMonitor.get_memory_usage()
        }
    
    @staticmethod
    def display_metrics():
        """Display performance metrics in UI"""
        from ui.components.modern_components import modern_card, progress_bar, status_badge
        
        summary = PerformanceMonitor.get_performance_summary()
        
        if not summary:
            st.info("Ni podatkov o zmogljivosti")
            return
        
        # Page load metrics
        modern_card(
            title="Zmogljivost strani",
            content=f"""
            <div style="font-size: 14px;">
                <p><strong>Povprečen čas nalaganja:</strong> {summary.get('avg_page_load', 0):.2f}s</p>
                <p><strong>Število nalaganj:</strong> {summary.get('total_page_loads', 0)}</p>
                <p><strong>Status:</strong> {
                    status_badge('success', 'HITER') if summary.get('avg_page_load', 0) < 1.0
                    else status_badge('warning', 'SREDNJI') if summary.get('avg_page_load', 0) < 2.0
                    else status_badge('error', 'POČASEN')
                }</p>
            </div>
            """,
            key="performance_card"
        )
        
        # Memory usage
        memory = summary.get('memory_usage', {})
        if memory:
            modern_card(
                title="Poraba pomnilnika",
                content=f"""
                <div style="font-size: 14px;">
                    <p><strong>RSS:</strong> {memory.get('rss_mb', 0):.1f} MB</p>
                    <p><strong>VMS:</strong> {memory.get('vms_mb', 0):.1f} MB</p>
                    {progress_bar(memory.get('percent', 0), f"{memory.get('percent', 0):.1f}% uporabljenega")}
                </div>
                """,
                key="memory_card"
            )


class PerformanceOptimizations:
    """Collection of performance optimization utilities"""
    
    @staticmethod
    def optimize_dataframe_display(df, max_rows: int = 100):
        """
        Optimize large dataframe display
        
        Args:
            df: Pandas dataframe
            max_rows: Maximum rows to display
            
        Returns:
            Optimized dataframe view
        """
        if len(df) > max_rows:
            st.info(f"Prikazujem prvih {max_rows} od {len(df)} vrstic")
            return df.head(max_rows)
        return df
    
    @staticmethod
    def batch_process_with_progress(items: List, process_func, batch_size: int = 10):
        """
        Process items in batches with progress
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            batch_size: Size of each batch
            
        Returns:
            Processed results
        """
        results = []
        total = len(items)
        
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        for i in range(0, total, batch_size):
            batch = items[i:i+batch_size]
            batch_results = [process_func(item) for item in batch]
            results.extend(batch_results)
            
            # Update progress
            progress = min((i + batch_size) / total, 1.0)
            progress_bar.progress(progress)
            status_text.text(f"Procesiranje: {min(i + batch_size, total)}/{total}")
        
        progress_bar.empty()
        status_text.empty()
        
        return results
    
    @staticmethod
    def lazy_load_images(image_urls: List[str], placeholder: str = "Nalagam slike..."):
        """
        Lazy load images
        
        Args:
            image_urls: List of image URLs
            placeholder: Placeholder text
            
        Returns:
            Container with lazy loaded images
        """
        container = st.container()
        
        with container:
            if 'images_loaded' not in st.session_state:
                st.session_state.images_loaded = False
            
            if not st.session_state.images_loaded:
                if st.button("Naloži slike"):
                    st.session_state.images_loaded = True
                    st.rerun()
                else:
                    st.info(placeholder)
            else:
                cols = st.columns(len(image_urls))
                for idx, url in enumerate(image_urls):
                    with cols[idx]:
                        st.image(url)
        
        return container


# Standalone optimization functions
def memoize_expensive_operation(ttl: int = 300):
    """
    Memoize expensive operations with TTL
    
    Args:
        ttl: Time to live in seconds
    """
    def decorator(func):
        @st.cache_data(ttl=ttl)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        return wrapper
    return decorator


def throttle_function(wait_time: float = 0.5):
    """
    Throttle function calls
    
    Args:
        wait_time: Minimum time between calls in seconds
    """
    def decorator(func):
        last_call = {'time': 0}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            current_time = time.time()
            if current_time - last_call['time'] < wait_time:
                return None
            last_call['time'] = current_time
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Export all utilities
__all__ = [
    'PerformanceMonitor',
    'PerformanceOptimizations',
    'memoize_expensive_operation',
    'throttle_function'
]