import inspect
from odoo import fields, models


class SchemaCatalogService(models.AbstractModel):
    """Service that extracts model, field, and method metadata from Odoo registry."""

    _name = "schema.catalog.service"
    _description = "Schema Catalog Service"

    SAFE_METHOD_PREFIXES = ("action_", "button_")

    def refresh_schema_catalog(self):
        schema_model_obj = self.env["schema.model"]
        schema_field_obj = self.env["schema.field"]
        schema_method_obj = self.env["schema.method"]

        schema_model_obj.search([]).unlink()

        for model_name in sorted(self.env):
            model = self.env[model_name]
            ir_model = self.env["ir.model"].sudo().search([("model", "=", model_name)], limit=1)
            if not ir_model:
                continue

            model_rec = schema_model_obj.create({
                "name": ir_model.name,
                "model": model_name,
                "description": ir_model.info,
                "transient": bool(getattr(model, "_transient", False)),
                "last_extracted": fields.Datetime.now(),
            })

            for field_name, field in model._fields.items():
                schema_field_obj.create({
                    "model_id": model_rec.id,
                    "name": field_name,
                    "field_description": field.string,
                    "ttype": field.type,
                    "relation": getattr(field, "comodel_name", False),
                    "required": field.required,
                    "readonly": field.readonly,
                })

            methods = self._extract_methods(model)
            for method in methods:
                schema_method_obj.create({
                    "model_id": model_rec.id,
                    "name": method["name"],
                    "signature": method["signature"],
                    "docstring": method["docstring"],
                    "is_safe_candidate": method["is_safe_candidate"],
                })

        return True

    def _extract_methods(self, model):
        extracted = []
        model_class = model.__class__
        for name, member in inspect.getmembers(model_class, predicate=inspect.isfunction):
            if name.startswith("_"):
                continue
            signature = str(inspect.signature(member))
            docstring = inspect.getdoc(member) or ""
            safe_candidate = name.startswith(self.SAFE_METHOD_PREFIXES) or name in {"create", "write", "unlink"}
            extracted.append({
                "name": name,
                "signature": signature,
                "docstring": docstring,
                "is_safe_candidate": safe_candidate,
            })
        return extracted
