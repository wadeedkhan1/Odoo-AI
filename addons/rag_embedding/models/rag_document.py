import hashlib
import json
from odoo import fields, models


class RagDocument(models.Model):
    """Business knowledge documents indexed for RAG retrieval."""

    _name = "rag.document"
    _description = "RAG Document"

    name = fields.Char(required=True)
    source = fields.Char(required=True)
    content = fields.Text(required=True)
    metadata_json = fields.Text(default="{}")
    active = fields.Boolean(default=True)


class RagVectorIndex(models.Model):
    """Reference rows connected with pgvector side table for similarity search."""

    _name = "rag.vector.index"
    _description = "RAG Vector Index"

    document_id = fields.Many2one("rag.document", ondelete="cascade")
    namespace = fields.Char(required=True, index=True)
    chunk_text = fields.Text(required=True)
    embedding_hash = fields.Char(required=True)
    dims = fields.Integer(default=0)

    def set_embedding(self, embedding):
        """Persist a numeric vector embedding inside the pgvector table."""
        self.ensure_one()
        hash_value = hashlib.sha256(json.dumps(embedding).encode("utf-8")).hexdigest()
        self.write({"embedding_hash": hash_value, "dims": len(embedding)})
        vector_literal = "[" + ",".join(str(x) for x in embedding) + "]"
        self.env.cr.execute(
            """
            INSERT INTO rag_vector_embedding (index_id, embedding)
            VALUES (%s, %s::vector)
            ON CONFLICT (index_id)
            DO UPDATE SET embedding = EXCLUDED.embedding
            """,
            (self.id, vector_literal),
        )
