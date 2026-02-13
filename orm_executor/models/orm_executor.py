"""Safe execution layer for model CRUD and business methods."""

from __future__ import annotations

from odoo import api, fields, models


class AskOdooExecutionLog(models.Model):
    """Audit log for all tool-triggered ORM operations."""

    _name = "askodoo.execution.log"
    _description = "AskOdoo Execution Log"

    user_id = fields.Many2one("res.users", required=True, default=lambda self: self.env.user)
    model_name = fields.Char(required=True)
    method_name = fields.Char(required=True)
    domain_json = fields.Text()
    payload_json = fields.Text()
    result_summary = fields.Text()
    status = fields.Selection([("ok", "OK"), ("denied", "Denied"), ("error", "Error")], default="ok")


class AskOdooORMExecutor(models.AbstractModel):
    """Constrained API for safe CRUD and method calls."""

    _name = "askodoo.orm.executor"
    _description = "AskOdoo ORM Executor"

    @api.model
    def execute_tool_call(self, tool_payload):
        if tool_payload.get("tool") != "orm_call":
            return {"status": "ignored", "message": "Unsupported tool"}
        args = tool_payload.get("args", {})
        model_name = args.get("model")
        method = args.get("method")
        domain = args.get("domain", [])
        values = args.get("values", {})
        allowed = self._is_allowed(model_name, method)
        if not allowed:
            self._log(model_name, method, domain, values, "NO_VALID_METHOD", status="denied")
            return {"status": "denied", "result": "NO_VALID_METHOD"}
        model = self.env[model_name]
        records = model.search(domain)
        try:
            if method == "create":
                result = model.create(values).ids
            elif method == "write":
                result = records.write(values)
            elif method == "unlink":
                result = records.unlink()
            else:
                result = getattr(records, method)()
            self._log(model_name, method, domain, values, str(result), status="ok")
            return {"status": "ok", "result": result}
        except Exception as error:  # pylint: disable=broad-except
            self._log(model_name, method, domain, values, str(error), status="error")
            return {"status": "error", "result": str(error)}

    @api.model
    def _is_allowed(self, model_name, method_name):
        schema = self.env["askodoo.schema.model"].search([("model_name", "=", model_name)], limit=1)
        if not schema:
            return False
        if method_name in {"create", "write", "unlink"}:
            return True
        return bool(schema.method_ids.filtered(lambda m: m.name == method_name))

    @api.model
    def _log(self, model_name, method_name, domain, payload, result, status="ok"):
        self.env["askodoo.execution.log"].sudo().create({
            "user_id": self.env.user.id,
            "model_name": model_name or "",
            "method_name": method_name or "",
            "domain_json": str(domain),
            "payload_json": str(payload),
            "result_summary": result,
            "status": status,
        })
