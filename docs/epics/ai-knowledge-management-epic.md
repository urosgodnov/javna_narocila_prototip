# AI Knowledge Management System - Brownfield Enhancement Epic

## Epic Goal
Integrate a comprehensive AI-powered knowledge management system into the existing admin module, enabling non-technical users to upload, manage, and query documents through an intuitive interface powered by vector embeddings and RAG (Retrieval-Augmented Generation).

## Epic Description

### Existing System Context:
- **Current functionality:** Admin module with database management, organization management, CPV codes, and criteria management
- **Technology stack:** Python, Streamlit, SQLite, ValidationManager pattern
- **Integration points:** Admin panel tabs, existing database infrastructure, file system storage
- **UI patterns:** Gradient-styled components, tab-based navigation, form validation

### Enhancement Details:

#### What's Being Added:
1. **AI Knowledge Management Module** (`ui/ai_manager.py`)
   - Document upload and processing pipeline
   - Vector embedding generation using OpenAI Embeddings API
   - Document chunking with configurable strategies
   - RAG-based query interface
   - Document lifecycle management (CRUD operations)

2. **System Prompts Management:**
   - **Database table for prompts:** Store and version system prompts
   - **Form integration points:** Connect prompts to specific form fields
   - **Dynamic prompt selection:** Context-aware prompt usage
   - **Prompt editing interface:** Admin can modify prompts without code changes
   - **Usage tracking:** Monitor which prompts are used where

3. **AI Integration Points in Forms:**
   - **Vrsta javnega naročila:** Special requirements from co-financier
   - **Pogajanja:** Special negotiation requests
   - **Pogoji za sodelovanje:** 
     - Professional activity suitability (drugo)
     - Economic and financial standing (drugo)
     - Technical and professional ability (drugo)
   - **Variante merila:** Alternative criteria suggestions

4. **Hybrid Storage Architecture:**
   - **SQLite:** Document metadata, processing status, chunking configuration, system prompts
   - **File System:** Raw documents in organized directory structure (`/data/documents/`)
   - **OpenAI:** Generate text embeddings via Embeddings API
   - **Qdrant:** Store and search vector embeddings with metadata filtering

5. **Configuration Management:**
   - Secure API key storage in `.env` file (never in database or code)
   - Environment variable loading with `python-dotenv`

6. **User Interface Components:**
   - Document upload with drag-and-drop
   - Processing status dashboard
   - Document explorer with search/filter
   - Query interface with context display
   - System prompts editor with preview
   - Settings panel for non-sensitive configuration (chunk size, temperature, etc.)
   - API status indicators (connected/disconnected)
   - AI suggestion buttons in forms

### Architecture Decisions:

#### Storage Strategy (Hybrid Approach):
```python
# SQLite Schema
documents_table = {
    'id': 'INTEGER PRIMARY KEY',
    'filename': 'TEXT',
    'file_path': 'TEXT',  # Relative path in file system
    'file_type': 'TEXT',
    'file_size': 'INTEGER',
    'upload_date': 'DATETIME',
    'processing_status': 'TEXT',  # pending, processing, completed, failed
    'chunk_count': 'INTEGER',
    'embedding_model': 'TEXT',
    'metadata_json': 'TEXT'
}

document_chunks_table = {
    'id': 'INTEGER PRIMARY KEY',
    'document_id': 'INTEGER FOREIGN KEY',
    'chunk_index': 'INTEGER',
    'chunk_text': 'TEXT',
    'chunk_size': 'INTEGER',
    'vector_id': 'TEXT',  # Qdrant point ID
    'created_at': 'DATETIME'
}

system_prompts_table = {
    'id': 'INTEGER PRIMARY KEY',
    'prompt_key': 'TEXT UNIQUE',  # Identifier for the prompt location
    'form_section': 'TEXT',  # vrsta_narocila, pogajanja, pogoji_sodelovanje, variante_merila
    'field_name': 'TEXT',  # Specific field identifier
    'prompt_text': 'TEXT',  # The actual system prompt
    'description': 'TEXT',  # Admin-friendly description
    'is_active': 'BOOLEAN',
    'version': 'INTEGER',
    'created_at': 'DATETIME',
    'updated_at': 'DATETIME',
    'usage_count': 'INTEGER DEFAULT 0'
}

prompt_usage_log_table = {
    'id': 'INTEGER PRIMARY KEY',
    'prompt_id': 'INTEGER FOREIGN KEY',
    'form_section': 'TEXT',
    'user_input': 'TEXT',
    'ai_response': 'TEXT',
    'response_time_ms': 'INTEGER',
    'tokens_used': 'INTEGER',
    'created_at': 'DATETIME'
}
```

#### Environment Configuration (.env):
```bash
# .env file (never commit to version control)
# OpenAI Configuration
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Qdrant Configuration
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_API_KEY=your-qdrant-api-key
QDRANT_COLLECTION_NAME=javna_narocila_docs

# Application Settings
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
AI_TIMEOUT_SECONDS=30
CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Feature Flags
ENABLE_AI_SUGGESTIONS=true
ENABLE_DOCUMENT_UPLOAD=true
LOG_AI_USAGE=true
```

#### Class Structure:
```python
class AIKnowledgeManager:
    """Main orchestrator for AI knowledge operations"""
    
class DocumentProcessor:
    """Handles document ingestion and chunking"""
    
class EmbeddingGenerator:
    """Generates embeddings using OpenAI Embeddings API"""
    
class VectorStoreManager:
    """Manages Qdrant vector database operations (storage and retrieval only)"""
    
class QueryEngine:
    """RAG implementation for document queries"""
    
class SystemPromptManager:
    """Manages system prompts for form AI assistance"""
    
class FormAIAssistant:
    """Provides AI suggestions for form fields"""
    
class ConfigurationManager:
    """Secure API key and settings management from .env file"""
    
    def __init__(self):
        from dotenv import load_dotenv
        load_dotenv()  # Load from .env file
        
    def get_openai_key(self) -> str:
        return os.getenv('OPENAI_API_KEY')
    
    def get_qdrant_config(self) -> dict:
        return {
            'host': os.getenv('QDRANT_HOST', 'localhost'),
            'port': int(os.getenv('QDRANT_PORT', 6333)),
            'api_key': os.getenv('QDRANT_API_KEY')
        }
```

### Success Criteria:
- Non-technical users can upload and manage documents without assistance
- Document processing pipeline handles multiple file formats (PDF, DOCX, TXT, MD)
- Query responses include source citations and confidence scores
- System maintains performance with 1000+ documents
- API keys are securely stored in `.env` file only
- No API keys appear in code, database, or UI
- Application gracefully handles missing API keys with clear error messages

## Stories

### Story 1: Core Infrastructure and System Prompts Management
**Description:** Implement the foundational document storage system with upload, metadata tracking, and system prompts management for form AI assistance.

**Key Components:**
- SQLite schema creation for documents, chunks, and system prompts
- File system organization with proper directory structure
- Document upload interface with validation
- System prompts CRUD interface in admin panel
- Form integration points for AI assistance
- Status tracking and error handling

**Acceptance Criteria:**
- Documents can be uploaded via drag-and-drop or file selector
- System prompts can be created, edited, and versioned
- AI assistance buttons appear in specified form fields
- Prompts are correctly mapped to form sections
- Delete operation removes both DB records and files
- Usage tracking captures all AI interactions

### Story 2: Vector Processing and Form AI Integration
**Description:** Integrate OpenAI for both embeddings generation and completions, Qdrant for vector storage only, and connect AI assistance to form fields.

**Key Components:**
- OpenAI Embeddings API for generating text embeddings
- OpenAI Completions API for generating AI suggestions
- Qdrant client setup for vector storage and similarity search
- Chunking strategies (fixed-size, sentence-based, semantic)
- Form AI assistant for specific fields:
  - Vrsta naročila: Special co-financier requirements
  - Pogajanja: Special negotiation requests
  - Pogoji sodelovanje: Professional/economic/technical suggestions
  - Variante merila: Alternative criteria suggestions
- Background processing with progress tracking
- Error recovery and retry logic

**Acceptance Criteria:**
- Documents are automatically chunked upon upload
- Embeddings are generated using OpenAI Embeddings API
- Generated embeddings are stored in Qdrant for vector search
- AI suggestions are contextually relevant to form fields
- Processing status is real-time updated in UI
- Form fields show AI suggestion buttons when applicable
- Response time for AI suggestions is under 2 seconds
- OpenAI API usage is tracked for cost monitoring

### Story 3: Query Interface and Advanced Features
**Description:** Build the user-facing query system with context retrieval, response generation, and prompt analytics.

**Key Components:**
- Query input interface with auto-suggestions
- Vector similarity search in Qdrant
- Context assembly from relevant chunks
- OpenAI completion for response generation
- Source attribution and confidence display
- System prompt performance analytics
- Usage statistics dashboard

**Acceptance Criteria:**
- Users can query the knowledge base in natural language
- Responses include relevant context from documents
- Sources are clearly cited with document names
- Admin can view prompt usage statistics
- Response time is under 3 seconds for typical queries
- UI shows thinking/processing indicators
- Analytics show most-used prompts and average response times

## Compatibility Requirements
- [x] Existing admin panel tabs remain functional
- [x] Database migrations are non-destructive
- [x] UI components follow established gradient styling
- [x] ValidationManager pattern is extended for AI settings
- [x] Session state management follows existing patterns

## Risk Mitigation

### Primary Risks:

1. **API Key Security**
   - **Risk:** Exposure of sensitive API keys
   - **Mitigation:** 
     - Store all keys in `.env` file (never in code or database)
     - Add `.env` to `.gitignore` to prevent version control exposure
     - Load keys only server-side using `python-dotenv`
     - Never expose keys in Streamlit UI or client-side code
   - **Rollback:** Immediate key rotation, audit logs, check git history

2. **Storage Scalability**
   - **Risk:** File system bloat with large documents
   - **Mitigation:** File size limits, compression, periodic cleanup
   - **Rollback:** Archive old documents, implement quotas

3. **Vector Database Availability**
   - **Risk:** Qdrant connection failures
   - **Mitigation:** Connection pooling, retry logic, graceful degradation
   - **Rollback:** Cache recent queries, offline mode indicator

4. **Processing Performance**
   - **Risk:** UI blocking during document processing
   - **Mitigation:** Background tasks, progress indicators, batch processing
   - **Rollback:** Manual processing trigger, smaller batch sizes

## Implementation Guidelines

### Initial Setup: Environment Configuration
```python
# setup_environment.py
import os
from pathlib import Path

def setup_environment():
    """Validate .env file exists with required keys"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("ERROR: .env file not found")
        print("Please create .env file with required API keys:")
        print("  OPENAI_API_KEY=your-key-here")
        print("  QDRANT_API_KEY=your-key-here")
        return False
    
    # Validate required keys are present
    from dotenv import load_dotenv
    load_dotenv()
    
    required_keys = ['OPENAI_API_KEY', 'QDRANT_API_KEY']
    missing_keys = [key for key in required_keys if not os.getenv(key)]
    
    if missing_keys:
        print(f"Missing required API keys in .env: {missing_keys}")
        return False
    
    return True

# Add to .gitignore
"""
# API Keys and Secrets
.env
*.key
*.pem
"""
```

### Phase 1: Foundation (Story 1)
```python
# ui/ai_manager.py structure
def render_ai_manager():
    """Main entry point from admin panel"""
    inject_custom_css()
    
    tabs = st.tabs(["📚 Documents", "🔍 Query", "🤖 Prompts", "⚙️ Settings", "📊 Analytics"])
    
    with tabs[0]:
        render_document_management()
    with tabs[1]:
        render_query_interface()
    with tabs[2]:
        render_system_prompts_management()
    with tabs[3]:
        render_settings_panel()
    with tabs[4]:
        render_analytics_dashboard()

# System Prompts Management
def render_system_prompts_management():
    """Manage system prompts for form AI assistance"""
    
    # Prompt sections mapping
    PROMPT_SECTIONS = {
        'vrsta_narocila': {
            'title': 'Vrsta javnega naročila',
            'fields': ['posebne_zahteve_sofinancerja']
        },
        'pogajanja': {
            'title': 'Pogajanja',
            'fields': ['posebne_zelje_pogajanja']
        },
        'pogoji_sodelovanje': {
            'title': 'Pogoji za sodelovanje',
            'fields': [
                'ustreznost_poklicna_drugo',
                'ekonomski_polozaj_drugo',
                'tehnicna_sposobnost_drugo'
            ]
        },
        'variante_merila': {
            'title': 'Variante merila',
            'fields': ['merila_drugo']
        }
    }
    
    # CRUD interface for prompts
    selected_section = st.selectbox("Izberi sekcijo", list(PROMPT_SECTIONS.keys()))
    # ... prompt editing interface
```

### Phase 2: Vector Integration (Story 2)
```python
# OpenAI Embedding Generation
class EmbeddingGenerator:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_EMBEDDING_MODEL', 'text-embedding-3-small')
    
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings using OpenAI API"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [embedding.embedding for embedding in response.data]
        except Exception as e:
            logger.error(f"Failed to generate embeddings: {e}")
            raise
    
    def generate_single_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text"""
        embeddings = self.generate_embeddings([text])
        return embeddings[0] if embeddings else None

# Integration with Qdrant (storage only)
class VectorStoreManager:
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.client = QdrantClient(
            host=os.getenv('QDRANT_HOST'),
            port=int(os.getenv('QDRANT_PORT')),
            api_key=os.getenv('QDRANT_API_KEY')
        )
    
    def store_embeddings(self, chunks: List[Dict], document_id: str):
        """Store OpenAI-generated embeddings in Qdrant"""
        # Generate embeddings using OpenAI
        texts = [chunk['text'] for chunk in chunks]
        embeddings = self.embedding_generator.generate_embeddings(texts)
        
        # Store in Qdrant
        points = [
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    'document_id': document_id,
                    'chunk_index': i,
                    'text': chunk['text'],
                    'metadata': chunk.get('metadata', {})
                }
            )
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings))
        ]
        
        self.client.upsert(
            collection_name=os.getenv('QDRANT_COLLECTION_NAME'),
            points=points
        )
```

### Phase 3: Query System and Form Integration (Story 3)
```python
# RAG implementation
class QueryEngine:
    def __init__(self):
        self.embedding_generator = EmbeddingGenerator()
        self.vector_store = VectorStoreManager()
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    def process_query(self, query: str, top_k: int = 5) -> QueryResult:
        # 1. Generate query embedding using OpenAI
        query_embedding = self.embedding_generator.generate_single_embedding(query)
        
        # 2. Search Qdrant for similar chunks (vector search only)
        similar_chunks = self.vector_store.search(query_embedding, top_k)
        
        # 3. Assemble context from chunks
        context = self.assemble_context(similar_chunks)
        
        # 4. Generate response with OpenAI Completions API
        response = self.openai_client.chat.completions.create(
            model=os.getenv('OPENAI_MODEL', 'gpt-4-turbo-preview'),
            messages=[
                {"role": "system", "content": "Answer based on the provided context."},
                {"role": "user", "content": f"Context: {context}\n\nQuery: {query}"}
            ]
        )
        
        # 5. Format with citations
        return self.format_response(response, similar_chunks)

# Form AI Integration Example
class FormAIAssistant:
    def get_ai_suggestion(self, form_section: str, field_name: str, context: dict) -> str:
        """Generate AI suggestion for specific form field"""
        
        # Get relevant system prompt
        prompt = SystemPromptManager().get_prompt(form_section, field_name)
        
        # Get relevant documents from knowledge base
        relevant_docs = QueryEngine().get_relevant_context(context)
        
        # Generate suggestion using OpenAI
        suggestion = self.generate_suggestion(prompt, relevant_docs, context)
        
        # Log usage for analytics
        self.log_usage(form_section, field_name, suggestion)
        
        return suggestion

# Integration in existing forms (example for vrsta_narocila)
def render_vrsta_narocila_form():
    """Existing form with AI assistance"""
    
    # Existing field
    if st.checkbox("Navedite posebne zahteve sofinancerja"):
        col1, col2 = st.columns([4, 1])
        
        with col1:
            special_requirements = st.text_area(
                "Posebne zahteve:",
                key="posebne_zahteve_sofinancerja"
            )
        
        with col2:
            if st.button("🤖 AI predlog", key="ai_vrsta_narocila"):
                # Get AI suggestion
                suggestion = FormAIAssistant().get_ai_suggestion(
                    form_section="vrsta_narocila",
                    field_name="posebne_zahteve_sofinancerja",
                    context=st.session_state.form_data
                )
                
                # Update the text area
                st.session_state.posebne_zahteve_sofinancerja = suggestion
                st.rerun()
```

## Beautiful UI Components

### Document Upload Card:
```python
st.markdown("""
<div style="
    padding: 40px;
    border-radius: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    text-align: center;
    border: 2px dashed rgba(255,255,255,0.3);
">
    <h2>📤 Drop Documents Here</h2>
    <p>PDF, DOCX, TXT, MD supported • Max 10MB per file</p>
</div>
""", unsafe_allow_html=True)
```

### Processing Status:
- Real-time progress bars with chunk count
- Color-coded status badges (pending=yellow, processing=blue, completed=green, failed=red)
- Animated processing indicators
- Toast notifications for completion

### Query Interface:
- Large, prominent search box with placeholder examples
- Auto-complete suggestions from document titles
- Response cards with gradient borders
- Collapsible source context panels
- Confidence score visualization

## Definition of Done
- [x] All three stories completed with acceptance criteria met
- [x] Document upload and management fully functional
- [x] Vector embeddings generated and searchable
- [x] Query interface returns relevant responses with sources
- [x] API keys securely managed
- [x] UI is intuitive for non-technical users
- [x] Performance benchmarks met (3s query response)
- [x] Error handling covers all edge cases
- [x] Admin panel integration seamless

## Next Steps and Recommendations

### For Production Scaling:
1. Consider moving to cloud storage (S3) for documents
2. Implement caching layer (Redis) for frequent queries
3. Add monitoring and alerting for API usage
4. Consider rate limiting for API calls

### For Enhanced Features (Future):
1. Multi-language support for documents
2. Document versioning and change tracking
3. Collaborative annotations
4. Export functionality for knowledge graphs
5. Integration with external knowledge bases

---

## Story Manager Handoff:

"Please develop detailed user stories for this AI Knowledge Management epic. Key considerations:

- This is an enhancement to an existing Streamlit-based admin system with form workflow
- Integration points: Admin panel tabs, SQLite database, ValidationManager, existing form fields
- System prompts must integrate with 4 specific form sections (vrsta_narocila, pogajanja, pogoji_sodelovanje, variante_merila)
- AI assistance buttons must appear in specific form fields for "drugo" (other) options
- Existing patterns to follow: Gradient UI styling, session state management, modular file structure
- Critical compatibility requirements: Maintain existing admin functionality, preserve form workflows, follow established UI patterns
- Each story must include verification that existing admin features and forms remain intact

The epic should deliver:
1. A user-friendly AI knowledge management system for document upload and RAG queries
2. System prompts management interface for administrators
3. Seamless AI assistance integration in existing form fields
4. Analytics dashboard for monitoring AI usage and performance

All features must be accessible to non-technical users while maintaining system integrity, security, and existing workflows."