# 2. Context & Components

```text
[User Browser] <--HTTPS--> [Streamlit App]
                             ├─ Form Service
                             ├─ Template Admin Service
                             ├─ Semantic Retrieval Service
                             ├─ AI Generation Service
                             ├─ Document Assembly Service
                             └─ Download Module

Database Layer:
  ├─ SQLite (drafts)
  └─ ChromaDB (embeddings)
```

- **Streamlit App**: Single-page application that hosts both user and admin interfaces; leverages Streamlit callbacks to invoke services directly.
- **Form Service**: On startup, loads a fixed JSON schema parsed from `SEZNAM POTREBNIH_PODATKOV.docx`. Renders a static form with predetermined fields. Manages draft save/retrieve operations through SQLite.
- **Template Admin Service**: Administrator-only module for managing Word templates and database operations. Parses `.docx` templates via `python-docx` and exposes controls to view/overwrite templates, clear or back up SQLite drafts, and manage ChromaDB collections.
- **Semantic Retrieval Service**: Generates embeddings for historical contracts and stores them in ChromaDB. Provides a function to retrieve top-k similar contract snippets for prompt enrichment.
- **AI Generation Service**: Composes prompts using a fixed system prompt, user form data, and retrieved context, and calls the LLM (via OpenAI) to generate narrative text.
- **Document Assembly Service**: Uses `python-docx` to merge field values and AI-generated narratives into template documents and then packages them into a ZIP in-memory.
- **Download Module**: Utilizes Streamlit’s `st.download_button` to serve the generated ZIP to end users for direct download.
- **SQLite (Drafts)**: Persists user draft data (JSON blobs) for retrieval across sessions.
- **ChromaDB**: Stores vector embeddings for semantic search of past contracts.

---
