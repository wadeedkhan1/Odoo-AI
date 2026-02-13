import json
import re
from odoo import models


class AskOdooAssistantService(models.AbstractModel):
    """Main orchestration service for RAG-grounded prompts and tool execution."""

    _name = "ai.assistant.service"
    _description = "AskOdoo Assistant Service"

    SYSTEM_PROMPT = (
        "You are AskOdoo, an AI assistant for Odoo. "
        "Always produce safe answers grounded in provided schema/method context. "
        "If an executable action is needed, output only JSON tool call with tool='orm_call'."
    )

    def ask(self, query, session_id=False):
        session = self._get_or_create_session(query, session_id)
        retrieved = self.env["rag.embedding.service"].semantic_search(query)
        prompt = self._build_prompt(query, retrieved, session)
        llm_text = self.env["llm.connector.service"].complete(prompt)
        tool_call = self._extract_tool_call(llm_text)

        if tool_call:
            result = self.env["orm.executor.service"].execute_tool_call(tool_call)
            session.write({
                "response": json.dumps(result, indent=2),
                "tool_payload": json.dumps(tool_call, indent=2),
                "state": "completed" if result.get("status") == "OK" else "failed",
            })
            return result

        session.write({"response": llm_text, "state": "completed"})
        return {"status": "OK", "result": llm_text}

    def _build_prompt(self, query, retrieved, session):
        grouped = {"schema": [], "method": [], "knowledge": []}
        for rec in retrieved:
            grouped.setdefault(rec["namespace"], []).append(rec["chunk_text"])

        return (
            f"System Instructions:\n{self.SYSTEM_PROMPT}\n\n"
            f"Retrieved Schema:\n" + "\n\n".join(grouped.get("schema", [])) + "\n\n"
            f"Available Methods:\n" + "\n\n".join(grouped.get("method", [])) + "\n\n"
            f"Business Context:\n" + "\n\n".join(grouped.get("knowledge", [])) + "\n\n"
            f"Conversation Context:\nLast Query: {session.query}\nLast Response: {session.response or ''}\n\n"
            f"User Query:\n{query}\n"
        )

    def _extract_tool_call(self, text):
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        fenced = re.search(r"```json\s*(\{.*?\})\s*```", text, re.S)
        if fenced:
            try:
                return json.loads(fenced.group(1))
            except json.JSONDecodeError:
                return None
        return None

    def _get_or_create_session(self, query, session_id=False):
        if session_id:
            session = self.env["ai.assistant.session"].browse(session_id)
            if session.exists():
                return session
        return self.env["ai.assistant.session"].create({"query": query})
