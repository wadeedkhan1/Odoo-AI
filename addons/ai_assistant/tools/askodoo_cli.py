#!/usr/bin/env python3
"""CLI wrapper to run AskOdoo from terminal in a typical Odoo setup."""

import argparse
import odoo
from odoo import api
from odoo.tools.config import config


def run_query(cfg, db, query):
    config.parse_config(["-c", cfg])
    registry = odoo.modules.registry.Registry(db)
    with registry.cursor() as cr:
        env = api.Environment(cr, odoo.SUPERUSER_ID, {})
        result = env["ai.assistant.service"].ask(query)
        print(result)


def main():
    parser = argparse.ArgumentParser(description="AskOdoo CLI")
    parser.add_argument("--config", required=True)
    parser.add_argument("--db", required=True)
    parser.add_argument("--query", required=True)
    args = parser.parse_args()
    run_query(args.config, args.db, args.query)


if __name__ == "__main__":
    main()
