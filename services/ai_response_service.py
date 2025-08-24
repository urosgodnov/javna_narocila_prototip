"""
AI Response Service for generating intelligent responses based on document context.
Uses OpenAI to synthesize information from vector search results.
"""

import os
import logging
from typing import List, Dict, Optional, Tuple
from openai import OpenAI

# Force load environment variables
try:
    from dotenv import load_dotenv
    load_dotenv(override=True)
except ImportError:
    pass

logger = logging.getLogger(__name__)

class AIResponseService:
    """Generate AI responses based on document chunks."""
    
    def __init__(self):
        """Initialize OpenAI client."""
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not configured")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            # Get model from environment (can be updated dynamically)
            self.default_model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
            self.max_tokens = int(os.getenv("AI_MAX_TOKENS", "2000"))
            self.temperature = float(os.getenv("AI_TEMPERATURE", "0.7"))
    
    def _get_current_model(self) -> str:
        """Get the currently selected model, checking session state first."""
        # Try to get from Streamlit session state if available
        try:
            import streamlit as st
            if hasattr(st, 'session_state') and 'selected_openai_model' in st.session_state:
                return st.session_state.selected_openai_model
        except:
            pass
        
        # Fall back to environment variable (which may have been updated)
        return os.getenv("OPENAI_MODEL", self.default_model)
    
    def generate_response(
        self, 
        query: str, 
        chunks: List[Dict],
        context_mode: str = "document",
        language: str = "sl"
    ) -> str:
        """
        Generate AI response based on query and document chunks.
        
        Args:
            query: User's question or request
            chunks: List of relevant document chunks from vector search
            context_mode: Type of context ("document", "form", "organization", "all")
            language: Response language ("sl" for Slovenian, "en" for English)
            
        Returns:
            Generated response text
        """
        if not self.client:
            return "❌ OpenAI ni konfiguriran. Preverite API ključ."
        
        if not chunks:
            return "🔍 Ni najdenih relevantnih informacij za odgovor na vaše vprašanje."
        
        # Check if user is asking for summary
        is_summary_request = self._is_summary_request(query)
        
        # Build context from chunks
        context_text = self._build_context(chunks)
        
        # Create system message based on language
        if language == "sl":
            system_message = self._get_slovenian_system_message(is_summary_request, context_mode)
        else:
            system_message = self._get_english_system_message(is_summary_request, context_mode)
        
        # Build messages for OpenAI
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": f"Kontekst dokumenta:\n\n{context_text}"},
            {"role": "user", "content": query}
        ]
        
        try:
            # Get current model and settings (may have been updated)
            current_model = self._get_current_model()
            current_max_tokens = int(os.getenv("AI_MAX_TOKENS", str(self.max_tokens)))
            current_temperature = float(os.getenv("AI_TEMPERATURE", str(self.temperature)))
            
            # Generate response
            # Note: o1 models don't support temperature and max_tokens parameters
            if current_model.startswith('o1'):
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages
                )
            else:
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    max_tokens=current_max_tokens,
                    temperature=current_temperature
                )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return f"❌ Napaka pri generiranju odgovora: {str(e)}"
    
    def _is_summary_request(self, query: str) -> bool:
        """Check if query is asking for a summary."""
        summary_keywords = [
            # Slovenian
            "povzemi", "povzetek", "povzemite", "povzetka",
            "opis", "opišite", "opiši",
            "kaj vsebuje", "kaj je v", "kaj piše",
            "trenutni dokument", "ta dokument", "celoten dokument",
            # English
            "summarize", "summary", "describe", "overview",
            "what contains", "what's in", "current document"
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in summary_keywords)
    
    def _build_context(self, chunks: List[Dict]) -> str:
        """Build context text from chunks."""
        context_parts = []
        
        for i, chunk in enumerate(chunks[:5], 1):  # Use top 5 chunks
            # Get text from chunk
            text = chunk.get('chunk_text') or chunk.get('text', '')
            if not text:
                continue
                
            # Add chunk with metadata
            chunk_index = chunk.get('chunk_index', i)
            total_chunks = chunk.get('total_chunks', 0)
            
            if total_chunks:
                context_parts.append(f"[Del {chunk_index}/{total_chunks}]")
            else:
                context_parts.append(f"[Del {i}]")
            
            context_parts.append(text.strip())
            context_parts.append("")  # Empty line between chunks
        
        return "\n".join(context_parts)
    
    def _get_slovenian_system_message(self, is_summary: bool, context_mode: str) -> str:
        """Get Slovenian system message."""
        base_message = """Si AI asistent za javna naročila v Sloveniji. 
Tvoja naloga je pomagati uporabnikom z informacijami iz dokumentov javnih naročil.
Odgovarjaj v slovenščini, natančno in jedrnato."""
        
        if is_summary:
            return base_message + """
            
Uporabnik prosi za povzetek dokumenta. Pripravi strukturiran povzetek, ki vključuje:
1. Vrsto dokumenta in glavni namen
2. Ključne informacije (datumi, roki, zneski, pogoji)
3. Pomembne zahteve ali omejitve
4. Kontaktne informacije, če so na voljo

Če dokument vsebuje informacije o veljavnosti, obdobjih ali rokih, jih obvezno vključi.
Povzetek naj bo jasen in organiziran po smiselnih sklopih."""
        
        else:
            return base_message + """
            
Odgovori na uporabnikovo vprašanje na podlagi podanega konteksta.
Če informacija ni v kontekstu, to jasno povej.
Bodi natančen pri navajanju datumov, številk in drugih konkretnih podatkov.
Če je vprašanje nejasno, prosi za pojasnilo."""
    
    def _get_english_system_message(self, is_summary: bool, context_mode: str) -> str:
        """Get English system message."""
        base_message = """You are an AI assistant for public procurement in Slovenia.
Your task is to help users with information from public procurement documents.
Answer accurately and concisely."""
        
        if is_summary:
            return base_message + """
            
The user is asking for a document summary. Prepare a structured summary including:
1. Document type and main purpose
2. Key information (dates, deadlines, amounts, conditions)
3. Important requirements or limitations
4. Contact information if available

If the document contains validity periods, deadlines, or dates, always include them.
The summary should be clear and organized by logical sections."""
        
        else:
            return base_message + """
            
Answer the user's question based on the provided context.
If the information is not in the context, clearly state that.
Be precise when citing dates, numbers, and other specific data.
If the question is unclear, ask for clarification."""
    
    def generate_document_summary(
        self,
        document_id: str,
        all_chunks: List[Dict],
        language: str = "sl"
    ) -> str:
        """
        Generate a complete document summary using all chunks.
        
        Args:
            document_id: Document identifier
            all_chunks: All document chunks (not just search results)
            language: Response language
            
        Returns:
            Complete document summary
        """
        if not self.client:
            return "❌ OpenAI ni konfiguriran."
        
        if not all_chunks:
            return "📄 Dokument nima vsebine za povzetek."
        
        # Sort chunks by index
        sorted_chunks = sorted(
            all_chunks, 
            key=lambda x: x.get('chunk_index', 0)
        )
        
        # Build complete document text
        full_text = "\n\n".join([
            chunk.get('chunk_text', chunk.get('text', ''))
            for chunk in sorted_chunks
            if chunk.get('chunk_text') or chunk.get('text')
        ])
        
        # Truncate if too long (keep first 10000 chars)
        if len(full_text) > 10000:
            full_text = full_text[:10000] + "\n\n[... dokument je skrajšan ...]"
        
        # Generate summary
        if language == "sl":
            prompt = """Pripravi celovit povzetek tega dokumenta javnega naročila.
            
Povzetek naj vključuje:
1. **Tip in namen dokumenta**
2. **Ključne datume in roke** (veljavnost, oddaja ponudb, itd.)
3. **Finančne informacije** (če obstajajo)
4. **Glavne zahteve in pogoje**
5. **Postopke in korake**
6. **Kontaktne informacije**

Bodi natančen pri vseh datumih in številkah."""
        else:
            prompt = """Prepare a comprehensive summary of this public procurement document.

The summary should include:
1. **Document type and purpose**
2. **Key dates and deadlines** (validity, submission, etc.)
3. **Financial information** (if any)
4. **Main requirements and conditions**
5. **Procedures and steps**
6. **Contact information**

Be precise with all dates and numbers."""
        
        messages = [
            {"role": "system", "content": "Si strokovnjak za javna naročila. Pripravi jasen in strukturiran povzetek dokumenta."},
            {"role": "user", "content": f"Dokument:\n\n{full_text}\n\n{prompt}"}
        ]
        
        try:
            # Get current model and settings
            current_model = self._get_current_model()
            current_max_tokens = int(os.getenv("AI_MAX_TOKENS", str(self.max_tokens)))
            
            # o1 models don't support temperature and max_tokens
            if current_model.startswith('o1'):
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages
                )
            else:
                response = self.client.chat.completions.create(
                    model=current_model,
                    messages=messages,
                    max_tokens=current_max_tokens,
                    temperature=0.5  # Lower temperature for summaries
                )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"❌ Napaka pri generiranju povzetka: {str(e)}"