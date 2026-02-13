# AskOdoo - AI-Powered Odoo Database Assistant

AskOdoo is a modular Odoo addon collection that combines Retrieval-Augmented Generation (RAG), multi-provider LLM integration, and a safe ORM execution engine.

## Project Structure

```text
addons/
  schema_extract/   # model/field/method extraction and metadata catalog
  rag_embedding/    # pgvector-backed embeddings and semantic retrieval
  llm_connector/    # OpenAI/Gemini/Ollama providers + prompt orchestration
  orm_executor/     # allowlisted and ACL-aware ORM tool execution
  ai_assistant/     # chat orchestration, API controller, and CLI
```

## Architecture Overview

```mermaid
flowchart LR
    U[User Query] --> A[ai_assistant]
    A --> R[rag_embedding Retriever]
    R --> S[schema_extract Catalog]
    R --> D[Business Docs]
    A --> L[llm_connector]
    L --> P[Prompt with schema+methods]
    P --> M[LLM]
    M --> T{Tool call JSON?}
    T -->|Yes| E[orm_executor]
    E --> O[Odoo ORM + ACL]
    O --> X[Execution Log]
    T -->|No| A
    E --> A
    A --> U
```

## Database Diagram

```mermaid
erDiagram
    SCHEMA_MODEL ||--o{ SCHEMA_FIELD : has
    SCHEMA_MODEL ||--o{ SCHEMA_METHOD : exposes
    RAG_DOCUMENT ||--o{ RAG_VECTOR_INDEX : chunked_to
    ORM_EXECUTION_LOG }o--|| RES_USERS : executed_by

    SCHEMA_MODEL {
        int id
        string model
        string name
        text description
        bool transient
        datetime last_extracted
    }
    SCHEMA_FIELD {
        int id
        int model_ref
        string name
        string ttype
        bool required
        bool readonly
    }
    SCHEMA_METHOD {
        int id
        int model_ref
        string name
        text signature
        text docstring
        bool is_safe_candidate
    }
    RAG_DOCUMENT {
        int id
        string source
        text content
        json metadata
    }
    RAG_VECTOR_INDEX {
        int id
        int document_id
        string namespace
        text chunk_text
        int dims
        string embedding_hash
    }
    ORM_EXECUTION_LOG {
        int id
        string model
        string method
        json payload
        string status
        text message
    }
```

## Sequence Flow (RAG + ORM Execution)

```mermaid
sequenceDiagram
    participant User
    participant Assistant as ai_assistant
    participant Retriever as rag_embedding
    participant LLM as llm_connector
    participant Executor as orm_executor

    User->>Assistant: "Confirm sales order SO123"
    Assistant->>Retriever: semantic_search(query)
    Retriever-->>Assistant: sale.order schema + action_confirm method
    Assistant->>LLM: Prompt(schema, methods, context, query)
    LLM-->>Assistant: {"tool":"orm_call", "args":...}
    Assistant->>Executor: execute_tool_call(payload)
    Executor->>Executor: allowlist + ACL + method validation
    Executor-->>Assistant: success/failure + records
    Assistant-->>User: final response
```

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure PostgreSQL has pgvector extension available.
3. Add this repository's `addons` directory to your Odoo `addons_path`.
4. Install modules in this order:
   - `llm_connector`
   - `schema_extract`
   - `rag_embedding`
   - `orm_executor`
   - `ai_assistant`

## Configuration

- Configure one or more LLM backends in **Settings → Technical → AskOdoo → LLM Backends**.
- Mark one backend as default.
- Run schema extraction once after installing modules.

## CLI and Operational Commands

### Extract schema and methods
```bash
odoo-bin shell -d <db> -c <odoo.conf> -c "env['schema.catalog.service'].refresh_schema_catalog()"
```

### Build embeddings from schema and documents
```bash
odoo-bin shell -d <db> -c <odoo.conf> -c "env['rag.embedding.service'].rebuild_embeddings()"
```

### Run AskOdoo assistant from CLI
```bash
python addons/ai_assistant/tools/askodoo_cli.py --config <odoo.conf> --db <db> --query "Confirm sales order SO123"
```

## Example Workflow

1. Query: `Confirm sales order 'SO123'`.
2. Retriever returns schema/method grounding for `sale.order` and `action_confirm`.
3. LLM generates tool call:
   ```json
   {
     "tool": "orm_call",
     "args": {
       "model": "sale.order",
       "method": "action_confirm",
       "domain": [["name", "=", "SO123"]]
     }
   }
   ```
4. `orm_executor` validates allowlist + ACL and executes the method safely.
5. Execution is logged to `orm.execution.log`.

## Tests

Run module tests:
```bash
odoo-bin -d <db> --test-enable --init orm_executor,ai_assistant --stop-after-init
```

## Notes

- If no valid method can be verified, the executor returns `NO_VALID_METHOD`.
- All tool executions remain bounded by the current Odoo user permissions and record rules.
