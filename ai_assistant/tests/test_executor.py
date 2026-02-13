"""Unit tests for method grounding and safe execution."""

from odoo.tests.common import TransactionCase


class TestAskOdooExecutor(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env['askodoo.schema.model'].extract_all_models()

    def test_denied_unknown_method(self):
        payload = {
            'tool': 'orm_call',
            'args': {'model': 'res.partner', 'method': 'action_nonexistent', 'domain': []},
        }
        result = self.env['askodoo.orm.executor'].execute_tool_call(payload)
        self.assertEqual(result['result'], 'NO_VALID_METHOD')

    def test_allow_write(self):
        partner = self.env['res.partner'].create({'name': 'Old Name'})
        payload = {
            'tool': 'orm_call',
            'args': {
                'model': 'res.partner',
                'method': 'write',
                'domain': [('id', '=', partner.id)],
                'values': {'name': 'New Name'},
            },
        }
        result = self.env['askodoo.orm.executor'].execute_tool_call(payload)
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(partner.name, 'New Name')
