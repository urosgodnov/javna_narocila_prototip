# System Architecture Design

## 1. Architecture Overview

This document outlines the high-level system architecture for the Public Procurement Documentation Generator, reflecting the requirement for a fixed form structure loaded at startup. All components run in-process within a single Streamlit app.

---

## 2. Context & Components

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

## 3. Data Flow Sequence

1. **Form Initialization**: On app launch, Form Service loads the fixed JSON schema and renders the full set of form fields.
2. **Draft Save/Retrieve**: User enters data and clicks “Save Draft”—the Form Service writes to SQLite. Selecting a draft loads its JSON into the form.
3. **Context Retrieval**: When the user requests AI text, Semantic Retrieval Service queries ChromaDB for relevant contract excerpts.
4. **AI Generation**: AI Generation Service builds a prompt (fixed system prompt + form data + context) and calls the LLM API to receive narrative text.
5. **Document Assembly**: Document Assembly Service merges data and narratives into `.docx` templates and packages them into an in-memory ZIP.
6. **Download Trigger**: Download Module uses `st.download_button` to serve the in-memory ZIP for user download.

---

## 4. Module Interactions

| Module                     | Invocation Mechanism             | Tech                        |
| -------------------------- | -------------------------------- | --------------------------- |
| Streamlit App              | Streamlit callbacks              | Streamlit (Python)          |
| Form Service               | In-process functions             | Python, SQLAlchemy (SQLite) |
| Template Admin Service     | In-process admin callbacks       | Python, python-docx         |
| Semantic Retrieval Service | In-process embeddings & queries  | Python, ChromaDB client     |
| AI Generation Service      | In-process OpenAI library calls  | Python, openai              |
| Document Assembly Service  | In-process merge & ZIP functions | Python, zipfile             |
| Download Module            | `st.download_button` invocation  | Streamlit (Python)          |

---

## 5. Deployment Topology

- **MVP (Single Container)**:

  - One container hosts the Streamlit app, SQLite file, and ChromaDB instance (Docker Compose or single image).
  - Environment variables configure OpenAI API key and ChromaDB endpoint.

- **Future (Microservices)**:

  - Split services into microservices behind an API gateway.
  - Migrate SQLite to PostgreSQL; use managed ChromaDB.
  - Scale AI Generation via serverless functions.

---

## 6. Security & Compliance

- **HTTPS** for browser-to-app traffic.
- **Secrets** stored as environment variables.
- **Input validation** in Form Service to prevent injection.
- **Role separation**: admin UI protected by a secret URL or token.

---

## 7. Scalability & Extensibility

- **Abstracted persistence layer** allows swapping SQLite for a full RDBMS.
- **ChromaDB client** abstraction for migrating vector stores.
- **Modular design**: each service is in its own Python module, facilitating future extraction.
- **Logging hooks** added to each service for tracing and monitoring.

---

*End of Architecture Design*

