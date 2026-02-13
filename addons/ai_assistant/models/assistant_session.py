from odoo import fields, models


class AiAssistantSession(models.Model):
    """Conversation history for AskOdoo interactions."""

    _name = "ai.assistant.session"
    _description = "AI Assistant Session"

    name = fields.Char(required=True, default="AskOdoo Session")
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    query = fields.Text(required=True)
    response = fields.Text()
    tool_payload = fields.Text()
    state = fields.Selection(
        [("draft", "Draft"), ("completed", "Completed"), ("failed", "Failed")],
        default="draft",
        required=True,
    )
