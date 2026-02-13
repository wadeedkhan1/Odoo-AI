from odoo import http
from odoo.http import request


class AskOdooController(http.Controller):
    """JSON endpoint for external chat integrations."""

    @http.route("/ai_assistant/query", type="json", auth="user", methods=["POST"], csrf=False)
    def query(self, query, session_id=None):
        return request.env["ai.assistant.service"].sudo().ask(query=query, session_id=session_id)
