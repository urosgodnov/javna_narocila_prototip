"""
Enhanced AI Form Integration Module - Story 28.5
Extends AI suggestions with uploaded document context
Provides better, more specific suggestions based on form documents
"""

import os
import json
import sqlite3
import hashlib
import logging
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta
from collections import OrderedDict

# Configure logging
logger = logging.getLogger(__name__)

# Import base AI processor
try:
    from ui.ai_processor import FormAIAssistant, EmbeddingGenerator, VectorStoreManager
    import database
    AI_AVAILABLE = True
except ImportError:
    logger.warning("AI processor not available")
    AI_AVAILABLE = False

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    logger.warning("OpenAI not available")
    OPENAI_AVAILABLE = False


class DocumentContextCache:
    """LRU cache for document contexts with TTL"""
    
    def __init__(self, max_size: int = 100, ttl_minutes: int = 30):
        self.cache = OrderedDict()
        self.max_size = max_size
        self.ttl = timedelta(minutes=ttl_minutes)
        self.hit_count = 0
        self.miss_count = 0
    
    def _is_expired(self, timestamp: datetime) -> bool:
        """Check if cache entry is expired"""
        return datetime.now() - timestamp > self.ttl
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired"""
        if key in self.cache:
            value, timestamp = self.cache[key]
            
            if self._is_expired(timestamp):
                # Remove expired entry
                del self.cache[key]
                self.miss_count += 1
                return None
            
            # Move to end (most recently used)
            self.cache.move_to_end(key)
            self.hit_count += 1
            return value
        
        self.miss_count += 1
        return None
    
    def set(self, key: str, value: Any):
        """Set value in cache with current timestamp"""
        # Remove oldest if at capacity
        if len(self.cache) >= self.max_size and key not in self.cache:
            self.cache.popitem(last=False)
        
        self.cache[key] = (value, datetime.now())
        self.cache.move_to_end(key)
    
    def clear_form(self, form_id: int):
        """Clear all cache entries for a specific form"""
        keys_to_remove = [k for k in self.cache if f"_form{form_id}_" in k]
        for key in keys_to_remove:
            del self.cache[key]
    
    def get_stats(self) -> Dict:
        """Get cache statistics"""
        total = self.hit_count + self.miss_count
        hit_rate = (self.hit_count / total * 100) if total > 0 else 0
        
        return {
            'size': len(self.cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': hit_rate,
            'ttl_minutes': self.ttl.total_seconds() / 60
        }


class EnhancedFormAIAssistant(FormAIAssistant):
    """Extended AI assistant using uploaded form documents for better context"""
    
    def __init__(self):
        """Initialize enhanced assistant with caching"""
        super().__init__()
        self.context_cache = DocumentContextCache(max_size=100, ttl_minutes=30)
        self.relevance_threshold = 0.7  # Minimum relevance score for documents
    
    def get_ai_suggestion(self, form_section: str, field_name: str, 
                         context: Dict[str, Any]) -> str:
        """
        Enhanced suggestion with document context
        
        Args:
            form_section: Section of the form
            field_name: Name of the field
            context: Form context including form_id
            
        Returns:
            AI-generated suggestion enriched with document context
        """
        try:
            # Generate cache key
            cache_key = self._get_cache_key(form_section, field_name, context)
            
            # Check cache first
            cached_result = self.context_cache.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for {field_name}")
                return cached_result
            
            # Get form ID from context
            form_id = context.get('form_id')
            
            # Get base system prompt
            system_prompt = self.get_system_prompt(form_section, field_name)
            
            # Build context-aware prompt
            if form_id:
                # Get relevant documents for this form
                enhanced_prompt = self._enhance_prompt_with_documents(
                    system_prompt, form_id, form_section, field_name, context
                )
            else:
                # No form ID, use base prompt
                enhanced_prompt = system_prompt
            
            # Generate suggestion using enhanced prompt
            suggestion = self._generate_enhanced_suggestion(
                enhanced_prompt, form_section, field_name, context
            )
            
            # Cache the result
            self.context_cache.set(cache_key, suggestion)
            
            # Log usage for analytics
            self._log_enhanced_usage(form_section, field_name, form_id, suggestion)
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error in enhanced AI suggestion: {e}")
            # Fallback to base implementation
            return super().get_ai_suggestion(form_section, field_name, context)
    
    def _get_cache_key(self, form_section: str, field_name: str, 
                      context: Dict[str, Any]) -> str:
        """Generate cache key from parameters"""
        # Include relevant context in cache key
        context_str = json.dumps({
            'form_id': context.get('form_id'),
            'vrsta_postopka': context.get('vrsta_postopka'),
            'vrsta_narocila': context.get('vrsta_narocila'),
            'predmet_narocila': context.get('predmet_narocila', '')[:50]
        }, sort_keys=True)
        
        key_parts = [form_section, field_name, context_str]
        key_str = "_".join(key_parts)
        
        # Hash for consistent length
        return f"cache_{hashlib.md5(key_str.encode()).hexdigest()}"
    
    def _enhance_prompt_with_documents(self, base_prompt: str, form_id: int,
                                      form_section: str, field_name: str,
                                      context: Dict[str, Any]) -> str:
        """Enhance prompt with relevant document context"""
        
        # Get relevant documents for this form and field
        relevant_docs = self._get_relevant_form_documents(
            form_id, form_section, field_name
        )
        
        if not relevant_docs:
            logger.info(f"No relevant documents found for form {form_id}")
            return base_prompt
        
        # Build enhanced prompt with document context
        enhanced = f"{base_prompt}\n\n"
        enhanced += "=== RELEVANTNI DOKUMENTI IZ OBRAZCA ===\n\n"
        
        for i, doc in enumerate(relevant_docs[:3], 1):
            enhanced += f"{i}. {doc['filename']} (relevanca: {doc['score']:.0%}):\n"
            enhanced += f"   Vsebina: {doc['text'][:500]}"
            if len(doc['text']) > 500:
                enhanced += "..."
            enhanced += "\n\n"
        
        enhanced += "Pri pripravi predloga upoštevaj zgornje dokumente, "
        enhanced += "posebej tehnične zahteve, specifikacije in podobne primere. "
        enhanced += "Predlog naj bo specifičen za ta projekt.\n"
        
        return enhanced
    
    def _get_relevant_form_documents(self, form_id: int, form_section: str, 
                                    field_name: str) -> List[Dict]:
        """Retrieve relevant document chunks from vector store"""
        
        try:
            # Build search query based on field type
            search_query = self._build_document_search_query(form_section, field_name)
            
            # Generate embedding for search
            if not self.embedding_gen:
                return []
            
            query_embedding = self.embedding_gen.generate_single_embedding(search_query)
            if not query_embedding:
                return []
            
            # Search in vector store with form filter
            if not self.vector_store or not self.vector_store.client:
                return []
            
            # Build filter for form documents
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            
            search_filter = Filter(
                must=[
                    FieldCondition(
                        key="form_id",
                        match=MatchValue(value=form_id)
                    ),
                    FieldCondition(
                        key="tip_dokumenta",
                        match=MatchValue(value="form_upload")
                    )
                ]
            )
            
            # Search for similar documents
            results = self.vector_store.client.search(
                collection_name=self.vector_store.collection_name,
                query_vector=query_embedding,
                query_filter=search_filter,
                limit=5,
                with_payload=True,
                score_threshold=self.relevance_threshold
            )
            
            # Format results
            formatted_results = []
            for result in results:
                payload = result.payload or {}
                formatted_results.append({
                    'filename': payload.get('original_name', 'Neznana datoteka'),
                    'text': payload.get('text', ''),
                    'field_name': payload.get('field_name', ''),
                    'score': result.score,
                    'chunk_index': payload.get('chunk_index', 0)
                })
            
            # Sort by relevance score
            formatted_results.sort(key=lambda x: x['score'], reverse=True)
            
            logger.info(f"Found {len(formatted_results)} relevant documents for form {form_id}")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error retrieving form documents: {e}")
            return []
    
    def _build_document_search_query(self, form_section: str, field_name: str) -> str:
        """Build search query for document retrieval"""
        
        # Field-specific search queries in Slovenian
        FIELD_QUERIES = {
            # Vrsta naročila
            'posebne_zahteve_sofinancerja': 'sofinanciranje zahteve pogoji financiranje EU sredstva',
            
            # Pogajanja
            'posebne_zelje_pogajanja': 'pogajanja postopek optimizacija cena rok kakovost',
            
            # Pogoji sodelovanja
            'ustreznost_poklicna_drugo': 'poklicna ustreznost registracija dovoljenje certifikat kvalifikacija',
            'ekonomski_polozaj_drugo': 'finančni ekonomski bonitetna ocena prihodki kapital zavarovanje',
            'tehnicna_sposobnost_drugo': 'tehnične reference kadri oprema izkušnje projekti',
            
            # Merila
            'merila_drugo': 'merila ocenjevanje točkovanje kriteriji cena kakovost rok'
        }
        
        # Get specific query or build from field name
        base_query = FIELD_QUERIES.get(field_name, field_name.replace('_', ' '))
        
        # Add section context
        section_context = {
            'vrsta_narocila': 'vrsta naročila specifikacije',
            'pogajanja': 'pogajalski postopek',
            'pogoji_sodelovanje': 'pogoji za sodelovanje sposobnost',
            'variante_merila': 'merila za oddajo variante'
        }
        
        if form_section in section_context:
            base_query = f"{section_context[form_section]} {base_query}"
        
        return base_query
    
    def _generate_enhanced_suggestion(self, enhanced_prompt: str, 
                                     form_section: str, field_name: str,
                                     context: Dict[str, Any]) -> str:
        """Generate suggestion using enhanced prompt with document context"""
        
        if not self.openai_client:
            return "OpenAI API ni na voljo. Preverite API ključ."
        
        try:
            # Build messages for chat completion
            messages = [
                {"role": "system", "content": enhanced_prompt},
                {"role": "user", "content": self._build_user_prompt(form_section, field_name, context)}
            ]
            
            # Generate completion
            response = self.openai_client.chat.completions.create(
                model=os.getenv('OPENAI_MODEL', 'gpt-4'),
                messages=messages,
                max_tokens=500,
                temperature=0.7,
                presence_penalty=0.3,
                frequency_penalty=0.3
            )
            
            suggestion = response.choices[0].message.content.strip()
            
            return suggestion
            
        except Exception as e:
            logger.error(f"Error generating enhanced suggestion: {e}")
            return f"Napaka pri generiranju predloga: {str(e)}"
    
    def _build_user_prompt(self, form_section: str, field_name: str, 
                          context: Dict[str, Any]) -> str:
        """Build user prompt with context"""
        
        prompt_parts = [f"Generiraj vsebino za polje '{field_name}' v razdelku '{form_section}'."]
        
        # Add relevant context
        if context.get('vrsta_postopka'):
            prompt_parts.append(f"Vrsta postopka: {context['vrsta_postopka']}")
        
        if context.get('vrsta_narocila'):
            prompt_parts.append(f"Vrsta naročila: {context['vrsta_narocila']}")
        
        if context.get('predmet_narocila'):
            prompt_parts.append(f"Predmet naročila: {context['predmet_narocila'][:200]}")
        
        if context.get('ocenjena_vrednost'):
            prompt_parts.append(f"Ocenjena vrednost: {context['ocenjena_vrednost']} EUR")
        
        return "\n".join(prompt_parts)
    
    def _log_enhanced_usage(self, form_section: str, field_name: str, 
                           form_id: Optional[int], suggestion: str):
        """Log usage for analytics and improvement"""
        try:
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                
                # Create usage log table if not exists
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ai_usage_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                        form_section TEXT,
                        field_name TEXT,
                        form_id INTEGER,
                        suggestion_length INTEGER,
                        has_document_context BOOLEAN,
                        cache_stats TEXT
                    )
                """)
                
                # Log usage
                cache_stats = json.dumps(self.context_cache.get_stats())
                cursor.execute("""
                    INSERT INTO ai_usage_log 
                    (form_section, field_name, form_id, suggestion_length, 
                     has_document_context, cache_stats)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (form_section, field_name, form_id, len(suggestion), 
                      bool(form_id), cache_stats))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error logging usage: {e}")
    
    def check_form_has_documents(self, form_id: int) -> bool:
        """Check if form has processed documents available"""
        if not form_id:
            return False
        
        try:
            with sqlite3.connect(database.DATABASE_FILE) as conn:
                cursor = conn.cursor()
                
                # Check for processed documents
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM form_documents fd
                    JOIN ai_documents ad ON fd.ai_document_id = ad.id
                    WHERE fd.form_id = ? 
                    AND fd.processing_status = 'completed'
                    AND ad.chunk_count > 0
                """, (form_id,))
                
                count = cursor.fetchone()[0]
                return count > 0
                
        except Exception as e:
            logger.error(f"Error checking form documents: {e}")
            return False
    
    def clear_form_cache(self, form_id: int):
        """Clear cache for a specific form (useful after document updates)"""
        self.context_cache.clear_form(form_id)
        logger.info(f"Cleared cache for form {form_id}")
    
    def get_cache_statistics(self) -> Dict:
        """Get cache performance statistics"""
        return self.context_cache.get_stats()


# Helper function for UI integration
def render_enhanced_ai_field(form_section: str, field_name: str, **kwargs):
    """
    Render AI field with enhanced document context if available
    
    This is a drop-in replacement for render_ai_field that automatically
    uses document context when available.
    """
    from ui.ai_form_integration import render_ai_field
    
    # Check if we should use enhanced assistant
    context = kwargs.get('context', {})
    form_id = context.get('form_id')
    
    if AI_AVAILABLE and form_id:
        # Check if form has documents
        assistant = EnhancedFormAIAssistant()
        if assistant.check_form_has_documents(form_id):
            logger.info(f"Using enhanced AI with document context for form {form_id}")
            # The render_ai_field will use our enhanced assistant
            # through the get_ai_suggestion override
    
    # Use standard render (which will use our enhanced assistant if available)
    return render_ai_field(form_section, field_name, **kwargs)


# Export the enhanced assistant as the default if AI is available
if AI_AVAILABLE:
    # Override the default assistant in ai_form_integration
    import ui.ai_form_integration
    ui.ai_form_integration.FormAIAssistant = EnhancedFormAIAssistant
    logger.info("Enhanced AI assistant activated with document context support")