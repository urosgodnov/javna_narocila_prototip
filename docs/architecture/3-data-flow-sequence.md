# 3. Data Flow Sequence

1. **Form Initialization**: On app launch, Form Service loads the fixed JSON schema and renders the full set of form fields.
2. **Draft Save/Retrieve**: User enters data and clicks “Save Draft”—the Form Service writes to SQLite. Selecting a draft loads its JSON into the form.
3. **Context Retrieval**: When the user requests AI text, Semantic Retrieval Service queries ChromaDB for relevant contract excerpts.
4. **AI Generation**: AI Generation Service builds a prompt (fixed system prompt + form data + context) and calls the LLM API to receive narrative text.
5. **Document Assembly**: Document Assembly Service merges data and narratives into `.docx` templates and packages them into an in-memory ZIP.
6. **Download Trigger**: Download Module uses `st.download_button` to serve the in-memory ZIP for user download.

---
