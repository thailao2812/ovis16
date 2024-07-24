# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class XUnallocatedPcontract(models.Model):
    _name = 'x_unallocated.pcontract'

    name = fields.Char(string='P Contract', size=64)
    description = fields.Text('Description')
    product_id = fields.Many2one('product.product', 'Product')
    partner_id = fields.Many2one('res.partner', string='Counter party')
    quality = fields.Char(string='Quality', size=128)
    ship_month_id = fields.Many2one('s.period', 'Shipt Month')
    quantity = fields.Float('Quantity')
    entity_date = fields.Date('Entity Date')
    dd_from = fields.Date('DD FROM')
    dd_to = fields.Date('DD TO')
    origin = fields.Selection([('VN', 'VN'),
                               ('ID', 'ID'),
                               ('IN', 'IN'),
                               ('CO', 'CO'),
                               ('LA', 'LA'),
                               ('CI', 'CI'),  # Ivory Coast
                               ('HN', 'HN'),  # Honduras
                               ('BR', 'BR'),  # Brazil
                               ('GU', 'GU'),  # Guatemala
                               ('UG', 'UG')  # Uganda
                               ], string='Origin', copy=True)
