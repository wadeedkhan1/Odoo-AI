{
    "name": "AskOdoo AI Assistant",
    "version": "16.0.1.0.0",
    "summary": "Natural language interface for RAG-grounded Odoo execution.",
    "license": "LGPL-3",
    "depends": ["base", "schema_extract", "rag_embedding", "llm_connector", "orm_executor", "web"],
    "data": ["security/ir.model.access.csv", "data/prompt_template.xml"],
    "installable": True,
}
