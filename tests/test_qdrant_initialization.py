#!/usr/bin/env python3
"""
Unit tests for Qdrant collection initialization (Story 27.1).
Tests non-blocking behavior, idempotent operations, and proper error handling.
"""
import pytest
import os
import sys
from unittest.mock import Mock, patch, MagicMock
from typing import List

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.qdrant_init import (
    get_qdrant_client,
    init_qdrant_collection,
    check_qdrant_status,
    init_qdrant_on_startup,
    ensure_qdrant_initialized,
    METADATA_SCHEMA,
    COLLECTION_NAME,
    VECTOR_SIZE,
    DISTANCE_METRIC
)


class TestQdrantInitialization:
    """Test suite for Story 27.1: Create Qdrant Collection with Metadata Schema."""
    
    @pytest.fixture
    def mock_qdrant_client(self):
        """Create a mock Qdrant client."""
        with patch('utils.qdrant_init.QdrantClient') as mock_client_class:
            mock_client = Mock()
            mock_client_class.return_value = mock_client
            yield mock_client
    
    @pytest.fixture
    def mock_env_vars(self):
        """Mock environment variables for Qdrant."""
        with patch.dict(os.environ, {
            'QDRANT_URL': 'https://test.qdrant.io:6333',
            'QDRANT_API_KEY': 'test-api-key'
        }):
            yield
    
    def test_collection_constants(self):
        """Test that collection constants match Story 27.1 requirements."""
        assert COLLECTION_NAME == "javna_narocila"
        assert VECTOR_SIZE == 1536  # For text-embedding-3-small
        assert DISTANCE_METRIC == "Cosine"
    
    def test_metadata_schema_completeness(self):
        """Test that metadata schema contains all required fields from Story 27.1."""
        required_fields = [
            'document_id', 'document_type', 'organization', 'created_at',
            'form_id', 'chunk_index', 'total_chunks', 'original_filename',
            'file_format', 'embedding_model', 'extraction_method'
        ]
        
        for field in required_fields:
            assert field in METADATA_SCHEMA, f"Missing required field: {field}"
    
    def test_get_qdrant_client_with_url(self, mock_env_vars):
        """Test client creation with QDRANT_URL environment variable."""
        with patch('utils.qdrant_init.QdrantClient') as mock_client_class:
            client = get_qdrant_client()
            
            if client:  # Only if qdrant-client is installed
                mock_client_class.assert_called_once()
                call_args = mock_client_class.call_args
                assert call_args[1]['url'] == 'https://test.qdrant.io:6333'
                assert call_args[1]['api_key'] == 'test-api-key'
    
    def test_get_qdrant_client_with_host_port(self):
        """Test client creation with QDRANT_HOST and QDRANT_PORT (backward compatibility)."""
        with patch.dict(os.environ, {
            'QDRANT_HOST': 'localhost',
            'QDRANT_PORT': '6333',
            'QDRANT_API_KEY': 'test-key'
        }, clear=True):
            with patch('utils.qdrant_init.QdrantClient') as mock_client_class:
                client = get_qdrant_client()
                
                if client:  # Only if qdrant-client is installed
                    call_args = mock_client_class.call_args
                    assert 'localhost' in call_args[1]['url']
                    assert '6333' in call_args[1]['url']
    
    def test_get_qdrant_client_without_package(self):
        """Test that missing qdrant-client package is handled gracefully."""
        with patch('utils.qdrant_init.QdrantClient', side_effect=ImportError):
            client = get_qdrant_client()
            assert client is None  # Should return None, not raise
    
    def test_init_collection_creates_new(self, mock_qdrant_client):
        """Test creating a new collection when it doesn't exist."""
        # Mock empty collections
        mock_response = Mock()
        mock_response.collections = []
        mock_qdrant_client.get_collections.return_value = mock_response
        
        with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
            result = init_qdrant_collection()
        
        # Verify collection was created
        mock_qdrant_client.create_collection.assert_called_once()
        assert result['success'] is True
        assert result['created'] is True
        assert result['collection_name'] == 'javna_narocila'
        assert result['vector_size'] == 1536
    
    def test_init_collection_already_exists(self, mock_qdrant_client):
        """Test idempotent behavior when collection already exists."""
        # Mock existing collection
        mock_collection = Mock()
        mock_collection.name = "javna_narocila"
        mock_response = Mock()
        mock_response.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_response
        
        with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
            result = init_qdrant_collection(force=False)
        
        # Should NOT create collection
        mock_qdrant_client.create_collection.assert_not_called()
        assert result['success'] is True
        assert result['exists'] is True
        assert result['created'] is False
    
    def test_init_collection_force_recreate(self, mock_qdrant_client):
        """Test force recreation of existing collection."""
        # Mock existing collection
        mock_collection = Mock()
        mock_collection.name = "javna_narocila"
        mock_response = Mock()
        mock_response.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_response
        
        with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
            result = init_qdrant_collection(force=True)
        
        # Should delete and recreate
        mock_qdrant_client.delete_collection.assert_called_once_with(
            collection_name="javna_narocila"
        )
        mock_qdrant_client.create_collection.assert_called_once()
        assert result['success'] is True
        assert result['created'] is True
    
    def test_init_collection_non_blocking_on_error(self, mock_qdrant_client):
        """Test non-blocking behavior when Qdrant is unavailable."""
        # Mock connection error
        mock_qdrant_client.get_collections.side_effect = Exception("Connection refused")
        
        with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
            result = init_qdrant_collection()
        
        # Should return failure but not raise exception
        assert result['success'] is False
        assert "Connection refused" in result['message']
        # App should continue (non-blocking requirement from Story 27.1)
    
    def test_init_collection_without_qdrant_client(self):
        """Test initialization when qdrant-client is not installed."""
        with patch('utils.qdrant_init.get_qdrant_client', return_value=None):
            result = init_qdrant_collection()
        
        assert result['success'] is False
        assert "without vector database" in result['message']
    
    def test_check_status_connected(self, mock_qdrant_client):
        """Test status check when connected to Qdrant."""
        # Mock successful connection
        mock_collection = Mock()
        mock_collection.name = "javna_narocila"
        mock_response = Mock()
        mock_response.collections = [mock_collection]
        mock_qdrant_client.get_collections.return_value = mock_response
        
        # Mock collection info
        mock_info = Mock()
        mock_info.vectors_count = 42
        mock_info.config.params.vectors.size = 1536
        mock_info.config.params.vectors.distance = "Cosine"
        mock_qdrant_client.get_collection.return_value = mock_info
        
        with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
            status = check_qdrant_status()
        
        assert status['connected'] is True
        assert status['collection_exists'] is True
        assert status['vector_count'] == 42
        assert status['config']['vector_size'] == 1536
    
    def test_check_status_not_connected(self):
        """Test status check when Qdrant is not available."""
        with patch('utils.qdrant_init.get_qdrant_client', return_value=None):
            status = check_qdrant_status()
        
        assert status['connected'] is False
        assert status['collection_exists'] is False
        assert status['error'] == "Client not available"
    
    def test_init_on_startup_success(self, mock_qdrant_client):
        """Test initialization on app startup (app.py integration)."""
        mock_response = Mock()
        mock_response.collections = []
        mock_qdrant_client.get_collections.return_value = mock_response
        
        with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
            result = init_qdrant_on_startup()
        
        assert result['success'] is True
        mock_qdrant_client.create_collection.assert_called_once()
    
    def test_init_on_startup_non_blocking(self):
        """Test that startup initialization is non-blocking on errors."""
        with patch('utils.qdrant_init.init_qdrant_collection') as mock_init:
            mock_init.side_effect = Exception("Unexpected error")
            
            # Should catch exception and return error result
            result = init_qdrant_on_startup()
            
            assert result['success'] is False
            assert "Unexpected error" in result['message']
            # App should continue running (non-blocking requirement)
    
    @patch('utils.qdrant_init.st')
    def test_ensure_initialized_with_streamlit(self, mock_st, mock_qdrant_client):
        """Test Streamlit integration for initialization."""
        # Mock session state
        mock_st.session_state = {}
        
        # Mock successful initialization
        mock_response = Mock()
        mock_response.collections = []
        mock_qdrant_client.get_collections.return_value = mock_response
        
        with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
            result = ensure_qdrant_initialized()
        
        # Should set session state
        assert mock_st.session_state.get('qdrant_initialized') is not None
        
        # Should show success message if created
        if result:
            assert mock_st.success.called or mock_st.warning.called
    
    def test_ensure_initialized_without_streamlit(self, mock_qdrant_client):
        """Test initialization outside of Streamlit context."""
        # Mock no Streamlit available
        with patch('utils.qdrant_init.st', side_effect=ImportError):
            mock_response = Mock()
            mock_response.collections = []
            mock_qdrant_client.get_collections.return_value = mock_response
            
            with patch('utils.qdrant_init.get_qdrant_client', return_value=mock_qdrant_client):
                result = ensure_qdrant_initialized()
            
            # Should still work without Streamlit
            assert isinstance(result, bool)


class TestIntegrationRequirements:
    """Test integration requirements from Story 27.1."""
    
    def test_follows_init_database_pattern(self):
        """Test that initialization follows the pattern from init_database.py."""
        # Check that functions exist with similar signatures
        assert callable(init_qdrant_collection)
        assert callable(check_qdrant_status)
        assert callable(init_qdrant_on_startup)
        
        # Check that they return dicts with status information
        with patch('utils.qdrant_init.get_qdrant_client', return_value=None):
            result = init_qdrant_collection()
            assert isinstance(result, dict)
            assert 'success' in result
            assert 'message' in result
    
    def test_logging_approach(self):
        """Test that logging is used appropriately."""
        with patch('utils.qdrant_init.logger') as mock_logger:
            with patch('utils.qdrant_init.get_qdrant_client', return_value=None):
                init_qdrant_collection()
            
            # Should log warnings for failures
            assert mock_logger.warning.called
    
    def test_non_blocking_behavior(self):
        """Test that all operations are non-blocking as required."""
        # Test each function with errors - none should raise
        with patch('utils.qdrant_init.get_qdrant_client', side_effect=Exception):
            try:
                get_qdrant_client()  # Should return None
                init_qdrant_collection()  # Should return error dict
                check_qdrant_status()  # Should return error status
                init_qdrant_on_startup()  # Should return error dict
                ensure_qdrant_initialized()  # Should return False
            except Exception:
                pytest.fail("Functions should be non-blocking but raised an exception")


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])