from odoo import models


class RagEmbeddingService(models.AbstractModel):
    """Embedding indexing and similarity retrieval for schema, methods, and docs."""

    _name = "rag.embedding.service"
    _description = "RAG Embedding Service"

    def rebuild_embeddings(self):
        self.env["rag.vector.index"].search([]).unlink()

        schema_models = self.env["schema.model"].search([])
        for model in schema_models:
            text = self._serialize_schema_model(model)
            self._create_embedding(namespace="schema", chunk_text=text)
            for method in model.method_ids:
                method_text = f"model={model.model}\nmethod={method.name}{method.signature}\ndoc={method.docstring or ''}"
                self._create_embedding(namespace="method", chunk_text=method_text)

        for doc in self.env["rag.document"].search([("active", "=", True)]):
            self._create_embedding(namespace="knowledge", chunk_text=doc.content, document_id=doc.id)
        return True

    def semantic_search(self, query, namespaces=None, limit=5):
        namespaces = namespaces or ["schema", "method", "knowledge"]
        query_embedding = self.env["llm.connector.service"].embed_text(query)
        vector_literal = "[" + ",".join(str(x) for x in query_embedding) + "]"
        self.env.cr.execute(
            """
            SELECT idx.id, idx.namespace, idx.chunk_text,
                   emb.embedding <-> %s::vector AS distance
            FROM rag_vector_index idx
            JOIN rag_vector_embedding emb ON emb.index_id = idx.id
            WHERE idx.namespace = ANY(%s)
            ORDER BY emb.embedding <-> %s::vector
            LIMIT %s
            """,
            (vector_literal, namespaces, vector_literal, limit),
        )
        return [
            {"id": row[0], "namespace": row[1], "chunk_text": row[2], "distance": row[3]}
            for row in self.env.cr.fetchall()
        ]

    def _create_embedding(self, namespace, chunk_text, document_id=False):
        index = self.env["rag.vector.index"].create({
            "namespace": namespace,
            "chunk_text": chunk_text,
            "document_id": document_id or False,
            "embedding_hash": "pending",
        })
        embedding = self.env["llm.connector.service"].embed_text(chunk_text)
        index.set_embedding(embedding)

    def _serialize_schema_model(self, model):
        field_lines = [f"{f.name}:{f.ttype}" for f in model.field_ids]
        method_lines = [f"{m.name}{m.signature}" for m in model.method_ids]
        return (
            f"model={model.model}\n"
            f"name={model.name}\n"
            f"description={model.description or ''}\n"
            f"fields={'; '.join(field_lines)}\n"
            f"methods={'; '.join(method_lines)}"
        )
