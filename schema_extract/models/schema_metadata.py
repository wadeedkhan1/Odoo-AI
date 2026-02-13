"""Schema and method extraction models for AskOdoo."""

from __future__ import annotations

import inspect
import json
import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class AskOdooSchemaModel(models.Model):
    """Stores extracted Odoo model and field metadata."""

    _name = "askodoo.schema.model"
    _description = "AskOdoo Schema Model"

    model_name = fields.Char(required=True, index=True)
    description = fields.Char()
    transient = fields.Boolean(default=False)
    field_count = fields.Integer(default=0)
    fields_json = fields.Text(help="Serialized field metadata.")
    method_ids = fields.One2many("askodoo.schema.method", "schema_model_id")
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ("askodoo_schema_model_unique", "unique(model_name)", "Model name must be unique."),
    ]

    @api.model
    def extract_all_models(self):
        """Extract all ORM models and persist metadata records."""
        ir_models = self.env["ir.model"].sudo().search([])
        created_or_updated = 0
        for ir_model in ir_models:
            model_name = ir_model.model
            model = self.env.get(model_name)
            if not model:
                continue
            field_map = self._extract_fields_metadata(model)
            values = {
                "model_name": model_name,
                "description": ir_model.name,
                "transient": bool(getattr(model, "_transient", False)),
                "field_count": len(field_map),
                "fields_json": json.dumps(field_map, default=str),
            }
            rec = self.search([("model_name", "=", model_name)], limit=1)
            if rec:
                rec.write(values)
            else:
                rec = self.create(values)
            rec._extract_methods_metadata(model)
            created_or_updated += 1
        _logger.info("AskOdoo extracted %s models", created_or_updated)
        return created_or_updated

    def _extract_fields_metadata(self, model):
        metadata = {}
        for field_name, field in model._fields.items():
            metadata[field_name] = {
                "type": field.type,
                "string": field.string,
                "required": field.required,
                "readonly": field.readonly,
                "store": field.store,
                "relation": getattr(field, "comodel_name", False),
            }
        return metadata

    def _extract_methods_metadata(self, model):
        self.ensure_one()
        self.method_ids.unlink()
        method_records = []
        for method_name in dir(model.__class__):
            if method_name.startswith("_"):
                continue
            if not self._is_supported_method_name(method_name):
                continue
            method = getattr(model.__class__, method_name, None)
            if not callable(method):
                continue
            try:
                signature = str(inspect.signature(method))
            except (TypeError, ValueError):
                signature = "(self, *args, **kwargs)"
            method_records.append({
                "schema_model_id": self.id,
                "name": method_name,
                "signature": signature,
                "docstring": inspect.getdoc(method) or "",
                "is_public": True,
            })
        self.env["askodoo.schema.method"].create(method_records)

    @api.model
    def _is_supported_method_name(self, method_name):
        return method_name.startswith(("action_", "button_")) or not method_name.startswith("onchange")


class AskOdooSchemaMethod(models.Model):
    """Stores extracted callable metadata for model methods."""

    _name = "askodoo.schema.method"
    _description = "AskOdoo Schema Method"

    schema_model_id = fields.Many2one("askodoo.schema.model", required=True, ondelete="cascade")
    name = fields.Char(required=True, index=True)
    signature = fields.Char(required=True)
    docstring = fields.Text()
    is_public = fields.Boolean(default=True)

    _sql_constraints = [
        (
            "askodoo_schema_method_unique",
            "unique(schema_model_id, name)",
            "Each method name must be unique per model.",
        ),
    ]
