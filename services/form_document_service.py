"""
Form Document Service with Deduplication and Versioning
Handles document storage, deduplication, versioning, and associations
Part of Epic: EPIC-FORM-DOCS-001
"""

import os
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Dict, List, BinaryIO, Tuple
import sqlite3
from datetime import datetime
import json
import logging

logger = logging.getLogger(__name__)


class FormDocumentService:
    """Service layer for form document operations with deduplication and versioning"""
    
    def __init__(self, db_path: str = 'mainDB.db'):
        self.db_path = db_path
        self.storage_root = Path("data/form_documents")
        self.storage_root.mkdir(parents=True, exist_ok=True)
        self.temp_dir = self.storage_root / "temp"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Configuration
        self.max_file_size = 10 * 1024 * 1024  # 10MB
        self.allowed_extensions = {'.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx'}
        self.chunk_size = 8192  # For file hashing
    
    def save_document(self, 
                     file_data: BinaryIO,
                     form_id: int,
                     form_type: str,
                     field_name: str,
                     original_name: str,
                     mime_type: str,
                     organization_id: Optional[int] = None,
                     user: Optional[str] = None) -> Tuple[int, bool, str]:
        """
        Save a document with deduplication and versioning.
        
        Returns:
            Tuple of (document_id, is_new_file, status_message)
            - document_id: ID of the document record
            - is_new_file: True if file was newly stored, False if deduplicated
            - status_message: Human-readable status
        """
        
        # Validate file
        validation_error = self._validate_file(file_data, original_name)
        if validation_error:
            raise ValueError(f"File validation failed: {validation_error}")
        
        # Generate file hash for deduplication
        file_hash = self._generate_file_hash(file_data)
        file_size = file_data.tell()
        file_data.seek(0)  # Reset for reading
        
        # Check for existing document with same hash
        existing_doc = self._find_existing_document(file_hash)
        
        if existing_doc:
            # Document exists - check if it's already linked to this form
            existing_association = self._check_existing_association(
                existing_doc['id'], form_id, form_type, field_name
            )
            
            if existing_association:
                # Already linked - this might be a replacement scenario
                doc_id = self._handle_document_replacement(
                    existing_doc, file_data, form_id, form_type, 
                    field_name, original_name, mime_type, 
                    file_size, organization_id, user
                )
                return doc_id, False, "Document replaced with new version"
            else:
                # Create new association to existing file
                self._create_document_association(
                    existing_doc['id'], form_id, form_type, 
                    field_name, organization_id, user
                )
                return existing_doc['id'], False, "Existing document linked to form"
        
        # New document - store file and create metadata
        file_path = self._store_new_file(file_data, file_hash, original_name)
        
        # Create document record
        doc_id = self._create_document_record(
            file_hash=file_hash,
            original_name=original_name,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=mime_type,
            file_type=Path(original_name).suffix.lower()
        )
        
        # Create association
        self._create_document_association(
            doc_id, form_id, form_type, field_name, organization_id, user
        )
        
        # Create initial version record
        self._create_version_record(
            doc_id, 1, file_hash, str(file_path), 
            file_size, original_name, 'create', 
            'Initial upload', user
        )
        
        # Log the operation
        self._log_document_operation(doc_id, 'upload', user, 
                                    f"New document uploaded: {original_name}")
        
        return doc_id, True, "New document uploaded successfully"
    
    def _validate_file(self, file_data: BinaryIO, filename: str) -> Optional[str]:
        """Validate file type and size. Returns error message if invalid."""
        
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in self.allowed_extensions:
            return f"File type {ext} not allowed. Allowed types: {', '.join(self.allowed_extensions)}"
        
        # Check size
        file_data.seek(0, 2)  # Seek to end
        size = file_data.tell()
        file_data.seek(0)  # Reset
        
        if size == 0:
            return "File is empty"
        
        if size > self.max_file_size:
            return f"File too large ({size / 1024 / 1024:.1f}MB). Maximum: {self.max_file_size / 1024 / 1024}MB"
        
        # TODO: Add virus scan here if available
        
        return None
    
    def _generate_file_hash(self, file_data: BinaryIO) -> str:
        """Generate SHA-256 hash of file content for deduplication"""
        sha256_hash = hashlib.sha256()
        file_data.seek(0)
        
        # Read file in chunks to handle large files efficiently
        while chunk := file_data.read(self.chunk_size):
            sha256_hash.update(chunk)
        
        file_data.seek(0)  # Reset position
        return sha256_hash.hexdigest()
    
    def _find_existing_document(self, file_hash: str) -> Optional[Dict]:
        """Find active document by hash"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM form_documents 
                WHERE file_hash = ? 
                AND is_active = 1 
                AND processing_status != 'failed'
                LIMIT 1
            """, (file_hash,))
            
            result = cursor.fetchone()
            if result:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, result))
        return None
    
    def _check_existing_association(self, doc_id: int, form_id: int, 
                                   form_type: str, field_name: str) -> bool:
        """Check if document is already associated with this form/field"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT COUNT(*) FROM form_document_associations
                WHERE form_document_id = ? 
                AND form_id = ? 
                AND form_type = ?
                AND field_name = ?
            """, (doc_id, form_id, form_type, field_name))
            
            return cursor.fetchone()[0] > 0
    
    def _handle_document_replacement(self, existing_doc: Dict, file_data: BinaryIO,
                                    form_id: int, form_type: str, field_name: str,
                                    original_name: str, mime_type: str, file_size: int,
                                    organization_id: Optional[int], user: Optional[str]) -> int:
        """Handle replacement of existing document with new version"""
        
        # Generate new hash for the replacement file
        new_hash = self._generate_file_hash(file_data)
        
        # If hash is same, no need to replace
        if new_hash == existing_doc['file_hash']:
            return existing_doc['id']
        
        # Store new file
        file_path = self._store_new_file(file_data, new_hash, original_name)
        
        # Create new document record
        new_doc_id = self._create_document_record(
            file_hash=new_hash,
            original_name=original_name,
            file_path=str(file_path),
            file_size=file_size,
            mime_type=mime_type,
            file_type=Path(original_name).suffix.lower(),
            version=existing_doc['version'] + 1
        )
        
        # Mark old document as superseded
        self._supersede_document(existing_doc['id'], new_doc_id)
        
        # Copy associations to new document
        self._copy_associations(existing_doc['id'], new_doc_id)
        
        # Create version record
        self._create_version_record(
            new_doc_id, existing_doc['version'] + 1, new_hash, 
            str(file_path), file_size, original_name, 
            'replace', f"Replaced version {existing_doc['version']}", user
        )
        
        # Log the operation
        self._log_document_operation(new_doc_id, 'replace', user,
                                    f"Replaced document version {existing_doc['version']}")
        
        return new_doc_id
    
    def _store_new_file(self, file_data: BinaryIO, file_hash: str, 
                       original_name: str) -> Path:
        """Store file in hash-based directory structure"""
        
        # Use first 2 chars and next 2 chars of hash for directory structure
        # This prevents too many files in a single directory
        hash_dir = Path(file_hash[:2]) / file_hash[2:4]
        storage_path = self.storage_root / hash_dir
        storage_path.mkdir(parents=True, exist_ok=True)
        
        # Generate filename with hash and original extension
        file_ext = Path(original_name).suffix.lower()
        stored_filename = f"{file_hash}{file_ext}"
        file_path = storage_path / stored_filename
        
        # Save file
        with open(file_path, 'wb') as f:
            file_data.seek(0)
            shutil.copyfileobj(file_data, f)
        
        return file_path
    
    def _create_document_record(self, **kwargs) -> int:
        """Create new document record in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Set defaults
            kwargs.setdefault('version', 1)
            kwargs.setdefault('is_active', 1)
            kwargs.setdefault('processing_status', 'pending')
            
            cursor.execute("""
                INSERT INTO form_documents (
                    file_hash, original_name, file_path, file_size, 
                    mime_type, file_type, version, is_active, 
                    processing_status, upload_date
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            """, (
                kwargs['file_hash'], kwargs['original_name'], 
                kwargs['file_path'], kwargs['file_size'],
                kwargs.get('mime_type'), kwargs['file_type'],
                kwargs['version'], kwargs['is_active'],
                kwargs['processing_status']
            ))
            
            conn.commit()
            return cursor.lastrowid
    
    def _create_document_association(self, doc_id: int, form_id: int, 
                                    form_type: str, field_name: str,
                                    organization_id: Optional[int] = None,
                                    user: Optional[str] = None):
        """Create association between document and form"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO form_document_associations (
                    form_document_id, form_id, form_type, field_name,
                    organization_id, created_by
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (doc_id, form_id, form_type, field_name, organization_id, user))
            
            conn.commit()
    
    def _supersede_document(self, old_doc_id: int, new_doc_id: int):
        """Mark old document as superseded by new one"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                UPDATE form_documents 
                SET is_active = 0, 
                    superseded_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (new_doc_id, old_doc_id))
            
            conn.commit()
    
    def _copy_associations(self, old_doc_id: int, new_doc_id: int):
        """Copy all associations from old document to new one"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get existing associations
            cursor.execute("""
                SELECT form_id, form_type, field_name, organization_id, created_by
                FROM form_document_associations
                WHERE form_document_id = ?
            """, (old_doc_id,))
            
            associations = cursor.fetchall()
            
            # Create new associations
            for assoc in associations:
                cursor.execute("""
                    INSERT OR IGNORE INTO form_document_associations (
                        form_document_id, form_id, form_type, field_name,
                        organization_id, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (new_doc_id, *assoc))
            
            conn.commit()
    
    def _create_version_record(self, doc_id: int, version: int, file_hash: str,
                              file_path: str, file_size: int, original_name: str,
                              change_type: str, change_reason: str, user: Optional[str]):
        """Create version history record"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO form_document_versions (
                    document_id, version_number, file_hash, file_path,
                    file_size, original_name, change_type, change_reason,
                    changed_by
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (doc_id, version, file_hash, file_path, file_size,
                  original_name, change_type, change_reason, user))
            
            conn.commit()
    
    def _log_document_operation(self, doc_id: int, action: str, 
                               user: Optional[str], details: str):
        """Log document operation for audit trail"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO form_document_audit_log (
                    form_document_id, action, user_id, details
                ) VALUES (?, ?, ?, ?)
            """, (doc_id, action, user, details))
            
            conn.commit()
    
    def get_document(self, doc_id: int) -> Optional[Dict]:
        """Get document with all its associations"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get document
            cursor.execute("""
                SELECT * FROM form_documents WHERE id = ? AND is_active = 1
            """, (doc_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            columns = [desc[0] for desc in cursor.description]
            document = dict(zip(columns, result))
            
            # Get associations
            cursor.execute("""
                SELECT form_id, form_type, field_name, organization_id
                FROM form_document_associations
                WHERE form_document_id = ?
            """, (doc_id,))
            
            document['associations'] = [
                dict(zip(['form_id', 'form_type', 'field_name', 'organization_id'], row))
                for row in cursor.fetchall()
            ]
            
            # Get version history
            cursor.execute("""
                SELECT version_number, change_type, change_reason, changed_by, changed_at
                FROM form_document_versions
                WHERE document_id = ?
                ORDER BY version_number DESC
            """, (doc_id,))
            
            document['versions'] = [
                dict(zip(['version', 'change_type', 'reason', 'user', 'date'], row))
                for row in cursor.fetchall()
            ]
            
            return document
    
    def get_documents_for_form(self, form_id: int, form_type: str = 'draft',
                              field_name: Optional[str] = None) -> List[Dict]:
        """Get all documents associated with a form"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = """
                SELECT DISTINCT d.*, a.field_name
                FROM form_documents d
                JOIN form_document_associations a ON d.id = a.form_document_id
                WHERE a.form_id = ? AND a.form_type = ? AND d.is_active = 1
            """
            params = [form_id, form_type]
            
            if field_name:
                query += " AND a.field_name = ?"
                params.append(field_name)
            
            cursor.execute(query, params)
            
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row)) for row in cursor.fetchall()]
    
    def delete_document(self, doc_id: int, user: Optional[str] = None) -> bool:
        """
        Soft delete a document (mark as inactive).
        Physical deletion only if no associations exist.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check associations
                cursor.execute("""
                    SELECT COUNT(*) FROM form_document_associations
                    WHERE form_document_id = ?
                """, (doc_id,))
                
                association_count = cursor.fetchone()[0]
                
                if association_count > 1:
                    # Has multiple associations - just soft delete
                    cursor.execute("""
                        UPDATE form_documents 
                        SET is_active = 0, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                    """, (doc_id,))
                    
                    # Log within same connection
                    cursor.execute("""
                        INSERT INTO form_document_audit_log 
                        (form_document_id, action, user_id, details)
                        VALUES (?, ?, ?, ?)
                    """, (doc_id, 'delete', user, 
                          "Soft delete - document has multiple associations"))
                else:
                    # Get document info before deletion
                    cursor.execute("SELECT file_path FROM form_documents WHERE id = ?", (doc_id,))
                    result = cursor.fetchone()
                    
                    if result:
                        file_path = result[0]
                        # Delete from database first
                        cursor.execute("DELETE FROM form_documents WHERE id = ?", (doc_id,))
                        
                        # Then delete physical file
                        if file_path and os.path.exists(file_path):
                            try:
                                os.remove(file_path)
                            except Exception as e:
                                logger.error(f"Failed to delete file {file_path}: {e}")
                
                conn.commit()
                return True
        except Exception as e:
            logger.error(f"Error deleting document {doc_id}: {e}")
            return False
    
    def cleanup_orphaned_files(self) -> int:
        """Remove files not referenced in database"""
        orphaned_count = 0
        
        # Get all file paths from database
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT file_path FROM form_documents WHERE is_active = 1")
            db_files = {row[0] for row in cursor.fetchall()}
        
        # Check all files in storage
        for file_path in self.storage_root.rglob('*'):
            if file_path.is_file() and str(file_path) not in db_files:
                # Skip temp directory
                if 'temp' in file_path.parts:
                    continue
                    
                try:
                    os.remove(file_path)
                    orphaned_count += 1
                    logger.info(f"Removed orphaned file: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove orphaned file {file_path}: {e}")
        
        return orphaned_count
    
    def get_document_statistics(self) -> Dict:
        """Get statistics about document storage and deduplication"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            stats = {}
            
            # Total documents
            cursor.execute("SELECT COUNT(*) FROM form_documents WHERE is_active = 1")
            stats['total_documents'] = cursor.fetchone()[0]
            
            # Total unique files (by hash)
            cursor.execute("SELECT COUNT(DISTINCT file_hash) FROM form_documents WHERE is_active = 1")
            stats['unique_files'] = cursor.fetchone()[0]
            
            # Deduplication ratio
            if stats['total_documents'] > 0:
                stats['deduplication_ratio'] = 1 - (stats['unique_files'] / stats['total_documents'])
            else:
                stats['deduplication_ratio'] = 0
            
            # Storage saved through deduplication
            cursor.execute("""
                SELECT SUM(file_size * (association_count - 1)) as saved_bytes
                FROM (
                    SELECT d.file_hash, d.file_size, COUNT(a.id) as association_count
                    FROM form_documents d
                    JOIN form_document_associations a ON d.id = a.form_document_id
                    WHERE d.is_active = 1
                    GROUP BY d.file_hash
                    HAVING association_count > 1
                )
            """)
            
            saved_bytes = cursor.fetchone()[0] or 0
            stats['storage_saved_mb'] = saved_bytes / (1024 * 1024)
            
            # Processing status breakdown
            cursor.execute("""
                SELECT processing_status, COUNT(*) 
                FROM form_documents 
                WHERE is_active = 1
                GROUP BY processing_status
            """)
            
            stats['processing_status'] = dict(cursor.fetchall())
            
            # Documents by type
            cursor.execute("""
                SELECT file_type, COUNT(*) 
                FROM form_documents 
                WHERE is_active = 1
                GROUP BY file_type
            """)
            
            stats['by_type'] = dict(cursor.fetchall())
            
            return stats