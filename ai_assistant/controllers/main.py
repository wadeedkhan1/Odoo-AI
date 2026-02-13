"""HTTP controller exposing AskOdoo query endpoint."""

from odoo import http
from odoo.http import request


class AskOdooController(http.Controller):

    @http.route('/askodoo/query', type='json', auth='user')
    def askodoo_query(self, query):
        return request.env['askodoo.chat.session'].sudo().ask(query)
