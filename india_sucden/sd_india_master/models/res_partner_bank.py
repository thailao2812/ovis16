# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class ResPartnerBank(models.Model):
    _inherit = 'res.partner.bank'

    ifsc_code = fields.Char(string='IFSC Code')
    related_holder = fields.Char(string='Bank Holder Name')
    branch = fields.Char(string='Branch')
    estate_name = fields.Char(string='Estate Name', related='partner_id.estate_name', store=True)

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, rec.acc_number))
        return result