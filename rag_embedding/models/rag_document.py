"""Embedding document storage and retrieval."""

from __future__ import annotations

import json
import math

from odoo import api, fields, models


class AskOdooRagDocument(models.Model):
    """Represents embedded chunks with pgvector-compatible payload."""

    _name = "askodoo.rag.document"
    _description = "AskOdoo RAG Document"

    name = fields.Char(required=True)
    source_type = fields.Selection(
        [("schema", "Schema"), ("method", "Method"), ("knowledge", "Knowledge")],
        default="knowledge",
        required=True,
    )
    source_ref = fields.Char(index=True)
    content = fields.Text(required=True)
    embedding_json = fields.Text(help="JSON encoded embedding vector.")

    def as_vector(self):
        self.ensure_one()
        return json.loads(self.embedding_json or "[]")


    @api.model
    def init_pgvector(self):
        """Initialize pgvector extension and storage table."""
        self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS vector")
        self.env.cr.execute(
            """
            CREATE TABLE IF NOT EXISTS askodoo_rag_vector (
                id SERIAL PRIMARY KEY,
                document_id INTEGER UNIQUE REFERENCES askodoo_rag_document(id) ON DELETE CASCADE,
                embedding vector(64)
            )
            """
        )

    @api.model
    def _store_pgvector(self, document_id, vector):
        vector_literal = "[" + ",".join(str(float(v)) for v in vector[:64]) + "]"
        self.env.cr.execute(
            """
            INSERT INTO askodoo_rag_vector (document_id, embedding)
            VALUES (%s, %s::vector)
            ON CONFLICT (document_id) DO UPDATE SET embedding = EXCLUDED.embedding
            """,
            (document_id, vector_literal),
        )

    @api.model
    def build_schema_embeddings(self):
        """Refresh embeddings using schema and method metadata."""
        connector = self.env["askodoo.llm.connector"].get_default_connector()
        self.init_pgvector()
        self.search([("source_type", "in", ["schema", "method"])]).unlink()
        for schema in self.env["askodoo.schema.model"].search([]):
            schema_content = f"Model: {schema.model_name}\nDescription: {schema.description}\nFields: {schema.fields_json}"
            schema_rec = self.create({
                "name": schema.model_name,
                "source_type": "schema",
                "source_ref": schema.model_name,
                "content": schema_content,
                "embedding_json": json.dumps(connector.embed_text(schema_content)),
            })
            self._store_pgvector(schema_rec.id, json.loads(schema_rec.embedding_json))
            for method in schema.method_ids:
                method_content = (
                    f"Model: {schema.model_name}\nMethod: {method.name}{method.signature}\n"
                    f"Doc: {method.docstring or ''}"
                )
                method_rec = self.create({
                    "name": f"{schema.model_name}.{method.name}",
                    "source_type": "method",
                    "source_ref": f"{schema.model_name}.{method.name}",
                    "content": method_content,
                    "embedding_json": json.dumps(connector.embed_text(method_content)),
                })
                self._store_pgvector(method_rec.id, json.loads(method_rec.embedding_json))

    @api.model
    def semantic_search(self, query, top_k=5):
        """Naive in-Python cosine scoring for portability; replace with pgvector SQL in production."""
        connector = self.env["askodoo.llm.connector"].get_default_connector()
        query_vector = connector.embed_text(query)
        scored = []
        for doc in self.search([]):
            score = self._cosine_similarity(query_vector, doc.as_vector())
            scored.append((score, doc))
        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]

    @api.model
    def _cosine_similarity(self, vector_a, vector_b):
        if not vector_a or not vector_b or len(vector_a) != len(vector_b):
            return 0.0
        dot = sum(a * b for a, b in zip(vector_a, vector_b))
        norm_a = math.sqrt(sum(a * a for a in vector_a))
        norm_b = math.sqrt(sum(b * b for b in vector_b))
        if not norm_a or not norm_b:
            return 0.0
        return dot / (norm_a * norm_b)
