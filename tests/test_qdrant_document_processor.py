#!/usr/bin/env python3
"""
Unit tests for Qdrant Document Processor (Story 27.2)
Tests the complete document processing pipeline
"""

import pytest
import os
import sys
import tempfile
import json
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.qdrant_document_processor import (
    QdrantDocumentProcessor,
    get_processor_status,
    detect_document_type,
    generate_doc_id
)


class TestQdrantDocumentProcessor:
    """Test suite for Story 27.2: Document Processing Pipeline."""
    
    @pytest.fixture
    def processor(self):
        """Create a processor instance with mocked dependencies."""
        with patch('services.qdrant_document_processor.DocumentConverter'):
            with patch('services.qdrant_document_processor.OpenAI'):
                with patch('services.qdrant_document_processor.get_qdrant_client'):
                    processor = QdrantDocumentProcessor()
                    return processor
    
    @pytest.fixture
    def test_document(self):
        """Create a test document file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("This is a test document for Qdrant processing. " * 50)
            return f.name
    
    def test_processor_initialization(self):
        """Test that processor initializes with available components."""
        with patch('services.qdrant_document_processor.HAS_DOCLING', True):
            with patch('services.qdrant_document_processor.HAS_LANGCHAIN', True):
                with patch('services.qdrant_document_processor.HAS_OPENAI', True):
                    with patch.dict(os.environ, {'OPENAI_API_KEY': 'test-key'}):
                        processor = QdrantDocumentProcessor()
                        
                        # Check components are initialized
                        assert processor.embedding_model == "text-embedding-3-small"
                        assert processor.text_splitter is not None
    
    def test_text_extraction_txt_file(self, processor, test_document):
        """Test text extraction from a text file."""
        text, metadata = processor.extract_text(test_document)
        
        assert text is not None
        assert len(text) > 0
        assert "test document" in text.lower()
        assert metadata["extraction_method"] in ["direct", "docling", None]
    
    def test_text_extraction_unsupported_format(self, processor):
        """Test extraction fails gracefully for unsupported formats."""
        with tempfile.NamedTemporaryFile(suffix='.xyz', delete=False) as f:
            f.write(b"unsupported content")
            
            with pytest.raises(ValueError, match="Unsupported file format"):
                processor.extract_text(f.name)
    
    def test_text_chunking_with_langchain(self):
        """Test text chunking with LangChain splitter."""
        with patch('services.qdrant_document_processor.HAS_LANGCHAIN', True):
            from langchain.text_splitter import RecursiveCharacterTextSplitter
            
            processor = QdrantDocumentProcessor()
            processor.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=100,
                chunk_overlap=20
            )
            
            text = "This is a test. " * 100
            chunks = processor.chunk_text(text)
            
            assert len(chunks) > 1
            assert all(len(chunk) <= 120 for chunk in chunks)  # Account for overlap
    
    def test_text_chunking_fallback(self, processor):
        """Test fallback chunking when LangChain not available."""
        processor.text_splitter = None
        
        text = "This is a test. " * 100
        chunks = processor.chunk_text(text)
        
        assert len(chunks) > 0
        assert isinstance(chunks, list)
    
    def test_embedding_creation(self, processor):
        """Test embedding generation with mocked OpenAI."""
        # Mock OpenAI response
        mock_embedding = [0.1] * 1536  # Correct dimensions
        processor.openai_client = Mock()
        processor.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=mock_embedding)]
        )
        
        embedding = processor.create_embedding("test text")
        
        assert embedding is not None
        assert len(embedding) == 1536
        processor.openai_client.embeddings.create.assert_called_once()
    
    def test_embedding_creation_failure(self, processor):
        """Test embedding creation handles errors gracefully."""
        processor.openai_client = Mock()
        processor.openai_client.embeddings.create.side_effect = Exception("API Error")
        
        embedding = processor.create_embedding("test text")
        
        assert embedding is None
    
    def test_process_document_complete_pipeline(self, processor, test_document):
        """Test the complete document processing pipeline."""
        # Mock components
        processor.openai_client = Mock()
        processor.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        processor.qdrant_client = Mock()
        processor.qdrant_client.upsert.return_value = None
        
        # Process document
        metadata = {
            "document_id": "test_doc_123",
            "document_type": "test",
            "organization": "test_org"
        }
        
        result = processor.process_document(test_document, metadata)
        
        # Verify result
        assert result["status"] == "success"
        assert result["chunks_processed"] > 0
        assert result["vectors_stored"] > 0
        assert result["processing_time"] > 0
        
        # Verify Qdrant was called
        processor.qdrant_client.upsert.assert_called()
    
    def test_process_document_without_openai(self, processor, test_document):
        """Test processing fails gracefully without OpenAI."""
        processor.openai_client = None
        
        result = processor.process_document(
            test_document,
            {"document_id": "test_123"}
        )
        
        assert result["status"] == "failed"
        assert "OpenAI" in result["error"]
    
    def test_process_document_with_progress_callback(self, processor, test_document):
        """Test progress callback during processing."""
        # Mock components
        processor.openai_client = Mock()
        processor.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        processor.qdrant_client = Mock()
        
        # Track progress calls
        progress_calls = []
        def progress_callback(message, progress):
            progress_calls.append((message, progress))
        
        # Process with callback
        result = processor.process_document(
            test_document,
            {"document_id": "test_123"},
            progress_callback=progress_callback
        )
        
        # Verify progress was reported
        assert len(progress_calls) > 0
        assert any("Extracting" in call[0] for call in progress_calls)
        assert any("chunks" in call[0].lower() for call in progress_calls)
        
        # Check progress values are between 0 and 1
        for _, progress in progress_calls:
            assert 0 <= progress <= 1
    
    def test_delete_document(self, processor):
        """Test document deletion from Qdrant."""
        processor.qdrant_client = Mock()
        processor.qdrant_client.delete.return_value = None
        
        result = processor.delete_document("test_doc_123")
        
        assert result is True
        processor.qdrant_client.delete.assert_called_once()
    
    def test_search_similar(self, processor):
        """Test semantic search functionality."""
        # Mock OpenAI embedding
        processor.openai_client = Mock()
        processor.openai_client.embeddings.create.return_value = Mock(
            data=[Mock(embedding=[0.1] * 1536)]
        )
        
        # Mock Qdrant search results
        mock_result = Mock(
            score=0.95,
            payload={
                "document_id": "doc_123",
                "chunk_text": "Sample text",
                "chunk_index": 0,
                "original_filename": "test.pdf",
                "organization": "test_org",
                "document_type": "procurement"
            }
        )
        processor.qdrant_client = Mock()
        processor.qdrant_client.search.return_value = [mock_result]
        
        # Perform search
        results = processor.search_similar("test query", limit=5)
        
        assert len(results) == 1
        assert results[0]["score"] == 0.95
        assert results[0]["document_id"] == "doc_123"
        assert "Sample text" in results[0]["chunk_text"]


class TestHelperFunctions:
    """Test helper functions in the module."""
    
    def test_detect_document_type(self):
        """Test document type detection from filename."""
        from ui.vector_database_manager import detect_document_type
        
        assert detect_document_type("specification_v1.pdf") == "specification"
        assert detect_document_type("contract_2024.docx") == "contract"
        assert detect_document_type("tender_docs.html") == "tender"
        assert detect_document_type("procurement_order.txt") == "procurement"
        assert detect_document_type("annual_report.pdf") == "report"
        assert detect_document_type("random_file.doc") == "general"
    
    def test_generate_doc_id(self):
        """Test document ID generation."""
        from ui.vector_database_manager import generate_doc_id
        
        doc_id1 = generate_doc_id()
        doc_id2 = generate_doc_id()
        
        assert doc_id1.startswith("doc_")
        assert doc_id2.startswith("doc_")
        assert doc_id1 != doc_id2  # Should be unique
        assert len(doc_id1) > 4  # Has actual ID part
    
    def test_processor_status(self):
        """Test processor status check."""
        status = get_processor_status()
        
        assert isinstance(status, dict)
        assert "docling" in status
        assert "langchain" in status
        assert "openai" in status
        assert "qdrant" in status
        assert "pdf_support" in status
        assert "docx_support" in status


class TestIntegration:
    """Integration tests for the complete pipeline."""
    
    @pytest.mark.integration
    def test_end_to_end_processing(self):
        """Test complete end-to-end document processing."""
        # This test requires actual services to be available
        # Skip if not in integration test environment
        if not os.getenv("RUN_INTEGRATION_TESTS"):
            pytest.skip("Integration tests not enabled")
        
        # Create test document
        test_content = """
        Public Procurement Document
        
        This is a test procurement specification for office supplies.
        The procurement includes computers, printers, and software licenses.
        Budget allocation is set at 50,000 EUR.
        
        Technical requirements:
        - Computers must have minimum 16GB RAM
        - Printers must support network printing
        - Software must include productivity suite
        
        Delivery timeline: 30 days from contract signing
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(test_content)
            test_file = f.name
        
        try:
            # Initialize processor
            processor = QdrantDocumentProcessor()
            
            # Check if services are available
            status = get_processor_status()
            if not (status["openai"] and status["qdrant"]):
                pytest.skip("Required services not available")
            
            # Process document
            result = processor.process_document(
                test_file,
                {
                    "document_id": f"test_integration_{generate_doc_id()}",
                    "document_type": "procurement",
                    "organization": "test_org",
                    "original_filename": "test_procurement.txt"
                }
            )
            
            # Verify processing succeeded
            assert result["status"] == "success"
            assert result["chunks_processed"] > 0
            assert result["vectors_stored"] > 0
            
            # Test search on processed document
            search_results = processor.search_similar(
                "computer specifications RAM",
                limit=3
            )
            
            assert len(search_results) > 0
            assert any("RAM" in r.get("chunk_text", "") for r in search_results)
            
            # Clean up - delete test document
            processor.delete_document(result["document_id"])
            
        finally:
            # Clean up test file
            os.remove(test_file)


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])