{
    "name": "AskOdoo RAG Embedding",
    "version": "16.0.1.0.0",
    "summary": "RAG storage and pgvector retrieval",
    "depends": ["base", "schema_extract", "llm_connector"],
    "data": [
        "security/ir.model.access.csv"
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
}
