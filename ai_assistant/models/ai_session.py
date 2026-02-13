"""Chat session model orchestrating RAG, prompting, and tool execution."""

from __future__ import annotations

from odoo import api, fields, models


class AskOdooPromptTemplate(models.Model):
    _name = "askodoo.prompt.template"
    _description = "AskOdoo Prompt Template"

    name = fields.Char(required=True)
    body = fields.Text(required=True)
    active = fields.Boolean(default=True)


class AskOdooChatSession(models.Model):
    _name = "askodoo.chat.session"
    _description = "AskOdoo Chat Session"

    name = fields.Char(required=True, default="AskOdoo Session")
    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    history = fields.Text(default="")

    @api.model
    def ask(self, user_query):
        rag_docs = self.env["askodoo.rag.document"].semantic_search(user_query, top_k=6)
        connector = self.env["askodoo.llm.connector"].get_default_connector()
        prompt = self._build_prompt(user_query, rag_docs)
        raw_output = connector.complete_text(prompt)
        tool_payload = connector.parse_tool_call(raw_output)
        if tool_payload.get("tool") == "orm_call":
            result = self.env["askodoo.orm.executor"].execute_tool_call(tool_payload)
            return {"type": "tool_result", "payload": tool_payload, "result": result}
        return {"type": "message", "message": tool_payload.get("args", {}).get("message", raw_output)}

    @api.model
    def _build_prompt(self, query, rag_docs):
        template = self.env["askodoo.prompt.template"].search([("active", "=", True)], limit=1)
        schema_blob = "\n\n".join(doc.content for doc in rag_docs)
        return (template.body if template else "") + (
            "\n\nRetrieved grounding:\n"
            f"{schema_blob}\n\n"
            "Return JSON tool call when action is required."
            "\nUser Query: "
            f"{query}"
        )
