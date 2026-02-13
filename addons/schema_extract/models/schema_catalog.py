from odoo import fields, models


class SchemaModel(models.Model):
    """Catalog of Odoo models available for tool execution."""

    _name = "schema.model"
    _description = "Schema Model"

    name = fields.Char(required=True)
    model = fields.Char(required=True, index=True)
    description = fields.Text()
    transient = fields.Boolean(default=False)
    last_extracted = fields.Datetime()
    field_ids = fields.One2many("schema.field", "model_id")
    method_ids = fields.One2many("schema.method", "model_id")


class SchemaField(models.Model):
    """Field metadata extracted from model _fields."""

    _name = "schema.field"
    _description = "Schema Field"

    model_id = fields.Many2one("schema.model", required=True, ondelete="cascade")
    name = fields.Char(required=True)
    field_description = fields.Char()
    ttype = fields.Char()
    relation = fields.Char()
    required = fields.Boolean(default=False)
    readonly = fields.Boolean(default=False)


class SchemaMethod(models.Model):
    """Method metadata extracted from python classes and registry models."""

    _name = "schema.method"
    _description = "Schema Method"

    model_id = fields.Many2one("schema.model", required=True, ondelete="cascade")
    name = fields.Char(required=True, index=True)
    signature = fields.Char()
    docstring = fields.Text()
    is_safe_candidate = fields.Boolean(default=False)
