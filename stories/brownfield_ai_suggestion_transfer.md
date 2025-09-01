# Brownfield Story: AI Suggestion Transfer with Knowledge Base Integration

## Story ID: AI-TRANSFER-001
**Type**: Feature Enhancement  
**Priority**: High  
**Status**: To Do  
**Created**: 2025-01-09  

## Executive Summary
Implement a feature that allows users to select and transfer AI-generated suggestions directly to "drugo" (other) text fields throughout the application. The AI should first query the Qdrant knowledge base for relevant answers, and only fall back to general AI if no suitable answer is found.

## Current State Analysis

### Existing AI Integration Points
The application currently has AI suggestion capabilities in the following locations:

1. **Price Information Section** (`priceInfo`)
   - Field: `priceFixation` with option "prosim za predlog AI"
   - AI suggestion field: `aiPriceFixationSuggestion` (object type with description)
   - User input field: `aiPriceFixationCustom` (string type)
   - Current implementation: Static suggestions in JSON description

2. **AI Form Integration Module** (`ui/ai_form_integration.py`)
   - Supports fields: `posebne_zahteve_sofinancerja`, `posebne_zelje_pogajanja`, `ustreznost_poklicna_drugo`, `ekonomski_polozaj_drugo`, `tehnicna_sposobnost_drugo`, `merila_drugo`
   - Uses `FormAIAssistant` class for generation
   - Currently generates suggestions without Qdrant integration

3. **Qdrant Infrastructure** (Already Implemented)
   - `services/qdrant_crud_service.py`: Full CRUD operations
   - `services/qdrant_document_processor.py`: Document processing and embedding
   - `services/ai_response_service.py`: AI response generation
   - `utils/qdrant_init.py`: Qdrant client initialization
   - Collection name: `javna_narocila_docs`

### Current Limitations
- AI suggestions are displayed as static text or in read-only fields
- No mechanism to transfer suggestions to input fields
- AI doesn't query Qdrant knowledge base first
- No visual indication of suggestion source (knowledge base vs. general AI)

## Proposed Solution

### Architecture Overview
```
User Request → Collect Form Context → Build Smart Query → Check Qdrant Knowledge Base
                    ↓                                              ↓
            (Project title, cofinancers,                    Found? → Return KB Answer
             lot info, all filled fields)                          ↓ Not Found
                                                        Query General AI with Context
                                                                    ↓
                                                    Display with Transfer Options
                                                                    ↓
                                                    User Selects or Rejects → Transfer/Regenerate
```

### Implementation Components

#### 1. Enhanced AI Suggestion Service with Full Context
Create `services/ai_suggestion_service.py`:
```python
class AIFieldSuggestionService:
    def __init__(self):
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
            field_type: Type of field (e.g., 'negotiation_terms')
            query: User's specific query or field prompt
            form_data: Complete form state from session
            
        Returns:
        {
            'suggestions': List[str],  # Multiple suggestions
            'source': 'knowledge_base' | 'ai_generated',
            'confidence': float,
            'context_used': Dict,  # What context was used
            'metadata': Dict
        }
        """
        
    def _collect_form_context(self, form_data: Dict) -> Dict:
        """Extract relevant context from all filled form fields"""
        context = {
            # Project basics
            'project_title': form_data.get('projectInfo', {}).get('title'),
            'project_description': form_data.get('projectInfo', {}).get('description'),
            
            # Cofinancing info
            'cofinancers': [],
            'funding_programs': [],
            
            # Current lot info
            'current_lot': {
                'name': form_data.get('current_lot_name'),
                'index': form_data.get('current_lot_index'),
                'type': form_data.get('lots', [{}])[0].get('type')
            },
            
            # Already filled relevant fields
            'procurement_type': form_data.get('procurementType'),
            'estimated_value': form_data.get('estimatedValue'),
            'criteria': form_data.get('evaluationCriteria', {}),
            
            # Technical specifications if available
            'technical_specs': form_data.get('technicalSpecifications')
        }
        
        # Extract cofinancer information
        if form_data.get('hasCofinancing'):
            cofinancing = form_data.get('cofinancing', {})
            context['cofinancers'] = cofinancing.get('cofinancers', [])
            context['funding_programs'] = cofinancing.get('programs', [])
            context['special_requirements'] = cofinancing.get('specialRequirements')
        
        return context
```

#### 2. UI Component for AI Trigger and Suggestion Display

##### AI Trigger Options (depending on field type):
- **For dropdowns**: Add "prosim za predlog AI" as an option
- **For text areas**: Add checkbox "Uporabi AI za predlog" above field
- **For text inputs**: Add "AI predlog" button next to field
- **For field groups**: Add toggle switch "AI pomoč" for the section

##### Suggestion Display Components:
- Multiple suggestion display with numbered options
- Source indicator (text labels: "Iz baze znanja" or "AI generirano")
- Confidence score visualization
- "Use this" button for each suggestion
- "Generate more" option

#### 3. Field Locations to Enhance

##### High Priority (Most Used):
1. **Cofinancer Special Requirements** (ALL procurement types)
   - `vrsta_narocila.posebne_zahteve_sofinancerja` - Available for every procurement type when cofinancing is enabled
   - `vrsta_narocila.specialRequirements` - Unified field name
   - `vrsta_narocila.cofinancer_special_requirements` - Alternative name
   - `vrsta_narocila.cofinancer_program_requirements` - Program specific requirements

2. **Price Information**
   - `priceInfo.priceFixation` → `priceInfo.otherPriceFixation`
   - `priceInfo.priceFixation` → `priceInfo.aiPriceFixationCustom`

3. **Criteria Fields**
   - Social criteria with "drugo" options
   - Environmental criteria with "drugo" options
   - Technical specifications with "drugo" options

4. **Negotiation Fields**
   - `negotiations.specialRequests` with AI suggestions

##### Medium Priority:
5. **Participation Conditions**
   - Professional suitability "drugo" fields
   - Economic status "drugo" fields
   - Technical capability "drugo" fields

### Technical Implementation Details

#### Step 1: Extend AI Processor with Context Collection
```python
# ui/ai_processor.py enhancement
class FormAIAssistant:
    def get_ai_suggestion_with_kb(
        self,
        form_section: str,
        field_name: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        # 1. Collect ALL form context from session state
        full_context = self._collect_complete_form_context()
        
        # 2. Build intelligent search query using full context
        search_query = self._build_contextual_query(
            form_section, 
            field_name, 
            full_context
        )
        
        # 3. Search Qdrant knowledge base with context-aware query
        kb_results = self.search_knowledge_base(
            query=search_query,
            filters={
                'project_type': full_context.get('procurement_type'),
                'has_cofinancing': bool(full_context.get('cofinancers')),
                'lot_type': full_context.get('current_lot', {}).get('type')
            }
        )
        
        # 4. If good results found, format with context
        if self._has_good_results(kb_results):
            return self._format_kb_suggestions(kb_results, full_context)
        
        # 5. Otherwise, use general AI with FULL context
        return self._generate_ai_suggestions_with_context(
            form_section, 
            field_name, 
            full_context
        )
    
    def _build_contextual_query(self, section: str, field: str, context: Dict) -> str:
        """Build search query enriched with form context"""
        
        # Example for negotiations field
        if section == 'negotiations' and field == 'special_requests':
            query_parts = [
                f"pogajanja {context.get('project_title', '')}",
                f"tip naročila {context.get('procurement_type', '')}"
            ]
            
            # Add cofinancer context if present
            if context.get('cofinancers'):
                query_parts.append(f"sofinancer {', '.join(context['cofinancers'])}")
            
            # Add lot-specific context
            if context.get('current_lot', {}).get('name'):
                query_parts.append(f"sklop {context['current_lot']['name']}")
            
            return ' '.join(query_parts)
        
        # Default query building
        return f"{field} {context.get('project_title', '')} {context.get('procurement_type', '')}"
    
    def _generate_ai_suggestions_with_context(
        self, 
        section: str, 
        field: str, 
        full_context: Dict
    ) -> Dict[str, Any]:
        """Generate AI suggestions using complete form context"""
        
        # Build comprehensive prompt with all context
        prompt = self._build_contextual_prompt(section, field, full_context)
        
        # Include context summary in system message
        system_message = f"""
        Generiraj predlog za polje '{field}' v razdelku '{section}'.
        
        Kontekst javnega naročila:
        - Naslov projekta: {full_context.get('project_title')}
        - Tip naročila: {full_context.get('procurement_type')}
        - Trenutni sklop: {full_context.get('current_lot', {}).get('name')}
        - Sofinancerji: {', '.join(full_context.get('cofinancers', ['ni']))}
        - Ocenjena vrednost: {full_context.get('estimated_value', 'ni določena')}
        
        Upoštevaj vse navedene informacije pri generiranju predloga.
        """
        
        return self._call_openai_with_context(prompt, system_message)
```

#### Step 2: Update Field Renderer with Multiple Trigger Types
```python
# ui/renderers/field_renderer.py enhancement
def _render_field_with_ai(self, full_key: str, schema: dict, parent_key: str):
    """Render field with appropriate AI trigger based on field type"""
    
    field_type = schema.get('type', 'string')
    has_ai_option = schema.get('ai_enabled', False)
    
    # Determine AI trigger type based on field
    if field_type == 'string' and 'enum' in schema:
        # Dropdown with AI option
        options = schema['enum']
        if has_ai_option:
            options.append("prosim za predlog AI")
        selected = st.selectbox(schema['title'], options, key=full_key)
        
        if selected == "prosim za predlog AI":
            self._show_ai_suggestions(full_key, schema)
            
    elif field_type == 'string' and schema.get('format') == 'textarea':
        # Text area with checkbox
        if has_ai_option:
            use_ai = st.checkbox("Uporabi AI za predlog", key=f"{full_key}_ai_checkbox")
            if use_ai:
                self._show_ai_suggestions(full_key, schema)
        
        value = st.text_area(schema['title'], key=full_key)
        
    else:
        # Regular input with button
        col1, col2 = st.columns([5, 1]) if has_ai_option else [st.container(), None]
        
        with col1:
            value = st.text_input(schema['title'], key=full_key)
        
        if col2 and has_ai_option:
            with col2:
                if st.button("AI predlog", key=f"{full_key}_ai_btn"):
                    self._show_ai_suggestions(full_key, schema)
    
    return value

def _show_ai_suggestions(self, full_key: str, schema: dict):
    """Display AI suggestions with transfer buttons"""
    
    # Collect form context
    context = self._collect_form_context()
    
    # Get suggestions
    suggestions = self._get_ai_suggestions(full_key, schema, context)
    
    # Show context being used
    with st.expander("Kontekst za AI predloge", expanded=False):
        st.write(f"Projekt: {context.get('project_title')}")
        st.write(f"Sofinancerji: {', '.join(context.get('cofinancers', []))}")
        st.write(f"Sklop: {context.get('current_lot', {}).get('name')}")
    
    # Display each suggestion with transfer button
    for idx, suggestion in enumerate(suggestions['suggestions']):
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            # Show source label
            source_label = "Iz baze znanja" if suggestion['source'] == 'knowledge_base' else "AI generirano"
            st.markdown(f"**Predlog {idx+1} ({source_label}):**")
            st.info(suggestion['text'])
            
            # Show confidence if available
            if 'confidence' in suggestion:
                st.progress(suggestion['confidence'])
        
        with col2:
            if st.button(f"Uporabi", key=f"use_{full_key}_{idx}"):
                # Transfer to associated field
                target_field = self._get_target_field(full_key)
                st.session_state[target_field] = suggestion['text']
                st.success("Predlog prenešen")
                st.rerun()
        
        with col3:
            if st.button(f"Zavrži", key=f"reject_{full_key}_{idx}"):
                # Request new suggestion
                st.rerun()
```

#### Step 3: Qdrant Query Enhancement with Full Context
```python
# services/qdrant_crud_service.py enhancement
def search_for_field_suggestion(
    self,
    field_type: str,
    form_context: Dict,
    limit: int = 3
) -> List[Dict]:
    """Search for field-specific suggestions using full form context"""
    
    # Extract key context elements
    context_elements = [
        form_context.get('project_title', ''),
        form_context.get('procurement_type', ''),
        *form_context.get('cofinancers', []),
        form_context.get('current_lot', {}).get('name', '')
    ]
    
    # Build enhanced query with full context
    query = f"{field_type} {' '.join(filter(None, context_elements))}"
    
    # Add context-aware filters
    filters = {
        'document_type': ['pogodbe', 'razpisi'],
        'field_relevance': field_type,
    }
    
    # Add cofinancing filter if applicable
    if form_context.get('cofinancers'):
        filters['has_cofinancing'] = True
        filters['funding_source'] = form_context['cofinancers'][0] if form_context['cofinancers'] else None
    
    # Add lot type filter if available
    if form_context.get('current_lot', {}).get('type'):
        filters['lot_type'] = form_context['current_lot']['type']
    
    # Search with semantic similarity and context filters
    results, _ = self.search_documents(
        query=query,
        filters=filters,
        limit=limit
    )
    
    # Log context used for transparency
    logger.info(f"Searched with context: {query[:100]}... Filters: {filters}")
    
    return results
```

### User Experience Flow

1. **User requests AI suggestion** via one of these methods:
   - Selects "prosim za predlog AI" in dropdown (for selection fields)
   - Checks "Uporabi AI za predlog" checkbox next to text field
   - Clicks "AI predlog" button beside input field
   - Toggles AI assistance switch for the field
2. **System collects full form context**:
   - Project title and description
   - All cofinancers and funding programs
   - Current lot information
   - All previously filled fields
   - Technical specifications if available
3. **System queries with context**:
   - Builds intelligent query using collected context
   - Searches Qdrant with project-specific filters
   - Falls back to AI with full context if needed
4. **System displays AI suggestion panel** with:
   - Loading message: "Analiziram kontekst projekta..."
   - Context summary shown to user
   - Multiple suggestions (1-3)
   - Source indicators (knowledge base vs AI)
   - Preview of each suggestion
5. **User can**:
   - Click "Uporabi" to transfer suggestion to field
   - Click "Zavrži in generiraj novo" for different suggestions
   - Click "Generiraj več" for more suggestions  
   - Manually edit transferred text
   - Combine multiple suggestions
   - See what context was used for generation

### Concrete Example 1: Cofinancer Requirements (All Procurement Types)

When filling out ANY procurement type (goods, services, works, or mixed) with cofinancing enabled:

1. **Field appears when**:
   - User indicates procurement has cofinancing
   - Available for ALL procurement types (blago, storitve, gradnje, mešano)
   - Shows as "Posebne zahteve sofinancerja"

2. **Context Collection**:
   ```
   Procurement Type: "Storitve"
   Cofinancers: ["EU - Kohezijski sklad", "Ministrstvo za okolje"]
   Program: "REACT-EU"
   Project: "Digitalizacija vodnih virov"
   ```

3. **AI Generates Requirements Based on**:
   - Specific EU program rules (REACT-EU)
   - Ministry's standard requirements
   - Similar past procurements with same cofinancers
   
4. **Example Suggestions**:
   ```
   Predlog 1 (iz baze znanja - REACT-EU projekti):
   "Izvajalec mora zagotoviti sledljivost sredstev EU v računovodstvu,
   mesečno poročanje o napredku, označevanje z logotipi EU na vseh
   dokumentih, in arhiviranje dokumentacije za 10 let po zaključku."
   
   Predlog 2 (AI generiran za Ministrstvo za okolje):
   "Dodatno k EU zahtevam: okoljska presoja pred začetkom del,
   uporaba certificiranih okolju prijaznih materialov (EU Ecolabel),
   in kvartalno poročanje o okoljskih kazalnikih projekta."
   ```

### Concrete Example 2: AI Suggestions for Negotiations

When a user reaches the negotiations field and selects "prosim za predlog AI", the system will:

1. **Collect Context**:
   ```
   Project: "Nadgradnja informacijskega sistema"
   Cofinancers: ["EU - Digitalna Evropa", "Ministrstvo za digitalno preobrazbo"]
   Current Lot: "Sklop 2: Programska oprema"
   Procurement Type: "Storitve"
   Estimated Value: 250000 EUR
   Technical Specs: "Razvoj web aplikacije z React in Python backend"
   ```

2. **Build Smart Query**:
   ```
   "pogajanja Nadgradnja informacijskega sistema storitve 
    EU Digitalna Evropa Sklop 2 Programska oprema 
    web aplikacija React Python 250000"
   ```

3. **Search Knowledge Base**:
   - Finds similar IT procurement negotiations
   - Filters for EU-funded projects
   - Prioritizes software development contracts

4. **Generate Suggestions with Context**:
   ```
   Predlog 1 (iz baze znanja):
   "Pogajanja bodo potekala v dveh krogih. Prvi krog bo namenjen 
   tehničnim vprašanjem in arhitekturi rešitve. Drugi krog bo 
   namenjen ceni in roku izvedbe. Posebna pozornost bo namenjena 
   zahtevam EU glede revizijske sledi in varnosti podatkov."
   
   Predlog 2 (AI generiran na podlagi konteksta):
   "Glede na sofinanciranje EU in tehnične zahteve predlagamo 
   pogajanja o: milestone plačilih vezanih na funkcionalne module, 
   garancijskih rokih za programsko kodo (min. 24 mesecev), 
   in podpori za skalabilnost sistema do 10000 uporabnikov."
   ```

5. **User Actions**:
   - Can click "Uporabi" to use suggestion
   - Can click "Zavrži in generiraj novo" for different approach
   - Can manually combine or edit suggestions

### Visual Design
```
┌─────────────────────────────────────┐
│ AI predlog za posebne želje pogajanj│
├─────────────────────────────────────┤
│ Uporabljam kontekst:                 │
│ • Projekt: Nadgradnja inf. sistema   │
│ • Sofinancer: EU - Digitalna Evropa  │
│ • Sklop: Programska oprema           │
│ • Vrednost: 250.000 EUR              │
├─────────────────────────────────────┤
│ Predlog 1 (iz baze znanja):         │
│ ┌───────────────────────────────┐   │
│ │ Pogajanja v dveh krogih...     │   │
│ │ Tehnična vprašanja najprej...  │   │
│ └───────────────────────────────┘   │
│ [Uporabi] [Zavrži in generiraj novo] │
│                                      │
│ Predlog 2 (AI generiran):           │
│ ┌───────────────────────────────┐   │
│ │ Milestone plačila vezana na    │   │
│ │ funkcionalne module...         │   │
│ └───────────────────────────────┘   │
│ [Uporabi] [Zavrži in generiraj novo] │
│                                      │
│ [Generiraj več predlogov]            │
└─────────────────────────────────────┘
```

## Testing Strategy

### Unit Tests
1. Test context collection from various form states
2. Test Qdrant query building with full context
3. Test suggestion formatting and transfer logic
4. Test fallback from KB to general AI with context preservation
5. Test confidence scoring based on context match
6. Test handling of empty/partial form context

### Integration Tests
1. Test full flow from selection to transfer
2. Test with empty knowledge base
3. Test with rich knowledge base
4. Test error handling (Qdrant down, AI unavailable)

### User Acceptance Criteria
- [ ] AI suggestions appear within 3 seconds
- [ ] System shows what context it's using (project, cofinancers, lot)
- [ ] Source of suggestion is clearly indicated (KB vs AI)
- [ ] Transfer to field works with single click
- [ ] User can reject and regenerate suggestions
- [ ] Transferred text can be edited
- [ ] Multiple suggestions are provided when available
- [ ] Suggestions are relevant to project context
- [ ] System gracefully handles no results
- [ ] Context from all form sections is utilized

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Create `AIFieldSuggestionService`
- [ ] Integrate Qdrant search for field suggestions
- [ ] Implement fallback to general AI
- [ ] Add logging and monitoring

### Phase 2: UI Components (Week 2)
- [ ] Create suggestion display component
- [ ] Add transfer buttons
- [ ] Implement "Generate more" functionality
- [ ] Add loading states and error handling

### Phase 3: Field Integration (Week 3)
- [ ] Integrate with price information fields
- [ ] Integrate with criteria fields
- [ ] Integrate with other "drugo" fields
- [ ] Add field-specific prompt templates

### Phase 4: Knowledge Base Enhancement (Week 4)
- [ ] Tag existing documents with field relevance
- [ ] Create field-specific embeddings
- [ ] Optimize search queries
- [ ] Build suggestion quality metrics

## Success Metrics
- User adoption rate: >60% use AI suggestions when available
- Transfer rate: >40% of shown suggestions are used
- Time saved: Average 2 minutes per form
- User satisfaction: >4/5 rating for AI suggestions

## Dependencies
- Qdrant server must be running
- OpenAI API key configured
- Sufficient documents in knowledge base
- Session state management

## Risks and Mitigations
1. **Risk**: Poor quality suggestions from knowledge base
   - **Mitigation**: Implement confidence scoring and filtering

2. **Risk**: Slow response times
   - **Mitigation**: Cache frequent queries, optimize embeddings

3. **Risk**: Users confused by multiple suggestions
   - **Mitigation**: Clear UI design, user guidance

## Future Enhancements
1. Learn from user selections to improve suggestions
2. Add suggestion explanations (why this was suggested)
3. Multi-language support
4. Context-aware suggestions based on entire form state
5. Batch suggestion generation for multiple fields

## Notes
- Ensure GDPR compliance for storing user selections
- Monitor API costs for OpenAI usage
- Consider implementing suggestion caching for common queries
- Add analytics to track most useful suggestions