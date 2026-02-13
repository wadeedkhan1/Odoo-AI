"""CLI for AskOdoo workflow automation."""

import argparse

from odoo import api
from odoo.modules.registry import Registry


def _with_env(db_name, uid=1):
    registry = Registry(db_name)
    with registry.cursor() as cr:
        env = api.Environment(cr, uid, {})
        yield env


def build_embeddings(db_name):
    for env in _with_env(db_name):
        env['askodoo.schema.model'].extract_all_models()
        env['askodoo.rag.document'].build_schema_embeddings()


def ask_query(db_name, query):
    for env in _with_env(db_name):
        return env['askodoo.chat.session'].ask(query)


def main():
    parser = argparse.ArgumentParser(description='AskOdoo CLI')
    sub = parser.add_subparsers(dest='command')

    cmd_embed = sub.add_parser('build-embeddings')
    cmd_embed.add_argument('--db', required=True)

    cmd_query = sub.add_parser('query')
    cmd_query.add_argument('--db', required=True)
    cmd_query.add_argument('--text', required=True)

    args = parser.parse_args()
    if args.command == 'build-embeddings':
        build_embeddings(args.db)
        print('Embeddings updated')
    elif args.command == 'query':
        print(ask_query(args.db, args.text))


if __name__ == '__main__':
    main()
