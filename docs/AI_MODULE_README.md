# 🤖 AI Knowledge Management Module

## Overview
The AI Knowledge Management module provides intelligent document processing and AI-powered form assistance for the Slovenian public procurement system. It integrates with OpenAI for text embeddings and completions, and uses Qdrant for vector storage.

## Features

### ✅ Implemented (Story 1 & 2)
- **Document Management**
  - Upload documents with categorization (pogodbe, razpisi, pravilniki, navodila, razno)
  - File type validation (PDF, DOCX, TXT, MD)
  - Metadata storage (description, tags)
  - Document filtering and search
  - File size limit enforcement (10MB)

- **System Prompts Management**
  - CRUD operations for AI prompts
  - Version tracking
  - Active/inactive status
  - Integration with 4 form sections:
    - Vrsta naročila (posebne_zahteve_sofinancerja)
    - Pogajanja (posebne_zelje_pogajanja)
    - Pogoji sodelovanje (3 "drugo" fields)
    - Variante merila (merila_drugo)

- **Environment Validation**
  - API key verification
  - Graceful error handling
  - Configuration status display

- **Vector Processing (Story 2)**
  - Document chunking with configurable overlap
  - OpenAI embeddings generation (text-embedding-3-small)
  - Qdrant vector storage with metadata
  - Offline mode when Qdrant unavailable
  - Processing status tracking
  
- **Form AI Integration (Story 2)**
  - AI suggestion buttons for 6 form fields
  - Context-aware suggestions using RAG
  - Document type filtering for relevance
  - Usage logging and analytics
  - FormAIAssistant for generating suggestions

### 🚧 Pending Implementation

- **Story 3**: Query Interface and Analytics
  - Natural language search
  - RAG implementation
  - Usage analytics
  - Response tracking

## Setup Instructions

### 1. Environment Configuration

Create a `.env` file in the project root with your API keys:

```bash
# Required API Keys
OPENAI_API_KEY=your-openai-api-key-here
QDRANT_API_KEY=your-qdrant-api-key-here

# Optional Configuration
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
AI_MAX_TOKENS=2000
AI_TEMPERATURE=0.7
CHUNK_SIZE=1000
CHUNK_OVERLAP=200
```

### 2. Database Setup

The AI tables are automatically created when you first access the AI Management tab. Tables include:
- `ai_documents` - Document metadata and categorization
- `ai_document_chunks` - Document chunks for processing
- `ai_system_prompts` - System prompts for form assistance
- `ai_prompt_usage_log` - Usage tracking

### 3. Accessing the Module

1. Start the Streamlit application
2. Navigate to Admin Panel (password required)
3. Click on "🤖 AI Management" tab
4. You'll see 5 sub-tabs:
   - 📚 Dokumenti - Document upload and management
   - 🔍 Poizvedbe - Query interface (Story 3)
   - 🤖 Sistemski pozivi - System prompts management
   - ⚙️ Nastavitve - Configuration settings
   - 📊 Analitika - Usage analytics (Story 3)

## Document Types

Documents are categorized into 5 types:
- **pogodbe** (📝) - Contracts
- **razpisi** (📋) - Tenders
- **pravilniki** (📖) - Regulations
- **navodila** (📘) - Instructions
- **razno** (📂) - Other/Miscellaneous

## File Structure

```
/mnt/c/Programiranje/Python/javna_narocila_prototip/
├── ui/
│   ├── ai_manager.py          # Main AI module interface
│   ├── ai_processor.py        # Vector processing engine
│   └── ai_form_integration.py # Form AI field components
├── data/
│   └── documents/             # Document storage
│       ├── pogodbe/
│       ├── razpisi/
│       ├── pravilniki/
│       ├── navodila/
│       └── razno/
├── .env                       # API keys (not in git)
└── .env.example              # Example configuration
```

## Using AI in Forms

### Integration Example

To add AI assistance to your forms, use the `ai_form_integration` module:

```python
from ui.ai_form_integration import render_ai_field

# In your form code:
posebne_zahteve = render_ai_field(
    form_section='vrsta_narocila',
    field_name='posebne_zahteve_sofinancerja',
    field_label='Posebne zahteve sofinancerja',
    placeholder='Vnesite posebne zahteve...',
    context={'vrsta_postopka': 'odprti postopek'}
)
```

### AI-Enabled Form Fields

The following fields have AI assistance available:

1. **Vrsta naročila**
   - `posebne_zahteve_sofinancerja` - Special requirements from co-financier

2. **Pogajanja**
   - `posebne_zelje_pogajanja` - Special negotiation requests

3. **Pogoji za sodelovanje**
   - `ustreznost_poklicna_drugo` - Professional suitability (other)
   - `ekonomski_polozaj_drugo` - Economic status (other)
   - `tehnicna_sposobnost_drugo` - Technical capability (other)

4. **Variante merila**
   - `merila_drugo` - Criteria (other)

### Processing Documents

1. Upload a document through the AI Management interface
2. Click "⚙️ Procesiraj" to generate embeddings
3. The document will be chunked and vectorized
4. Status changes from `pending` → `processing` → `completed`
5. Once completed, the document is searchable for AI suggestions

## Testing

Run the test script to verify installation:

```bash
python3 test_ai_manager.py
```

Expected output:
- ✅ Environment validation
- ✅ Database tables created
- ✅ Document type field verified
- ✅ Default prompts generated

## Security Notes

- API keys are stored in `.env` file only
- `.env` is excluded from version control
- No sensitive data in database or logs
- File uploads validated for type and size

## Next Steps

1. **Implement Story 2**: Add vector processing capabilities
2. **Implement Story 3**: Build query interface and analytics
3. **Configure Qdrant**: Set up vector database instance
4. **Test with real documents**: Upload actual procurement documents

## Troubleshooting

### Missing API Keys
If you see "❌ AI modul ni konfiguriran":
1. Check `.env` file exists
2. Verify both OPENAI_API_KEY and QDRANT_API_KEY are set
3. Restart the application

### Document Upload Issues
- Ensure file is under 10MB
- Check file type is PDF, DOCX, TXT, or MD
- Verify `data/documents/` directory exists and is writable

### Database Errors
- Tables are auto-created on first access
- Run `python3 test_ai_manager.py` to verify setup
- Check `mainDB.db` file permissions

## Support

For issues or questions about the AI module, check:
- This documentation
- Test script output (`test_ai_manager.py`)
- Application logs in the Dnevnik tab