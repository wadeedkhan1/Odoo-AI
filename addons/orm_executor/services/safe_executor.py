import json
from odoo import models
from odoo.exceptions import AccessError, UserError


class SafeOrmExecutor(models.AbstractModel):
    """Constrained execution layer for AI tool calls."""

    _name = "orm.executor.service"
    _description = "Safe ORM Executor"

    def execute_tool_call(self, payload):
        """Validate and execute a structured tool call.

        Expected payload:
        {
            "tool": "orm_call",
            "args": {
                "model": "sale.order",
                "method": "action_confirm",
                "domain": [["name", "=", "SO123"]],
                "values": {}
            }
        }
        """
        if payload.get("tool") != "orm_call":
            raise UserError("Unsupported tool")

        args = payload.get("args", {})
        model = args.get("model")
        method = args.get("method")
        domain = args.get("domain", [])
        values = args.get("values", {})

        if not self._is_allowed(model, method):
            self._log(model, method, domain, values, "denied", "NO_VALID_METHOD")
            return {"status": "NO_VALID_METHOD"}

        recordset = self.env[model].search(domain)
        try:
            self.env[model].check_access_rights("read")
            recordset.check_access_rule("read")
            result = self._execute(model, method, recordset, values)
            self._log(model, method, domain, values, "success", "OK")
            return {"status": "OK", "result": self._serialize_result(result)}
        except (AccessError, UserError) as exc:
            self._log(model, method, domain, values, "denied", str(exc))
            return {"status": "DENIED", "message": str(exc)}
        except Exception as exc:  # noqa: BLE001 - explicit audit for unexpected errors
            self._log(model, method, domain, values, "error", str(exc))
            return {"status": "ERROR", "message": str(exc)}

    def _is_allowed(self, model_name, method_name):
        model_ok = self.env["schema.model"].search_count([("model", "=", model_name)]) > 0
        method_ok = self.env["schema.method"].search_count([
            ("model_id.model", "=", model_name),
            ("name", "=", method_name),
            ("is_safe_candidate", "=", True),
        ]) > 0
        return model_ok and method_ok

    def _execute(self, model_name, method_name, recordset, values):
        model_obj = self.env[model_name]
        if method_name == "create":
            model_obj.check_access_rights("create")
            return model_obj.create(values).ids
        if method_name == "write":
            model_obj.check_access_rights("write")
            recordset.check_access_rule("write")
            recordset.write(values)
            return recordset.ids
        if method_name == "unlink":
            model_obj.check_access_rights("unlink")
            recordset.check_access_rule("unlink")
            ids = recordset.ids
            recordset.unlink()
            return ids
        if not hasattr(recordset, method_name):
            return "NO_VALID_METHOD"
        return getattr(recordset, method_name)()

    def _serialize_result(self, result):
        if isinstance(result, models.Model):
            return {"ids": result.ids, "model": result._name}
        if isinstance(result, (list, tuple, dict, str, int, float, bool)) or result is None:
            return result
        return str(result)

    def _log(self, model, method, domain, values, status, message):
        self.env["orm.execution.log"].sudo().create({
            "model": model or "",
            "method": method or "",
            "domain_json": json.dumps(domain),
            "values_json": json.dumps(values),
            "status": status,
            "message": message,
        })
