#!/usr/bin/env python3
"""
Qdrant collection initialization module for vector database.
Follows the pattern established in init_database.py for non-blocking initialization.
"""
import os
import logging
from typing import Dict, Any, Optional
from datetime import datetime

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available, rely on system environment
    pass

# Set up logging
logger = logging.getLogger(__name__)

# Metadata schema definition for the collection
METADATA_SCHEMA = {
    'document_id': 'string',           # Unique document identifier
    'document_type': 'string',         # procurement, contract, specification, etc.
    'organization': 'string',          # Organization name
    'created_at': 'datetime',          # Creation timestamp
    'form_id': 'integer',              # Reference to form if applicable
    'chunk_index': 'integer',          # Chunk position in document
    'total_chunks': 'integer',         # Total number of chunks
    'original_filename': 'string',     # Original file name
    'file_format': 'string',           # pdf, docx, html, etc.
    'embedding_model': 'string',       # text-embedding-3-small
    'extraction_method': 'string',     # docling
}

# Collection configuration constants
COLLECTION_NAME = "javna_narocila"
VECTOR_SIZE = 1536  # For text-embedding-3-small
DISTANCE_METRIC = "Cosine"


def get_qdrant_client() -> Optional[Any]:
    """
    Get Qdrant client instance with configuration from environment.
    Returns None if client cannot be created (non-blocking).
    
    Returns:
        QdrantClient instance or None if unavailable
    """
    try:
        from qdrant_client import QdrantClient
        
        # Get configuration from environment with defaults
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")
        
        # If no URL provided, try constructing from host/port for backward compatibility
        if not url:
            host = os.getenv("QDRANT_HOST", "localhost")
            port = os.getenv("QDRANT_PORT", "6333")
            url = f"http://{host}:{port}"
        
        if not api_key:
            logger.warning("QDRANT_API_KEY not found in environment variables")
            # Continue anyway - might be local instance without auth
        
        client = QdrantClient(url=url, api_key=api_key)
        return client
        
    except ImportError:
        logger.warning("qdrant-client package not installed. Vector database features will be unavailable.")
        return None
    except Exception as e:
        logger.warning(f"Could not create Qdrant client: {e}")
        return None


def init_qdrant_collection(force: bool = False) -> Dict[str, Any]:
    """
    Initialize Qdrant collection for javna_narocila if not exists.
    Non-blocking: returns status but doesn't stop app if fails.
    
    Args:
        force: Force re-creation of collection even if it exists
    
    Returns:
        Dict with initialization results including success status
    """
    result = {
        'success': False,
        'created': False,
        'exists': False,
        'message': '',
        'collection_name': COLLECTION_NAME,
        'vector_size': VECTOR_SIZE,
        'distance': DISTANCE_METRIC
    }
    
    try:
        # Try to import Qdrant dependencies
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
        except ImportError as e:
            result['message'] = "Qdrant client not installed. Run: pip install qdrant-client"
            logger.warning(result['message'])
            return result
        
        # Get client
        client = get_qdrant_client()
        if not client:
            result['message'] = "Could not connect to Qdrant. App continuing without vector database."
            return result
        
        # Check existing collections
        try:
            collections = client.get_collections()
            collection_names = [c.name for c in collections.collections]
            
            if COLLECTION_NAME in collection_names:
                result['exists'] = True
                
                if not force:
                    result['success'] = True
                    result['message'] = f"Collection '{COLLECTION_NAME}' already exists"
                    logger.info(result['message'])
                    return result
                else:
                    # Delete existing collection if force is True
                    client.delete_collection(collection_name=COLLECTION_NAME)
                    logger.info(f"Deleted existing '{COLLECTION_NAME}' collection for re-creation")
        except Exception as e:
            # If we can't check collections, try to create anyway
            logger.warning(f"Could not check existing collections: {e}")
        
        # Create collection with proper configuration
        distance_enum = Distance.COSINE  # Use the enum directly
        
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=distance_enum
            )
        )
        
        result['success'] = True
        result['created'] = True
        result['message'] = f"Created '{COLLECTION_NAME}' collection in Qdrant"
        logger.info(result['message'])
        logger.info(f"Collection configured: vectors={VECTOR_SIZE}d, distance={DISTANCE_METRIC}")
        
    except Exception as e:
        # Handle any errors gracefully - app continues
        result['message'] = f"Could not initialize Qdrant collection: {str(e)}"
        logger.warning(result['message'])
        # Non-blocking - app continues without vector database
    
    return result


def check_qdrant_status() -> Dict[str, Any]:
    """
    Check the status of Qdrant collection.
    Non-blocking status check for monitoring.
    
    Returns:
        Dict with status information
    """
    status = {
        'connected': False,
        'collection_exists': False,
        'collection_name': COLLECTION_NAME,
        'vector_count': 0,
        'config': None,
        'error': None
    }
    
    try:
        client = get_qdrant_client()
        if not client:
            status['error'] = "Client not available"
            return status
        
        # Check connection by getting collections
        collections = client.get_collections()
        status['connected'] = True
        
        # Check if our collection exists
        collection_names = [c.name for c in collections.collections]
        if COLLECTION_NAME in collection_names:
            status['collection_exists'] = True
            
            # Try to get collection info
            try:
                collection_info = client.get_collection(collection_name=COLLECTION_NAME)
                status['vector_count'] = collection_info.vectors_count or 0
                status['config'] = {
                    'vector_size': collection_info.config.params.vectors.size,
                    'distance': str(collection_info.config.params.vectors.distance)
                }
            except Exception as e:
                logger.debug(f"Could not get collection details: {e}")
    
    except Exception as e:
        status['error'] = str(e)
        logger.debug(f"Error checking Qdrant status: {e}")
    
    return status


def ensure_qdrant_initialized():
    """
    Ensure Qdrant collection is initialized when needed.
    Can be called from Streamlit context or regular Python.
    Non-blocking - returns status but doesn't stop execution.
    
    Returns:
        bool: True if initialized successfully or already exists
    """
    try:
        # Try Streamlit session state if available
        import streamlit as st
        
        if 'qdrant_initialized' not in st.session_state:
            st.session_state.qdrant_initialized = False
        
        if not st.session_state.qdrant_initialized:
            result = init_qdrant_collection()
            if result['success']:
                st.session_state.qdrant_initialized = True
                if result['created']:
                    st.success(f"✅ Vector database initialized: '{result['collection_name']}'")
                else:
                    logger.info(f"Vector database ready: '{result['collection_name']}'")
            else:
                st.warning(f"⚠️ Vector database unavailable: {result['message']}")
                # Continue anyway - non-blocking
                st.session_state.qdrant_initialized = False
        
        return st.session_state.qdrant_initialized
        
    except (ImportError, Exception):
        # Not in Streamlit context or error - just initialize directly
        result = init_qdrant_collection()
        return result['success']


def init_qdrant_on_startup():
    """
    Initialize Qdrant collection on app startup.
    Called from app.py init_app_data() function.
    Non-blocking: logs status but doesn't stop app.
    
    Returns:
        Dict with initialization results
    """
    try:
        result = init_qdrant_collection()
        
        if result['success']:
            if result['created']:
                logger.info(f"✅ Qdrant: {result['message']}")
            else:
                logger.info(f"ℹ️ Qdrant: {result['message']}")
        else:
            logger.warning(f"⚠️ Qdrant: {result['message']}")
            # Non-blocking - app continues without vector database
        
        return result
        
    except Exception as e:
        logger.warning(f"Qdrant initialization error: {e}")
        # Non-blocking - app continues
        return {
            'success': False,
            'message': str(e)
        }


# Module initialization check
def _check_dependencies():
    """Check if required dependencies are available."""
    try:
        import qdrant_client
        return True
    except ImportError:
        logger.info("qdrant-client not installed. Install with: pip install qdrant-client")
        return False


# Check dependencies when module is imported
QDRANT_AVAILABLE = _check_dependencies()


if __name__ == "__main__":
    # Module can be run directly for testing
    import sys
    
    # Set up console logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("=" * 50)
    print("Qdrant Collection Initialization Test")
    print("=" * 50)
    
    # Check dependencies
    if not QDRANT_AVAILABLE:
        print("⚠️ qdrant-client not installed")
        print("Install with: pip install qdrant-client")
        sys.exit(1)
    
    # Check current status
    print("\nChecking current status...")
    status = check_qdrant_status()
    print(f"Connected: {status['connected']}")
    print(f"Collection exists: {status['collection_exists']}")
    
    if status['collection_exists']:
        print(f"Vector count: {status['vector_count']}")
        if status['config']:
            print(f"Configuration: {status['config']}")
        
        response = input("\nCollection exists. Force re-creation? (y/N): ")
        force = response.lower() == 'y'
    else:
        force = False
    
    # Initialize
    print("\nInitializing collection...")
    result = init_qdrant_collection(force=force)
    
    print("\n" + "=" * 50)
    if result['success']:
        print(f"✅ Success! {result['message']}")
        print(f"   Collection: {result['collection_name']}")
        print(f"   Vector size: {result['vector_size']}")
        print(f"   Distance: {result['distance']}")
    else:
        print(f"⚠️ Warning! {result['message']}")
        print("   App would continue without vector database")
    print("=" * 50)