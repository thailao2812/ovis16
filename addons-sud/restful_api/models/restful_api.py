# -*- coding: utf-8 -*-
import werkzeug
from odoo import SUPERUSER_ID
# from odoo.http import http
from odoo.http.http import request
# odoo.addons.website import slug, unslug
# from odoo.httpsite_partner.controllers.main import WebsitePartnerPage
from odoo.tools.translate import _
import json
from odoo import http


class WebsiteCrmPartnerAssign(http.Controller):
    _references_per_page = 40

    @http.route(['/product'], type='http', auth="public", website=True)
    def partner(self):
        records = request.env['product.product'].sudo().search([])
        result = '<html><body><table><tr><td>'
        result += '</td></tr><tr><td>'.join(records.mapped('default_code'))
        result += '</td></tr></table></body></html>'
        return result

    @http.route('/product/json', type='http', auth='none', methods=['GET'], website = True, csrf=False)
    def product_json(self):
        records = request.env['product.product'].sudo().search([])
        return records.read(['default_code', 'type'])

    @http.route(['/stock_balance'], type = 'http', auth = 'user', website = True)
    def  stock(self):
        records = request.env['stock.lot'].sudo().search([('remaining_qty', '!=', 0)])
        result = '<html><body><table><tr><td>'
        result += '</td></tr><tr><td>'.join(records.mapped('name'))
        # result += '</td><td> / '.join(str(records.mapped('remaining_qty')))
        result += '</td></tr></table></body></html>'
        return result

    @http.route('/stock_balance/json/<string:stack_no>', type='http', auth='none', methods=['GET'], website = True, csrf=False)
    def stock_json(self, stack_no):
        records = request.env['stock.lot'].sudo().search([('remaining_qty', '!=', 0),('name', '=', stack_no)])

        return records.read(['name', 'remaining_qty'])