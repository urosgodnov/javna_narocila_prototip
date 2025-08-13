# Database Schema Diagram

## Mermaid ERD Code

```mermaid
erDiagram
    drafts {
        int id PK
        text timestamp
        text form_data_json
    }
    
    javna_narocila {
        int id PK
        text organizacija
        text naziv
        text vrsta
        text postopek
        date datum_objave
        text status
        real vrednost
        text form_data_json
        timestamp zadnja_sprememba
        text uporabnik
        timestamp created_at
    }
    
    cpv_codes {
        int id PK
        varchar code UK
        text description
        timestamp created_at
        timestamp updated_at
    }
    
    criteria_types {
        int id PK
        varchar name UK
        text description
        timestamp created_at
    }
    
    cpv_criteria {
        int id PK
        varchar cpv_code FK
        int criteria_type_id FK
        timestamp created_at
        timestamp updated_at
    }
    
    cpv_codes ||--o{ cpv_criteria : has
    criteria_types ||--o{ cpv_criteria : applies_to
```

## Table Descriptions

### drafts
- Stores draft forms with timestamps and JSON data

### javna_narocila
- Main procurement table containing project information
- Tracks organization, name, type, procedure, status, and value
- Stores complete form data as JSON

### cpv_codes
- Common Procurement Vocabulary codes catalog
- Contains unique codes with descriptions

### criteria_types
- Types of criteria that can be applied to procurements
- Contains unique names with optional descriptions

### cpv_criteria
- Junction table for many-to-many relationship
- Links CPV codes with applicable criteria types
- Enforces unique combinations of cpv_code and criteria_type_id