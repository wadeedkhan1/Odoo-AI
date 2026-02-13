def post_init_hook(cr, registry):
    """Create pgvector extension and side table used by similarity queries."""
    cr.execute("CREATE EXTENSION IF NOT EXISTS vector")
    cr.execute(
        """
        CREATE TABLE IF NOT EXISTS rag_vector_embedding (
            index_id INTEGER PRIMARY KEY REFERENCES rag_vector_index(id) ON DELETE CASCADE,
            embedding vector(1536)
        )
        """
    )
