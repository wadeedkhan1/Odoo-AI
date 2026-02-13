{
    "name": "AskOdoo AI Assistant",
    "version": "16.0.1.0.0",
    "summary": "Chat and API interface for AskOdoo",
    "depends": ["base", "rag_embedding", "llm_connector", "orm_executor"],
    "data": [
        "security/ir.model.access.csv",
        "views/assistant_session_views.xml"
    ],
    "installable": True,
    "application": True,
}
