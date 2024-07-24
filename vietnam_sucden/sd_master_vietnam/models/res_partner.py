# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # list_purchase_contract = fields.One2many('list.farmer', 'farmer_id', string='Purchase')
    # list_sale_contract = fields.Many2many('s.contract')
    in_deforestation = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Deforestation', default='no')
    is_farmer = fields.Boolean(string='Farmer', default=False)
    company_name_new = fields.Char(string='Company Name')

    @api.model
    def create(self, vals):
        if not self.env.user.has_group('sd_master_vietnam.group_access_res_partner'):
            raise UserError(_("You don't have permission to do that"))
        return super(ResPartner, self).create(vals)

    def write(self, vals):
        if not self.env.user.has_group('sd_master_vietnam.group_access_res_partner'):
            raise UserError(_("You don't have permission to do that"))
        return super(ResPartner, self).write(vals)

    def purchase_contract(self):
        print(123)

    def sale_contract(self):
        print(234)