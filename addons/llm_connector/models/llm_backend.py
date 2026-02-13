import json
from odoo import fields, models


class LlmBackend(models.Model):
    """Configuration registry for LLM and embedding providers."""

    _name = "llm.backend"
    _description = "LLM Backend"

    name = fields.Char(required=True)
    provider = fields.Selection(
        selection=[("openai", "OpenAI"), ("gemini", "Gemini"), ("ollama", "Ollama")],
        required=True,
    )
    endpoint = fields.Char(help="Base API URL (if provider needs custom endpoint).")
    api_key = fields.Char(help="API key for remote providers.")
    completion_model = fields.Char(required=True)
    embedding_model = fields.Char(required=True)
    options_json = fields.Text(default="{}", help="Provider-specific options as JSON.")
    is_default = fields.Boolean(default=False)

    def get_options(self):
        """Return parsed backend options, defaulting to an empty dictionary."""
        self.ensure_one()
        try:
            return json.loads(self.options_json or "{}")
        except json.JSONDecodeError:
            return {}
