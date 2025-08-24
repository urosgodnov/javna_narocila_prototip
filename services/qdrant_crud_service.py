"""
Qdrant CRUD Service - Story 27.3
Full CRUD operations for vector database management
Handles search, update, delete, and batch operations
"""

import os
import sys
import json
import sqlite3
import logging
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
import uuid

# Force load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

# Configure logging
logger = logging.getLogger(__name__)

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import dependencies
try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Filter, FieldCondition, MatchValue, 
        PointIdsList, PointStruct
    )
    # Try to import index params - these may not exist in all versions
    try:
        from qdrant_client.models import PayloadIndexParams, KeywordIndexParams
        HAS_INDEX_PARAMS = True
    except ImportError:
        HAS_INDEX_PARAMS = False
        logger.info("Index params not available in this qdrant-client version")
    
    HAS_QDRANT = True
    logger.info("qdrant-client loaded successfully")
except ImportError as e:
    logger.error(f"qdrant-client not available: {e}")
    HAS_QDRANT = False
    HAS_INDEX_PARAMS = False

try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    logger.warning("OpenAI not installed")
    HAS_OPENAI = False

# Local imports
from utils.qdrant_init import get_qdrant_client, COLLECTION_NAME
import database


class QdrantCRUDService:
    """
    Service for complete CRUD operations on Qdrant vector database.
    Maintains consistency between Qdrant and SQLite metadata.
    """
    
    def __init__(self):
        """Initialize the CRUD service with database connections."""
        self.qdrant_client = get_qdrant_client() if HAS_QDRANT else None
        self.openai_client = None
        
        if HAS_OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
        
        self.embedding_model = os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small")
        self.db_file = database.DATABASE_FILE
        
        # Ensure payload indexes exist for filtering
        self._ensure_indexes()
    
    def _ensure_indexes(self):
        """Ensure Qdrant has necessary indexes for filtering."""
        if not self.qdrant_client:
            return
        
        # Skip index creation if params not available in this version
        if not HAS_INDEX_PARAMS:
            logger.info("Skipping index creation - not supported in this qdrant-client version")
            return
            
        try:
            # Create indexes for common filter fields
            index_fields = {
                "document_id": "keyword",
                "document_type": "keyword", 
                "organization": "keyword",
                "file_format": "keyword",
                "created_at": "keyword"
            }
            
            for field, index_type in index_fields.items():
                try:
                    if index_type == "keyword":
                        self.qdrant_client.create_payload_index(
                            collection_name=COLLECTION_NAME,
                            field_name=field,
                            field_schema=KeywordIndexParams(
                                type="keyword",
                                is_tenant=False
                            )
                        )
                    logger.debug(f"Index created/verified for field: {field}")
                except Exception as e:
                    # Index might already exist
                    logger.debug(f"Index for {field} might already exist: {e}")
                    
        except Exception as e:
            logger.warning(f"Could not ensure indexes: {e}")
    
    def _create_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for text using OpenAI."""
        if not self.openai_client:
            logger.warning("OpenAI client not available")
            return None
        
        try:
            response = self.openai_client.embeddings.create(
                model=self.embedding_model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Failed to create embedding: {e}")
            return None
    
    def search_documents(
        self, 
        query: str, 
        filters: Optional[Dict[str, Any]] = None,
        limit: int = 10,
        offset: int = 0
    ) -> Tuple[List[Dict], int]:
        """
        Search documents using semantic similarity.
        
        Args:
            query: Search query text
            filters: Optional metadata filters
            limit: Maximum results to return
            offset: Pagination offset
            
        Returns:
            Tuple of (results list, total count)
        """
        if not self.qdrant_client or not self.openai_client:
            logger.warning("Required clients not available for search")
            return [], 0
        
        try:
            # Generate query embedding
            query_vector = self._create_embedding(query)
            if not query_vector:
                return [], 0
            
            # Build filter conditions
            qdrant_filter = None
            if filters:
                conditions = []
                for key, value in filters.items():
                    if value and value != "All":
                        conditions.append(
                            FieldCondition(
                                key=key,
                                match=MatchValue(value=value)
                            )
                        )
                
                if conditions:
                    qdrant_filter = Filter(must=conditions)
            
            # Search in Qdrant
            # Version 1.15.1 uses 'query_filter' parameter
            search_params = {
                "collection_name": COLLECTION_NAME,
                "query_vector": query_vector,
                "limit": limit,
                "offset": offset,
                "with_payload": True
            }
            
            # Add filter if provided (using query_filter for v1.15.1)
            if qdrant_filter:
                search_params["query_filter"] = qdrant_filter
            
            results = self.qdrant_client.search(**search_params)
            
            # Format results
            formatted_results = []
            for result in results:
                formatted_results.append({
                    "score": result.score,
                    "id": result.id,
                    **result.payload
                })
            
            # Get total count (approximate)
            total_count = len(formatted_results)
            if len(formatted_results) == limit:
                # There might be more results
                total_count = self._estimate_total_results(query_vector, qdrant_filter)
            
            return formatted_results, total_count
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return [], 0
    
    def _estimate_total_results(
        self, 
        query_vector: List[float], 
        filter_condition: Optional[Filter]
    ) -> int:
        """Estimate total number of search results."""
        try:
            # Do a count-only search with high limit
            results = self.qdrant_client.search(
                collection_name=COLLECTION_NAME,
                query_vector=query_vector,
                query_filter=filter_condition,  # Use query_filter for v1.15.1
                limit=1000,  # High limit for counting
                with_payload=False  # Don't need payload for counting
            )
            return len(results)
        except:
            return 0
    
    def update_document_metadata(
        self, 
        document_id: str, 
        updates: Dict[str, Any]
    ) -> bool:
        """
        Update document metadata in both Qdrant and SQLite.
        
        Args:
            document_id: Document ID to update
            updates: Dictionary of fields to update
            
        Returns:
            True if successful
        """
        conn = None
        try:
            # Start SQLite transaction
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Update SQLite metadata
            update_fields = []
            update_values = []
            
            for key, value in updates.items():
                if key in ["document_type", "organization", "tags", "status"]:
                    update_fields.append(f"{key} = ?")
                    update_values.append(value if not isinstance(value, (list, dict)) else json.dumps(value))
            
            if update_fields:
                update_values.append(document_id)
                cursor.execute(f"""
                    UPDATE ai_documents 
                    SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP
                    WHERE document_id = ?
                """, update_values)
            
            # Update Qdrant payloads if client available
            if self.qdrant_client:
                # Get all points for this document
                points = self._get_document_points(document_id)
                
                if points:
                    # Update payload for each point
                    point_ids = [p.id for p in points]
                    self.qdrant_client.set_payload(
                        collection_name=COLLECTION_NAME,
                        payload=updates,
                        points=point_ids
                    )
            
            conn.commit()
            logger.info(f"Updated metadata for document: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Update failed for {document_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def delete_document(self, document_id: str) -> bool:
        """
        Delete document from both Qdrant and SQLite.
        
        Args:
            document_id: Document ID to delete
            
        Returns:
            True if successful
        """
        conn = None
        try:
            # Delete from Qdrant first
            if self.qdrant_client:
                # Get all points for this document
                points = self._get_document_points(document_id)
                
                if points:
                    point_ids = [p.id for p in points]
                    
                    # Delete points by IDs
                    self.qdrant_client.delete(
                        collection_name=COLLECTION_NAME,
                        points_selector=PointIdsList(points=point_ids)
                    )
                    logger.info(f"Deleted {len(point_ids)} vectors from Qdrant")
            
            # Delete from SQLite
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Delete document record
            cursor.execute("DELETE FROM ai_documents WHERE document_id = ?", (document_id,))
            deleted_rows = cursor.rowcount
            
            # Delete chunk records if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ai_document_chunks'
            """)
            if cursor.fetchone():
                cursor.execute("DELETE FROM ai_document_chunks WHERE document_id = ?", (document_id,))
            
            conn.commit()
            logger.info(f"Deleted document {document_id} from database")
            return deleted_rows > 0
            
        except Exception as e:
            logger.error(f"Delete failed for {document_id}: {e}")
            if conn:
                conn.rollback()
            return False
        finally:
            if conn:
                conn.close()
    
    def _get_document_points(self, document_id: str) -> List:
        """Get all Qdrant points for a document."""
        if not self.qdrant_client:
            return []
        
        try:
            # Scroll through points with filter
            points = []
            scroll_result = self.qdrant_client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=Filter(
                    must=[
                        FieldCondition(
                            key="document_id",
                            match=MatchValue(value=document_id)
                        )
                    ]
                ),
                limit=100,
                with_payload=False,
                with_vectors=False
            )
            
            points.extend(scroll_result[0])
            
            # Continue scrolling if there are more points
            while scroll_result[1] is not None:
                scroll_result = self.qdrant_client.scroll(
                    collection_name=COLLECTION_NAME,
                    scroll_filter=Filter(
                        must=[
                            FieldCondition(
                                key="document_id",
                                match=MatchValue(value=document_id)
                            )
                        ]
                    ),
                    limit=100,
                    offset=scroll_result[1],
                    with_payload=False,
                    with_vectors=False
                )
                points.extend(scroll_result[0])
            
            return points
            
        except Exception as e:
            logger.error(f"Failed to get points for document {document_id}: {e}")
            return []
    
    def batch_delete(self, document_ids: List[str]) -> Dict[str, bool]:
        """
        Delete multiple documents.
        
        Args:
            document_ids: List of document IDs to delete
            
        Returns:
            Dictionary mapping document_id to success status
        """
        results = {}
        for doc_id in document_ids:
            results[doc_id] = self.delete_document(doc_id)
        
        successful = sum(1 for v in results.values() if v)
        logger.info(f"Batch delete: {successful}/{len(document_ids)} successful")
        
        return results
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector collection.
        
        Returns:
            Dictionary with collection statistics
        """
        stats = {
            "total_documents": 0,
            "total_chunks": 0,
            "total_vectors": 0,
            "storage_mb": 0,
            "organizations": [],
            "document_types": [],
            "latest_document": None,
            "collection_exists": False
        }
        
        # Get Qdrant stats
        if self.qdrant_client:
            try:
                collection_info = self.qdrant_client.get_collection(COLLECTION_NAME)
                stats["total_vectors"] = collection_info.vectors_count or 0
                stats["collection_exists"] = True
                
                # Estimate storage (rough calculation)
                # Each vector is 1536 floats * 4 bytes = 6KB + metadata ~2KB = 8KB per vector
                stats["storage_mb"] = (stats["total_vectors"] * 8) / 1024
                
            except Exception as e:
                logger.warning(f"Could not get Qdrant stats: {e}")
        
        # Get SQLite stats
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='ai_documents'
            """)
            
            if cursor.fetchone():
                # Total documents
                cursor.execute("SELECT COUNT(*) FROM ai_documents")
                stats["total_documents"] = cursor.fetchone()[0]
                
                # Total chunks
                cursor.execute("SELECT SUM(chunks_count) FROM ai_documents WHERE chunks_count IS NOT NULL")
                result = cursor.fetchone()
                stats["total_chunks"] = result[0] if result[0] else 0
                
                # Unique organizations
                cursor.execute("SELECT DISTINCT organization FROM ai_documents WHERE organization IS NOT NULL")
                stats["organizations"] = [row[0] for row in cursor.fetchall()]
                
                # Document types
                cursor.execute("SELECT DISTINCT document_type FROM ai_documents WHERE document_type IS NOT NULL")
                stats["document_types"] = [row[0] for row in cursor.fetchall()]
                
                # Latest document
                cursor.execute("""
                    SELECT document_id, original_filename, created_at 
                    FROM ai_documents 
                    ORDER BY created_at DESC 
                    LIMIT 1
                """)
                latest = cursor.fetchone()
                if latest:
                    stats["latest_document"] = {
                        "id": latest[0],
                        "filename": latest[1],
                        "created_at": latest[2]
                    }
                    
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
        finally:
            if conn:
                conn.close()
        
        return stats
    
    def export_metadata(self, document_ids: Optional[List[str]] = None) -> List[Dict]:
        """
        Export document metadata for backup or analysis.
        
        Args:
            document_ids: Optional list of specific documents to export
            
        Returns:
            List of document metadata dictionaries
        """
        conn = None
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            if document_ids:
                placeholders = ','.join(['?' for _ in document_ids])
                query = f"""
                    SELECT * FROM ai_documents 
                    WHERE document_id IN ({placeholders})
                """
                cursor.execute(query, document_ids)
            else:
                cursor.execute("SELECT * FROM ai_documents")
            
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            return [dict(zip(columns, row)) for row in rows]
            
        except Exception as e:
            logger.error(f"Failed to export metadata: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def reprocess_document(
        self, 
        document_id: str,
        new_settings: Optional[Dict] = None
    ) -> bool:
        """
        Reprocess a document with new settings.
        
        Args:
            document_id: Document to reprocess
            new_settings: Optional new processing settings
            
        Returns:
            True if successful
        """
        # This would integrate with QdrantDocumentProcessor
        # For now, just mark as needing reprocessing
        return self.update_document_metadata(
            document_id,
            {"status": "pending_reprocess", "reprocess_settings": json.dumps(new_settings or {})}
        )


# Utility functions
def get_crud_service() -> QdrantCRUDService:
    """Get or create CRUD service instance."""
    return QdrantCRUDService()


if __name__ == "__main__":
    # Test the service
    print("=" * 50)
    print("Qdrant CRUD Service Test")
    print("=" * 50)
    
    service = QdrantCRUDService()
    
    # Get collection stats
    stats = service.get_collection_stats()
    print(f"\nCollection Statistics:")
    print(f"  Documents: {stats['total_documents']}")
    print(f"  Chunks: {stats['total_chunks']}")
    print(f"  Vectors: {stats['total_vectors']}")
    print(f"  Storage: {stats['storage_mb']:.2f} MB")
    
    # Test search if documents exist
    if stats['total_documents'] > 0:
        print("\nTesting search...")
        results, total = service.search_documents("test", limit=3)
        print(f"  Found {total} results")
        for i, result in enumerate(results, 1):
            print(f"  {i}. Score: {result.get('score', 0):.3f} - {result.get('original_filename', 'Unknown')}")
    
    print("\n✅ CRUD Service operational")