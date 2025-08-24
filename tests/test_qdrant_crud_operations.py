#!/usr/bin/env python3
"""
Comprehensive tests for Qdrant CRUD operations (Story 27.3)
Tests search, update, delete, and batch operations
"""

import pytest
import os
import sys
import tempfile
import json
import sqlite3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
import uuid

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.qdrant_crud_service import QdrantCRUDService
from services.qdrant_document_processor import QdrantDocumentProcessor


class TestQdrantCRUDOperations:
    """Test suite for CRUD operations on Qdrant vector database."""
    
    @pytest.fixture
    def crud_service(self):
        """Create CRUD service with mocked clients."""
        with patch('services.qdrant_crud_service.get_qdrant_client'):
            with patch('services.qdrant_crud_service.OpenAI'):
                service = QdrantCRUDService()
                return service
    
    @pytest.fixture
    def sample_document(self):
        """Create a sample document for testing."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("""
            Test Procurement Document
            
            This document contains procurement specifications.
            It includes requirements for computer equipment.
            Budget: 50,000 EUR
            Delivery: 30 days
            """)
            return f.name
    
    def test_search_documents(self, crud_service):
        """Test document search functionality."""
        # Mock OpenAI embedding
        crud_service.openai_client = Mock()
        crud_service.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        # Mock Qdrant search
        mock_result = Mock(
            score=0.85,
            id=str(uuid.uuid4()),
            payload={
                "document_id": "test_001",
                "original_filename": "test.pdf",
                "document_type": "procurement",
                "organization": "test_org",
                "chunk_text": "Test procurement content",
                "chunk_index": 0,
                "total_chunks": 5
            }
        )
        crud_service.qdrant_client = Mock()
        crud_service.qdrant_client.search.return_value = [mock_result]
        
        # Perform search
        results, total = crud_service.search_documents(
            query="procurement equipment",
            filters={"document_type": "procurement"},
            limit=10
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0]["score"] == 0.85
        assert results[0]["document_id"] == "test_001"
        assert "procurement" in results[0]["chunk_text"].lower()
        
        # Verify search was called with correct parameters
        crud_service.qdrant_client.search.assert_called_once()
        call_args = crud_service.qdrant_client.search.call_args
        assert call_args[1]["limit"] == 10
    
    def test_search_with_filters(self, crud_service):
        """Test search with metadata filters."""
        # Mock clients
        crud_service.openai_client = Mock()
        crud_service.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        crud_service.qdrant_client = Mock()
        crud_service.qdrant_client.search.return_value = []
        
        # Search with multiple filters
        filters = {
            "document_type": "contract",
            "organization": "demo_org",
            "file_format": "pdf"
        }
        
        results, total = crud_service.search_documents(
            query="test query",
            filters=filters,
            limit=5
        )
        
        # Verify filter was built correctly
        call_args = crud_service.qdrant_client.search.call_args
        assert call_args[1]["filter"] is not None
    
    def test_update_document_metadata(self, crud_service):
        """Test updating document metadata."""
        # Mock database
        with patch('services.qdrant_crud_service.sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Mock Qdrant client
            crud_service.qdrant_client = Mock()
            mock_point = Mock(id=str(uuid.uuid4()))
            crud_service._get_document_points = Mock(return_value=[mock_point])
            
            # Update metadata
            updates = {
                "document_type": "updated_type",
                "organization": "new_org",
                "tags": ["important", "reviewed"]
            }
            
            result = crud_service.update_document_metadata("test_001", updates)
            
            # Verify update was successful
            assert result is True
            
            # Verify database was updated
            mock_cursor.execute.assert_called()
            mock_conn.commit.assert_called_once()
            
            # Verify Qdrant was updated
            crud_service.qdrant_client.set_payload.assert_called_once()
    
    def test_delete_document(self, crud_service):
        """Test document deletion."""
        # Mock database
        with patch('services.qdrant_crud_service.sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_cursor.rowcount = 1
            mock_conn.cursor.return_value = mock_cursor
            mock_connect.return_value = mock_conn
            
            # Mock Qdrant
            crud_service.qdrant_client = Mock()
            mock_points = [Mock(id=str(uuid.uuid4())) for _ in range(3)]
            crud_service._get_document_points = Mock(return_value=mock_points)
            
            # Delete document
            result = crud_service.delete_document("test_001")
            
            # Verify deletion
            assert result is True
            
            # Verify Qdrant deletion
            crud_service.qdrant_client.delete.assert_called_once()
            
            # Verify database deletion
            assert mock_cursor.execute.call_count >= 1
            mock_conn.commit.assert_called_once()
    
    def test_batch_delete(self, crud_service):
        """Test batch document deletion."""
        # Mock individual delete
        crud_service.delete_document = Mock(side_effect=[True, True, False])
        
        # Batch delete
        doc_ids = ["doc_001", "doc_002", "doc_003"]
        results = crud_service.batch_delete(doc_ids)
        
        # Verify results
        assert results["doc_001"] is True
        assert results["doc_002"] is True
        assert results["doc_003"] is False
        
        # Verify each document was attempted
        assert crud_service.delete_document.call_count == 3
    
    def test_get_collection_stats(self, crud_service):
        """Test collection statistics retrieval."""
        # Mock Qdrant stats
        mock_collection = Mock(vectors_count=1500)
        crud_service.qdrant_client = Mock()
        crud_service.qdrant_client.get_collection.return_value = mock_collection
        
        # Mock database stats
        with patch('services.qdrant_crud_service.sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock query results
            mock_cursor.fetchone.side_effect = [
                ('ai_documents',),  # Table exists
                (10,),  # Total documents
                (150,),  # Total chunks
                None  # Latest document
            ]
            mock_cursor.fetchall.side_effect = [
                [('org1',), ('org2',)],  # Organizations
                [('procurement',), ('contract',)]  # Document types
            ]
            
            mock_connect.return_value = mock_conn
            
            # Get stats
            stats = crud_service.get_collection_stats()
            
            # Verify stats
            assert stats["total_vectors"] == 1500
            assert stats["total_documents"] == 10
            assert stats["total_chunks"] == 150
            assert len(stats["organizations"]) == 2
            assert len(stats["document_types"]) == 2
            assert stats["collection_exists"] is True
    
    def test_export_metadata(self, crud_service):
        """Test metadata export functionality."""
        with patch('services.qdrant_crud_service.sqlite3.connect') as mock_connect:
            mock_conn = Mock()
            mock_cursor = Mock()
            mock_conn.cursor.return_value = mock_cursor
            
            # Mock query results
            mock_cursor.description = [
                ('document_id',), ('original_filename',), ('document_type',)
            ]
            mock_cursor.fetchall.return_value = [
                ('doc_001', 'file1.pdf', 'procurement'),
                ('doc_002', 'file2.docx', 'contract')
            ]
            
            mock_connect.return_value = mock_conn
            
            # Export metadata
            metadata = crud_service.export_metadata(['doc_001', 'doc_002'])
            
            # Verify export
            assert len(metadata) == 2
            assert metadata[0]['document_id'] == 'doc_001'
            assert metadata[1]['original_filename'] == 'file2.docx'
    
    def test_get_document_points(self, crud_service):
        """Test retrieving points for a document."""
        # Mock Qdrant scroll
        mock_points = [Mock(id=str(uuid.uuid4())) for _ in range(5)]
        crud_service.qdrant_client = Mock()
        crud_service.qdrant_client.scroll.return_value = (mock_points, None)
        
        # Get points
        points = crud_service._get_document_points("test_001")
        
        # Verify
        assert len(points) == 5
        crud_service.qdrant_client.scroll.assert_called_once()
    
    def test_ensure_indexes(self, crud_service):
        """Test index creation for filtering."""
        crud_service.qdrant_client = Mock()
        
        # Re-run index creation
        crud_service._ensure_indexes()
        
        # Verify indexes were created for key fields
        calls = crud_service.qdrant_client.create_payload_index.call_count
        assert calls >= 5  # At least 5 fields should have indexes


class TestIntegrationWorkflow:
    """Integration tests for complete CRUD workflow."""
    
    @pytest.mark.integration
    def test_complete_document_lifecycle(self):
        """Test complete document lifecycle: upload, search, update, delete."""
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            pytest.skip("Integration tests not enabled")
        
        # Force correct environment
        os.environ['QDRANT_URL'] = 'https://df29e6ff-cca0-4d8c-826e-043a5685787b.europe-west3-0.gcp.cloud.qdrant.io'
        os.environ['QDRANT_API_KEY'] = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.M0KeDYWo0pgA9wP7RfQyL2XjpzXla0TwU1geTVI_Hro'
        
        # Create services
        processor = QdrantDocumentProcessor()
        crud_service = QdrantCRUDService()
        
        # Create test document
        test_content = """
        Integration Test Document
        This document tests the complete CRUD workflow.
        It includes search terms like procurement and contract.
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        doc_id = f"integration_test_{uuid.uuid4().hex[:8]}"
        
        try:
            # 1. Upload document
            result = processor.process_document(
                test_file,
                {
                    "document_id": doc_id,
                    "document_type": "test",
                    "organization": "integration_test"
                }
            )
            assert result["status"] == "success"
            
            # 2. Search for document
            search_results, total = crud_service.search_documents(
                "CRUD workflow",
                filters={"organization": "integration_test"}
            )
            assert total > 0
            
            # 3. Update metadata
            update_result = crud_service.update_document_metadata(
                doc_id,
                {"document_type": "updated_test", "tags": ["integration"]}
            )
            assert update_result is True
            
            # 4. Delete document
            delete_result = crud_service.delete_document(doc_id)
            assert delete_result is True
            
            # 5. Verify deletion
            search_after_delete, total_after = crud_service.search_documents(
                "CRUD workflow",
                filters={"document_id": doc_id}
            )
            assert total_after == 0
            
        finally:
            # Clean up
            os.unlink(test_file)
            # Ensure document is deleted even if test fails
            try:
                crud_service.delete_document(doc_id)
            except:
                pass
    
    @pytest.mark.performance
    def test_search_performance(self):
        """Test search performance with multiple queries."""
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            pytest.skip("Integration tests not enabled")
        
        crud_service = QdrantCRUDService()
        
        import time
        queries = [
            "procurement specifications",
            "contract terms",
            "technical requirements",
            "budget allocation",
            "delivery timeline"
        ]
        
        times = []
        for query in queries:
            start = time.time()
            results, total = crud_service.search_documents(query, limit=10)
            elapsed = time.time() - start
            times.append(elapsed)
        
        # Average search time should be under 2 seconds
        avg_time = sum(times) / len(times)
        assert avg_time < 2.0, f"Search too slow: {avg_time:.2f}s average"


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])