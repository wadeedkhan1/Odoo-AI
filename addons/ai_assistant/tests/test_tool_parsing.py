from odoo.tests.common import TransactionCase


class TestToolParsing(TransactionCase):
    """Validate extraction of JSON tool calls from model output."""

    def test_extract_json_fenced_block(self):
        service = self.env["ai.assistant.service"]
        text = """Here is the tool call:\n```json\n{\"tool\":\"orm_call\",\"args\":{\"model\":\"sale.order\",\"method\":\"action_confirm\",\"domain\":[]}}\n```"""
        payload = service._extract_tool_call(text)
        self.assertEqual(payload["tool"], "orm_call")
