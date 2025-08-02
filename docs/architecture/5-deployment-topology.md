# 5. Deployment Topology

- **MVP (Single Container)**:

  - One container hosts the Streamlit app, SQLite file, and ChromaDB instance (Docker Compose or single image).
  - Environment variables configure OpenAI API key and ChromaDB endpoint.

- **Future (Microservices)**:

  - Split services into microservices behind an API gateway.
  - Migrate SQLite to PostgreSQL; use managed ChromaDB.
  - Scale AI Generation via serverless functions.

---
