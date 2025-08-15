"""
AI Processing Module for Document Vectorization and Form AI Integration
Implements Story 2: Vector Processing and Form AI Integration
"""

import os
import json
import sqlite3
import uuid
import asyncio
from typing import List, Dict, Optional, Tuple, Any
from datetime import datetime
from pathlib import Path
import logging

import streamlit as st
from dotenv import load_dotenv
import database

try:
    import openai
    from openai import OpenAI
except ImportError:
    st.error("OpenAI package not installed. Please install: pip install openai")
    openai = None

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        PointStruct, Distance, VectorParams, 
        Filter, FieldCondition, MatchAny
    )
except ImportError:
    st.error("Qdrant client not installed. Please install: pip install qdrant-client")
    QdrantClient = None

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Handles document chunking and processing"""
    
    def __init__(self):
        self.chunk_size = int(os.getenv('CHUNK_SIZE', 1000))
        self.chunk_overlap = int(os.getenv('CHUNK_OVERLAP', 200))
    
    def chunk_document(self, text: str, document_id: int) -> List[Dict]:
        """Split document into overlapping chunks"""
        chunks = []
        start = 0
        chunk_index = 0
        
        # Clean the text
        text = text.strip()
        
        if not text:
            return chunks
        
        while start < len(text):
            end = start + self.chunk_size
            
            # Try to break at sentence boundary
            if end < len(text):
                # Look for sentence endings
                for sep in ['. ', '.\n', '! ', '? ', '\n\n']:
                    last_sep = text.rfind(sep, start, end)
                    if last_sep != -1:
                        end = last_sep + len(sep)
                        break
            
            chunk_text = text[start:end].strip()
            
            if chunk_text:  # Only add non-empty chunks
                chunks.append({
                    'document_id': document_id,
                    'chunk_index': chunk_index,
                    'text': chunk_text,
                    'start_pos': start,
                    'end_pos': end,
                    'chunk_size': len(chunk_text)
                })
                chunk_index += 1
            
            # Move start position with overlap
            start += self.chunk_size - self.chunk_overlap
        
        return chunks
    
    def extract_text_from_file(self, file_path: str, file_type: str) -> str:
        """Extract text from various file formats"""
        text = ""
        
        try:
            if file_type in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
            
            elif file_type == '.pdf':
                # For PDF extraction, we'd need PyPDF2 or similar
                # For now, return placeholder
                text = f"[PDF content extraction not yet implemented for {file_path}]"
                logger.warning(f"PDF extraction not implemented for {file_path}")
            
            elif file_type == '.docx':
                # For DOCX extraction, we'd need python-docx
                # For now, return placeholder
                text = f"[DOCX content extraction not yet implemented for {file_path}]"
                logger.warning(f"DOCX extraction not implemented for {file_path}")
            
            else:
                logger.error(f"Unsupported file type: {file_type}")
                
        except Exception as e:
            logger.error(f"Error extracting text from {file_path}: {e}")
            text = ""
        
        return text
    
    def process_uploaded_document(self, document_id: int) -> bool:
        """Process document through embedding pipeline"""
        try:
            # Update status to processing
            self.update_status(document_id, 'processing')
            
            # Get document metadata
            doc_metadata = self.get_document_metadata(document_id)
            if not doc_metadata:
                raise ValueError(f"Document {document_id} not found")
            
            # Extract text from document
            doc_text = self.extract_text_from_file(
                doc_metadata['file_path'], 
                doc_metadata['file_type']
            )
            
            if not doc_text:
                raise ValueError("No text extracted from document")
            
            # Chunk document
            chunks = self.chunk_document(doc_text, document_id)
            
            if not chunks:
                raise ValueError("No chunks created from document")
            
            # Generate embeddings
            embedding_gen = EmbeddingGenerator()
            texts = [chunk['text'] for chunk in chunks]
            embeddings = embedding_gen.generate_embeddings(texts)
            
            if not embeddings:
                raise ValueError("Failed to generate embeddings")
            
            # Store in Qdrant
            vector_store = VectorStoreManager()
            vector_store.store_document_chunks(chunks, embeddings, document_id, doc_metadata)
            
            # Save chunks to database
            self.save_chunks_to_db(chunks)
            
            # Update status to completed
            self.update_status(document_id, 'completed', chunk_count=len(chunks))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            self.update_status(document_id, 'failed', error=str(e))
            return False
    
    def get_document_metadata(self, document_id: int) -> Optional[Dict]:
        """Get document metadata from database"""
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM ai_documents WHERE id = ?
            """, (document_id,))
            result = cursor.fetchone()
            return dict(result) if result else None
    
    def save_chunks_to_db(self, chunks: List[Dict]):
        """Save document chunks to database"""
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            for chunk in chunks:
                cursor.execute("""
                    INSERT INTO ai_document_chunks 
                    (document_id, chunk_index, chunk_text, chunk_size, vector_id)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    chunk['document_id'],
                    chunk['chunk_index'],
                    chunk['text'],
                    chunk['chunk_size'],
                    chunk.get('vector_id', '')
                ))
            conn.commit()
    
    def update_status(self, document_id: int, status: str, 
                     chunk_count: int = 0, error: str = None):
        """Update document processing status"""
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            
            if error:
                # Store error in metadata_json
                cursor.execute("""
                    UPDATE ai_documents 
                    SET processing_status = ?, metadata_json = ?
                    WHERE id = ?
                """, (status, json.dumps({'error': error}), document_id))
            else:
                cursor.execute("""
                    UPDATE ai_documents 
                    SET processing_status = ?, chunk_count = ?
                    WHERE id = ?
                """, (status, chunk_count, document_id))
            
            conn.commit()


class EmbeddingGenerator:
    """Generate embeddings using OpenAI API"""
    
    def __init__(self):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key not found in environment")
        
        self.client = OpenAI(api_key=api_key)
        self.model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Batch generate embeddings"""
        try:
            # OpenAI has a limit on batch size, so we may need to chunk
            max_batch_size = 100
            all_embeddings = []
            
            for i in range(0, len(texts), max_batch_size):
                batch = texts[i:i + max_batch_size]
                
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embeddings)
            
            return all_embeddings
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            st.error(f"OpenAI API error: {e}")
            return []
    
    def generate_single_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for a single text"""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else None


class VectorStoreManager:
    """Manage Qdrant vector operations"""
    
    def __init__(self):
        if not QdrantClient:
            raise ImportError("Qdrant client not available")
        
        try:
            self.client = QdrantClient(
                host=os.getenv('QDRANT_HOST', 'localhost'),
                port=int(os.getenv('QDRANT_PORT', 6333)),
                api_key=os.getenv('QDRANT_API_KEY') if os.getenv('QDRANT_API_KEY') != 'test-qdrant-api-key' else None
            )
            self.collection_name = os.getenv('QDRANT_COLLECTION_NAME', 'javna_narocila')
            self.ensure_collection()
        except Exception as e:
            logger.warning(f"Qdrant connection failed: {e}. Running in offline mode.")
            self.client = None
    
    def ensure_collection(self):
        """Create collection if not exists"""
        if not self.client:
            return
        
        try:
            collections = self.client.get_collections().collections
            if not any(c.name == self.collection_name for c in collections):
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(
                        size=1536,  # OpenAI embedding size
                        distance=Distance.COSINE
                    )
                )
                logger.info(f"Created Qdrant collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Error ensuring collection: {e}")
    
    def store_document_chunks(self, chunks: List[Dict], embeddings: List[List[float]], 
                            document_id: int, doc_metadata: Dict):
        """Store embeddings in Qdrant with document metadata"""
        if not self.client:
            logger.warning("Qdrant client not available, skipping vector storage")
            return
        
        try:
            points = []
            for chunk, embedding in zip(chunks, embeddings):
                point_id = str(uuid.uuid4())
                points.append(
                    PointStruct(
                        id=point_id,
                        vector=embedding,
                        payload={
                            'document_id': document_id,
                            'chunk_index': chunk['chunk_index'],
                            'text': chunk['text'],
                            'tip_dokumenta': doc_metadata.get('tip_dokumenta', 'unknown'),
                            'tags': doc_metadata.get('tags', ''),
                            'description': doc_metadata.get('description', ''),
                            'filename': doc_metadata.get('filename', '')
                        }
                    )
                )
                # Store vector_id in chunk for reference
                chunk['vector_id'] = point_id
            
            # Batch upsert
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )
            logger.info(f"Stored {len(points)} vectors for document {document_id}")
            
        except Exception as e:
            logger.error(f"Error storing vectors: {e}")
    
    def search(self, query_vector: List[float], top_k: int = 5, 
              filter_dict: Dict = None) -> List[Any]:
        """Search for similar vectors"""
        if not self.client:
            logger.warning("Qdrant client not available")
            return []
        
        try:
            # Build filter if provided
            search_filter = None
            if filter_dict and 'document_types' in filter_dict:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="tip_dokumenta",
                            match=MatchAny(any=filter_dict['document_types'])
                        )
                    ]
                )
            
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=query_vector,
                query_filter=search_filter,
                limit=top_k,
                with_payload=True,
                with_vectors=False
            )
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching vectors: {e}")
            return []


class FormAIAssistant:
    """Provide AI suggestions for form fields"""
    
    def __init__(self):
        self.embedding_gen = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            self.openai_client = OpenAI(api_key=api_key)
        else:
            self.openai_client = None
    
    def get_ai_suggestion(self, form_section: str, field_name: str, 
                         context: dict) -> str:
        """Generate AI suggestion for specific field"""
        try:
            # Get system prompt
            prompt = self.get_system_prompt(form_section, field_name)
            
            # Build context query
            query = self.build_context_query(form_section, field_name, context)
            
            # Get relevant context from knowledge base
            relevant_docs = self.search_knowledge_base(
                query, 
                top_k=3,
                document_types=self.get_relevant_doc_types(form_section)
            )
            
            # Generate suggestion
            suggestion = self.generate_suggestion(prompt, relevant_docs, context)
            
            # Log usage
            self.log_usage(form_section, field_name, suggestion)
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error generating AI suggestion: {e}")
            return f"Napaka pri generiranju predloga: {str(e)}"
    
    def get_system_prompt(self, form_section: str, field_name: str) -> str:
        """Get system prompt from database or use default"""
        with sqlite3.connect(database.DATABASE_FILE) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT prompt_text FROM ai_system_prompts 
                WHERE form_section = ? AND field_name = ? AND is_active = 1
                ORDER BY version DESC LIMIT 1
            """, (form_section, field_name))
            result = cursor.fetchone()
            
            if result:
                return result[0]
            else:
                # Use default prompt
                return self.get_default_prompt(form_section, field_name)
    
    def get_default_prompt(self, section: str, field: str) -> str:
        """Get default prompt for a field"""
        default_prompts = {
            'vrsta_narocila_posebne_zahteve_sofinancerja': """
Ti si AI asistent za javna naročila. Na podlagi konteksta dokumentov in podatkov obrazca 
generiraj ustrezne posebne zahteve sofinancerja. Zahteve morajo biti:
- Specifične in merljive
- Skladne z zakonodajo o javnih naročilih
- Relevantne za vrsto naročila
- Napisane v slovenščini
Odgovori samo s konkretnimi zahtevami, brez dodatnih pojasnil.
""",
            'pogajanja_posebne_zelje_pogajanja': """
Ti si AI asistent za javna naročila. Generiraj predloge za posebne želje v zvezi s pogajanji.
Predlogi morajo biti:
- Realistični in izvedljivi
- V skladu s postopkom pogajanj
- Usmerjeni v optimizacijo ponudb
- Napisani v slovenščini
Odgovori samo s konkretnimi predlogi.
""",
            'pogoji_sodelovanje_ustreznost_poklicna_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatne pogoje za poklicno ustreznost.
Pogoji morajo biti:
- Relevantni za predmet naročila
- Sorazmerni in nediskriminatorni
- Preverljivi z dokazili
- Napisani v slovenščini
Odgovori samo s konkretnimi pogoji.
""",
            'pogoji_sodelovanje_ekonomski_polozaj_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatne pogoje za ekonomski in finančni položaj.
Pogoji morajo biti:
- Sorazmerni z vrednostjo naročila
- Objektivno preverljivi
- V skladu z ZJN-3
- Napisani v slovenščini
Odgovori samo s konkretnimi pogoji.
""",
            'pogoji_sodelovanje_tehnicna_sposobnost_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatne pogoje za tehnično in strokovno sposobnost.
Pogoji morajo biti:
- Povezani s predmetom naročila
- Objektivno merljivi
- Razumni in dosegljivi
- Napisani v slovenščini
Odgovori samo s konkretnimi pogoji.
""",
            'variante_merila_merila_drugo': """
Ti si AI asistent za javna naročila. Generiraj dodatna merila za ocenjevanje ponudb.
Merila morajo biti:
- Povezana s predmetom naročila
- Objektivna in merljiva
- Z jasno metodologijo točkovanja
- Napisana v slovenščini
Odgovori samo s konkretnimi merili in načinom točkovanja.
"""
        }
        
        prompt_key = f"{section}_{field}"
        return default_prompts.get(prompt_key, "Generiraj ustrezen predlog za to polje na podlagi konteksta.")
    
    def build_context_query(self, form_section: str, field_name: str, 
                           context: dict) -> str:
        """Build query for context retrieval"""
        # Extract relevant information from context
        query_parts = []
        
        if form_section == 'vrsta_narocila':
            query_parts.append("posebne zahteve sofinancerja")
            if context.get('vrsta_postopka'):
                query_parts.append(context['vrsta_postopka'])
        
        elif form_section == 'pogajanja':
            query_parts.append("pogajanja postopek")
            if context.get('predmet_narocila'):
                query_parts.append(context['predmet_narocila'])
        
        elif form_section == 'pogoji_sodelovanje':
            if 'ustreznost' in field_name:
                query_parts.append("poklicna ustreznost pogoji")
            elif 'ekonomski' in field_name:
                query_parts.append("ekonomski finančni položaj")
            elif 'tehnicna' in field_name:
                query_parts.append("tehnična strokovna sposobnost")
        
        elif form_section == 'variante_merila':
            query_parts.append("merila ocenjevanje ponudb")
            if context.get('vrsta_narocila'):
                query_parts.append(context['vrsta_narocila'])
        
        return " ".join(query_parts)
    
    def get_relevant_doc_types(self, form_section: str) -> List[str]:
        """Get relevant document types for form section"""
        doc_type_mapping = {
            'vrsta_narocila': ['razpisi', 'pravilniki', 'navodila'],
            'pogajanja': ['razpisi', 'pogodbe', 'navodila'],
            'pogoji_sodelovanje': ['razpisi', 'pravilniki'],
            'variante_merila': ['razpisi', 'pravilniki', 'navodila']
        }
        return doc_type_mapping.get(form_section, ['razpisi', 'pravilniki', 'navodila'])
    
    def search_knowledge_base(self, query: str, top_k: int = 3, 
                            document_types: List[str] = None) -> List[Dict]:
        """Search for relevant document chunks with optional type filtering"""
        try:
            # Generate query embedding
            query_embedding = self.embedding_gen.generate_single_embedding(query)
            
            if not query_embedding:
                return []
            
            # Search with optional filtering
            filter_dict = {'document_types': document_types} if document_types else None
            results = self.vector_store.search(query_embedding, top_k, filter_dict)
            
            # Extract and format results
            formatted_results = []
            for hit in results:
                formatted_results.append({
                    'text': hit.payload.get('text', ''),
                    'tip_dokumenta': hit.payload.get('tip_dokumenta', 'unknown'),
                    'filename': hit.payload.get('filename', ''),
                    'score': hit.score
                })
            
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def generate_suggestion(self, prompt: str, context_docs: List[Dict], 
                          form_context: dict) -> str:
        """Generate suggestion using OpenAI"""
        if not self.openai_client:
            return "OpenAI API ni na voljo. Preverite konfiguracijo."
        
        try:
            # Prepare context from documents
            context_text = "\n\n".join([
                f"[{doc['tip_dokumenta']}] {doc['text']}" 
                for doc in context_docs
            ])
            
            messages = [
                {"role": "system", "content": prompt},
                {"role": "user", "content": f"""
Kontekst dokumentov:
{context_text}

Podatki obrazca:
{json.dumps(form_context, ensure_ascii=False, indent=2)}

Generiraj ustrezen predlog za to polje.
"""}
            ]
            
            response = self.openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
                messages=messages,
                temperature=float(os.getenv('AI_TEMPERATURE', 0.7)),
                max_tokens=int(os.getenv('AI_MAX_TOKENS', 500))
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating suggestion: {e}")
            return f"Napaka pri generiranju: {str(e)}"
    
    def log_usage(self, form_section: str, field_name: str, suggestion: str):
        """Log AI usage for analytics"""
        try:
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                
                # Get prompt ID
                cursor.execute("""
                    SELECT id FROM ai_system_prompts 
                    WHERE form_section = ? AND field_name = ? AND is_active = 1
                    ORDER BY version DESC LIMIT 1
                """, (form_section, field_name))
                result = cursor.fetchone()
                prompt_id = result[0] if result else 0
                
                # Log usage
                cursor.execute("""
                    INSERT INTO ai_prompt_usage_log 
                    (prompt_id, form_section, user_input, ai_response, tokens_used)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    prompt_id,
                    form_section,
                    field_name,
                    suggestion[:500],  # Truncate for storage
                    len(suggestion) // 4  # Rough token estimate
                ))
                
                # Update usage count
                if prompt_id:
                    cursor.execute("""
                        UPDATE ai_system_prompts 
                        SET usage_count = usage_count + 1 
                        WHERE id = ?
                    """, (prompt_id,))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging usage: {e}")


# Utility function to process documents in background
def process_document_async(document_id: int):
    """Process document asynchronously"""
    processor = DocumentProcessor()
    success = processor.process_uploaded_document(document_id)
    
    if success:
        st.success(f"✅ Dokument {document_id} uspešno procesiran")
    else:
        st.error(f"❌ Napaka pri procesiranju dokumenta {document_id}")
    
    return success