from odoo import fields, models


class OrmExecutionLog(models.Model):
    """Audit log for AI-driven ORM calls."""

    _name = "orm.execution.log"
    _description = "ORM Execution Log"
    _order = "create_date desc"

    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, required=True)
    model = fields.Char(required=True)
    method = fields.Char(required=True)
    domain_json = fields.Text()
    values_json = fields.Text()
    status = fields.Selection(
        [("success", "Success"), ("denied", "Denied"), ("error", "Error")],
        required=True,
    )
    message = fields.Text()
