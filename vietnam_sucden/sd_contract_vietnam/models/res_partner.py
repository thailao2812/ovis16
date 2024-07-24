# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    list_purchase_contract = fields.One2many('list.farmer', 'farmer_id', string='Purchase')
    list_sale_contract = fields.Many2many('s.contract')
    certificate_ids = fields.Many2many('ned.certificate', string='Certificate')