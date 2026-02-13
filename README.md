# AskOdoo - AI-Powered Odoo Database Assistant

AskOdoo is an Odoo addon collection implementing schema-aware Retrieval-Augmented Generation (RAG) and safe ORM execution.

## Addons

- `schema_extract`: discovers models, fields, and callable public methods.
- `rag_embedding`: stores grounding chunks and embeddings in PostgreSQL (with pgvector table).
- `llm_connector`: unified providers (OpenAI, Gemini, Ollama) for embeddings and completions.
- `orm_executor`: allowlisted CRUD + business method executor with execution logs.
- `ai_assistant`: orchestration layer (prompt + chat API + CLI).

## Project Structure

```text
.
├── ai_assistant/
├── llm_connector/
├── orm_executor/
├── rag_embedding/
├── schema_extract/
└── docs/
```

## Installation

1. Place repository in your Odoo addons path.
2. Install Python dependency:
   ```bash
   pip install requests
   ```
3. Ensure PostgreSQL extension is available:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Install modules in order:
   - `schema_extract`
   - `llm_connector`
   - `rag_embedding`
   - `orm_executor`
   - `ai_assistant`

## CLI Commands

```bash
python -m odoo --addons-path=. -d <db> --load=base
python ai_assistant/cli/askodoo_cli.py build-embeddings --db <db>
python ai_assistant/cli/askodoo_cli.py query --db <db> --text "Confirm sales order SO123"
```

## HTTP Query API

`POST /askodoo/query` (JSON):

```json
{"query": "Confirm sales order SO123"}
```

## Example End-to-End Workflow

1. Schema extraction collects `sale.order` fields and methods such as `action_confirm`.
2. Embedding builder indexes schema and method metadata.
3. User asks: `Confirm sales order 'SO123'`.
4. RAG retrieval returns top chunks for `sale.order` and `action_confirm`.
5. Prompt is built with schema grounding and method signatures.
6. LLM returns tool call:

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

7. `orm_executor` validates allowlist and executes via ORM under current user ACL.
8. Execution result and audit logs are saved in `askodoo.execution.log`.

## Testing

```bash
python -m odoo -d <test_db> --test-enable --stop-after-init -i ai_assistant
```

## Architecture Diagrams

See `docs/architecture.md`.
