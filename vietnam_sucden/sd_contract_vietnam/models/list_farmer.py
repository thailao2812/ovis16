# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ListFarmer(models.Model):
    _name = 'list.farmer'

    purchase_contract_id = fields.Many2one('purchase.contract')
    farmer_id = fields.Many2one('res.partner', string='Farmer')
    farmer_code = fields.Char(string='Farmer Code', related='farmer_id.partner_code')
    quantity = fields.Float(string='Quantity')
    date = fields.Date(string='Date')


class ResPartner(models.Model):
    _inherit = 'res.partner'

    list_purchase_contract = fields.One2many('list.farmer', 'farmer_id', string='Purchase')