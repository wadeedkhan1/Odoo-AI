from odoo.tests.common import TransactionCase


class TestSafeExecutor(TransactionCase):
    """Validate allowlist behavior and NO_VALID_METHOD fallback."""

    def setUp(self):
        super().setUp()
        self.env["schema.catalog.service"].refresh_schema_catalog()
        self.executor = self.env["orm.executor.service"]

    def test_denies_unknown_method(self):
        payload = {
            "tool": "orm_call",
            "args": {
                "model": "res.partner",
                "method": "totally_unknown_method",
                "domain": [],
            },
        }
        result = self.executor.execute_tool_call(payload)
        self.assertEqual(result["status"], "NO_VALID_METHOD")
