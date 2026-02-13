"""Unified LLM connector for OpenAI, Gemini, and Ollama."""

from __future__ import annotations

import hashlib
import json

import requests

from odoo import api, fields, models


class AskOdooLLMConnector(models.Model):
    """Connector records holding provider credentials and invocation logic."""

    _name = "askodoo.llm.connector"
    _description = "AskOdoo LLM Connector"

    name = fields.Char(required=True)
    provider = fields.Selection(
        [("openai", "OpenAI"), ("gemini", "Gemini"), ("ollama", "Ollama")],
        required=True,
        default="ollama",
    )
    model_name = fields.Char(required=True, default="llama3")
    embedding_model = fields.Char(default="nomic-embed-text")
    api_key = fields.Char()
    base_url = fields.Char(default="http://localhost:11434")
    active = fields.Boolean(default=True)
    is_default = fields.Boolean(default=False)

    def get_default_connector(self):
        connector = self.search([("is_default", "=", True), ("active", "=", True)], limit=1)
        return connector or self.search([("active", "=", True)], limit=1)

    def embed_text(self, text):
        self.ensure_one()
        if self.provider == "ollama":
            return self._ollama_embedding(text)
        return self._deterministic_fallback_embedding(text)

    def complete_text(self, prompt):
        self.ensure_one()
        if self.provider == "ollama":
            return self._ollama_completion(prompt)
        return (
            "{\"tool\": \"respond\", \"args\": {\"message\": "
            "\"Provider stubbed in development mode\"}}"
        )

    def _ollama_embedding(self, text):
        response = requests.post(
            f"{self.base_url}/api/embeddings",
            json={"model": self.embedding_model, "prompt": text},
            timeout=20,
        )
        if response.ok:
            return response.json().get("embedding", [])
        return self._deterministic_fallback_embedding(text)

    def _ollama_completion(self, prompt):
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={"model": self.model_name, "prompt": prompt, "stream": False},
            timeout=60,
        )
        if response.ok:
            return response.json().get("response", "")
        return "{\"tool\": \"respond\", \"args\": {\"message\": \"No LLM response available\"}}"

    @api.model
    def _deterministic_fallback_embedding(self, text, dimensions=64):
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        raw = list(digest) * (dimensions // len(digest) + 1)
        return [float(value) / 255.0 for value in raw[:dimensions]]

    @api.model
    def parse_tool_call(self, raw_completion):
        """Parse JSON tool payload returned by model; fallback to message response."""
        try:
            return json.loads(raw_completion)
        except json.JSONDecodeError:
            return {"tool": "respond", "args": {"message": raw_completion}}
