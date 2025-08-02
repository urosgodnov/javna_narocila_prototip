# 4. Module Interactions

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
