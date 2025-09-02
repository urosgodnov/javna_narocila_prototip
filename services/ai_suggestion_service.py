"""
AI Suggestion Service with Knowledge Base Integration
Implements brownfield story for AI suggestion transfer with full form context
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
import streamlit as st
from datetime import datetime

# Import existing services
from services.qdrant_crud_service import QdrantCRUDService
from services.ai_response_service import AIResponseService

logger = logging.getLogger(__name__)


class AIFieldSuggestionService:
    """
    Service for generating AI suggestions with full form context.
    First queries Qdrant knowledge base, then falls back to general AI.
    """
    
    def __init__(self):
        """Initialize with Qdrant and AI response services."""
        self.qdrant_service = QdrantCRUDService()
        self.ai_response_service = AIResponseService()
        
    def get_field_suggestion(
        self, 
        field_context: str, 
        field_type: str,
        query: str,
        form_data: Dict = None
    ) -> Dict[str, Any]:
        """
        Collects full form context before generating suggestions.
        
        Args:
            field_context: Current field being filled (e.g., 'negotiations.special_requests')
            field_type: Type of field (e.g., 'negotiation_terms', 'cofinancer_requirements')
            query: User's specific query or field prompt
            form_data: Complete form state from session
            
        Returns:
            Dictionary with suggestions, source, confidence, and context used
        """
        logger.info(f"Getting AI suggestions for field: {field_context}, type: {field_type}")
        
        # Collect complete form context
        full_context = self._collect_form_context(form_data or {})
        logger.debug(f"Collected context keys: {list(full_context.keys())[:10]}")
        
        # Build intelligent search query using full context
        search_query = self._build_contextual_query(field_context, field_type, full_context)
        
        # Log what context we're using
        logger.info(f"Generating suggestions for {field_context} with context: {search_query[:200]}...")
        
        # First, try Qdrant knowledge base
        kb_results = self._search_knowledge_base(search_query, full_context)
        
        if kb_results and self._has_good_results(kb_results):
            # Format and return knowledge base suggestions
            return self._format_kb_suggestions(kb_results, full_context)
        
        # Fall back to general AI with full context
        return self._generate_ai_suggestions_with_context(
            field_context, 
            field_type, 
            full_context,
            query
        )
    
    def _collect_form_context(self, form_data: Dict) -> Dict[str, Any]:
        """
        Extract relevant context from all filled form fields.
        Reads project info, cofinancers, lots, and all relevant fields.
        """
        # Start with session state data if available
        if hasattr(st, 'session_state'):
            session_data = dict(st.session_state)
        else:
            session_data = form_data
        
        context = {
            # Project basics
            'project_title': session_data.get('projectInfo.title', ''),
            'project_description': session_data.get('projectInfo.description', ''),
            
            # Cofinancing info
            'cofinancers': [],
            'funding_programs': [],
            'has_cofinancing': session_data.get('projectInfo.hasCofinancing', False),
            
            # Current lot info
            'current_lot': {
                'name': session_data.get('current_lot_name', ''),
                'index': session_data.get('current_lot_index', 0),
                'type': ''
            },
            
            # Procurement details
            'procurement_type': session_data.get('procurementType.type', ''),
            'estimated_value': session_data.get('projectInfo.estimatedValue', 0),
            'submission_deadline': session_data.get('submissionProcedure.deadline', ''),
            
            # Technical specifications if available
            'technical_specs': session_data.get('technicalSpecifications.description', ''),
            
            # Evaluation criteria
            'criteria': {
                'price_weight': session_data.get('evaluationCriteria.priceWeight', 0),
                'quality_weight': session_data.get('evaluationCriteria.qualityWeight', 0),
                'has_social': session_data.get('evaluationCriteria.hasSocial', False),
                'has_environmental': session_data.get('evaluationCriteria.hasEnvironmental', False)
            }
        }
        
        # Extract cofinancer information
        if context['has_cofinancing']:
            # Look for cofinancer fields in session state
            for key in session_data:
                if 'cofinancer' in key.lower():
                    if isinstance(session_data[key], list):
                        context['cofinancers'].extend(session_data[key])
                    elif isinstance(session_data[key], str) and session_data[key]:
                        context['cofinancers'].append(session_data[key])
                
                if 'program' in key.lower() and 'funding' in key.lower():
                    if isinstance(session_data[key], str) and session_data[key]:
                        context['funding_programs'].append(session_data[key])
        
        # Get lot information
        lots = session_data.get('lots', [])
        if lots and len(lots) > context['current_lot']['index']:
            current_lot = lots[context['current_lot']['index']]
            context['current_lot']['name'] = current_lot.get('name', f"Sklop {context['current_lot']['index'] + 1}")
            context['current_lot']['type'] = current_lot.get('type', '')
        
        return context
    
    def _build_contextual_query(self, field_context: str, field_type: str, full_context: Dict) -> str:
        """
        Build search query enriched with form context.
        Creates intelligent queries based on field type and project context.
        """
        query_parts = []
        
        # Handle specific field types with context
        if 'cofinancer' in field_type.lower() or 'cofinancer' in field_context.lower():
            # Cofinancer requirements - highest priority
            query_parts.append("posebne zahteve sofinancerja")
            if full_context['cofinancers']:
                query_parts.append(' '.join(full_context['cofinancers']))
            if full_context['funding_programs']:
                query_parts.append(' '.join(full_context['funding_programs']))
            query_parts.append(full_context.get('procurement_type', ''))
            
        elif 'negotiation' in field_type.lower() or 'pogajanja' in field_context.lower():
            # Negotiations field
            query_parts.append("pogajanja")
            query_parts.append(full_context.get('project_title', ''))
            query_parts.append(full_context.get('procurement_type', ''))
            if full_context['cofinancers']:
                query_parts.append(f"sofinancer {', '.join(full_context['cofinancers'])}")
            if full_context.get('current_lot', {}).get('name'):
                query_parts.append(f"sklop {full_context['current_lot']['name']}")
                
        elif 'price' in field_type.lower() or 'cen' in field_context.lower():
            # Price information
            query_parts.append("oblikovanje cen valorizacija")
            query_parts.append(full_context.get('procurement_type', ''))
            value = full_context.get('estimated_value', 0)
            if value:
                query_parts.append(f"vrednost {value}")
                
        elif 'criteria' in field_type.lower() or 'merila' in field_context.lower():
            # Evaluation criteria
            query_parts.append("merila ocenjevanja")
            if full_context['criteria']['has_social']:
                query_parts.append("socialni vidiki")
            if full_context['criteria']['has_environmental']:
                query_parts.append("okoljski vidiki")
            query_parts.append(full_context.get('procurement_type', ''))
            
        else:
            # Generic query building
            query_parts.append(field_type)
            query_parts.append(full_context.get('project_title', ''))
            query_parts.append(full_context.get('procurement_type', ''))
        
        # Filter out empty parts and join
        query = ' '.join(filter(None, query_parts))
        
        # Limit query length for efficiency
        if len(query) > 500:
            query = query[:500]
        
        return query
    
    def _search_knowledge_base(self, query: str, context: Dict) -> List[Dict]:
        """
        Search Qdrant knowledge base with context-aware filters.
        """
        try:
            # Try multiple searches with different document types
            all_results = []
            
            # Search relevant document types
            for doc_type in ['pogodbe', 'razpisi', 'navodila']:
                filters = {
                    'document_type': doc_type
                }
                
                # Add cofinancing filter if applicable
                if context.get('cofinancers'):
                    filters['has_cofinancing'] = True
                
                # Add procurement type filter if available
                if context.get('procurement_type'):
                    filters['procurement_type'] = context['procurement_type']
                
                # Search with filters
                try:
                    results, total = self.qdrant_service.search_documents(
                        query=query,
                        filters=filters,
                        limit=2  # Get top 2 from each type
                    )
                    all_results.extend(results)
                except Exception as e:
                    logger.debug(f"Search failed for {doc_type}: {e}")
                    continue
            
            # Sort by relevance score if available
            all_results.sort(key=lambda x: x.get('score', 0), reverse=True)
            
            # Return top 5 results
            results = all_results[:5]
            
            logger.info(f"Found {len(results)} results in knowledge base for query: {query[:100]}...")
            
            return results
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            return []
    
    def _has_good_results(self, results: List[Dict]) -> bool:
        """
        Check if knowledge base results are good enough to use.
        """
        if not results:
            return False
        
        # Check if we have at least 2 results
        if len(results) < 2:
            return False
        
        # Check if top results have good similarity scores
        # Assuming results have a 'score' field from Qdrant
        if results[0].get('score', 0) < 0.7:  # Threshold for good match
            return False
        
        return True
    
    def _format_kb_suggestions(self, kb_results: List[Dict], context: Dict) -> Dict[str, Any]:
        """
        Format knowledge base results into suggestions.
        """
        suggestions = []
        
        for idx, result in enumerate(kb_results[:3]):  # Top 3 results
            # Extract text from result
            text = result.get('chunk_text', result.get('text', ''))
            
            # Clean and format text
            if len(text) > 500:
                text = text[:500] + "..."
            
            suggestion = {
                'text': text,
                'source': 'knowledge_base',
                'confidence': result.get('score', 0.5),
                'metadata': {
                    'document_id': result.get('document_id'),
                    'document_type': result.get('document_type'),
                    'chunk_index': result.get('chunk_index')
                }
            }
            
            suggestions.append(suggestion)
        
        return {
            'suggestions': suggestions,
            'source': 'knowledge_base',
            'context_used': {
                'project': context.get('project_title'),
                'cofinancers': context.get('cofinancers'),
                'lot': context.get('current_lot', {}).get('name')
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _generate_ai_suggestions_with_context(
        self, 
        field_context: str,
        field_type: str,
        full_context: Dict,
        query: str
    ) -> Dict[str, Any]:
        """
        Generate AI suggestions using complete form context.
        Falls back to this when knowledge base doesn't have good results.
        """
        # Build comprehensive prompt with all context
        prompt = self._build_contextual_prompt(field_context, field_type, full_context, query)
        
        # Generate suggestions using AI
        suggestions = []
        
        try:
            # Generate 2-3 different suggestions
            for i in range(2):
                # Vary the prompt slightly for diversity
                variation = "Predlagaj alternativo: " if i > 0 else ""
                
                # Use the new get_ai_response method for pure AI generation
                ai_response = self.ai_response_service.get_ai_response(
                    query=variation + prompt,
                    field_type=field_type
                )
                
                if ai_response and not ai_response.startswith("❌"):
                    suggestion = {
                        'text': ai_response,
                        'source': 'ai_generated',
                        'confidence': 0.7 - (i * 0.1),  # Slightly lower confidence for alternatives
                        'metadata': {
                            'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                            'context_fields': list(full_context.keys())
                        }
                    }
                    suggestions.append(suggestion)
        
        except Exception as e:
            logger.error(f"Error generating AI suggestions: {e}")
            # Provide a fallback suggestion
            suggestions.append({
                'text': self._get_fallback_suggestion(field_type),
                'source': 'fallback',
                'confidence': 0.3,
                'metadata': {'error': str(e)}
            })
        
        return {
            'suggestions': suggestions,
            'source': 'ai_generated',
            'context_used': {
                'project': full_context.get('project_title'),
                'cofinancers': full_context.get('cofinancers'),
                'lot': full_context.get('current_lot', {}).get('name'),
                'procurement_type': full_context.get('procurement_type')
            },
            'timestamp': datetime.now().isoformat()
        }
    
    def _build_contextual_prompt(
        self, 
        field_context: str,
        field_type: str,
        full_context: Dict,
        query: str
    ) -> str:
        """
        Build a comprehensive prompt with all context for AI generation.
        """
        prompt_parts = [
            f"Generiraj predlog za polje '{field_context}' v javnem naročilu.",
            "",
            "Kontekst javnega naročila:",
            f"- Naslov projekta: {full_context.get('project_title', 'Ni določen')}",
            f"- Opis: {full_context.get('project_description', 'Ni opisa')[:200]}",
            f"- Tip naročila: {full_context.get('procurement_type', 'Ni določen')}",
            f"- Trenutni sklop: {full_context.get('current_lot', {}).get('name', 'Splošni')}",
            f"- Ocenjena vrednost: {full_context.get('estimated_value', 0)} EUR",
        ]
        
        # Add cofinancer context if present
        if full_context.get('cofinancers'):
            prompt_parts.append(f"- Sofinancerji: {', '.join(full_context['cofinancers'])}")
        if full_context.get('funding_programs'):
            prompt_parts.append(f"- Programi financiranja: {', '.join(full_context['funding_programs'])}")
        
        # Add field-specific guidance
        if 'cofinancer' in field_type.lower():
            prompt_parts.extend([
                "",
                "Posebne zahteve sofinancerja morajo vključevati:",
                "- Zahteve glede poročanja",
                "- Zahteve glede označevanja in obveščanja javnosti",
                "- Zahteve glede revizijske sledi",
                "- Rok hrambe dokumentacije"
            ])
        elif 'negotiation' in field_type.lower():
            prompt_parts.extend([
                "",
                "Pogajanja naj vključujejo:",
                "- Število krogov pogajanj",
                "- Vsebino posameznih krogov",
                "- Elemente, o katerih se bo pogajalo",
                "- Način izvedbe pogajanj"
            ])
        elif 'price' in field_type.lower():
            prompt_parts.extend([
                "",
                "Oblikovanje cen naj vključuje:",
                "- Obdobje fiksnih cen",
                "- Način valorizacije",
                "- Indeks za valorizacijo",
                "- Pogoje za spremembo cen"
            ])
        
        # Add the original query if provided
        if query:
            prompt_parts.extend(["", f"Specifična zahteva: {query}"])
        
        prompt_parts.extend([
            "",
            "Predlog naj bo konkreten, specifičen za ta projekt in v slovenščini."
        ])
        
        return "\n".join(prompt_parts)
    
    def _get_fallback_suggestion(self, field_type: str) -> str:
        """
        Provide fallback suggestions when AI is unavailable.
        """
        fallbacks = {
            'cofinancer_requirements': (
                "Izvajalec mora zagotoviti:\n"
                "- Ločeno knjigovodsko evidenco za projekt\n"
                "- Mesečna poročila o napredku\n"
                "- Označevanje z logotipi sofinancerja\n"
                "- Hrambo dokumentacije 10 let po zaključku"
            ),
            'negotiation_terms': (
                "Pogajanja bodo potekala v dveh krogih:\n"
                "1. krog: Tehnične specifikacije in rok izvedbe\n"
                "2. krog: Cena in plačilni pogoji\n"
                "Ponudniki bodo povabljeni pisno najmanj 3 dni pred pogajanji."
            ),
            'price_formation': (
                "Cene ostanejo fiksne prvo leto.\n"
                "Po prvem letu se valorizirajo enkrat letno glede na indeks cen "
                "življenjskih potrebščin (SURS).\n"
                "Valorizacija se izvede na podlagi pisnega zahtevka."
            )
        }
        
        # Return appropriate fallback or generic message
        for key in fallbacks:
            if key in field_type.lower():
                return fallbacks[key]
        
        return "Prosimo, vnesite zahteve glede na specifike vašega projekta."