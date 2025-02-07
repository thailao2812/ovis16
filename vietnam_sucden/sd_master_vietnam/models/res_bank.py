# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _


class ResBank(models.Model):
    _inherit = 'res.bank'

    @api.depends('bic', 'street', 'city')
    def _compute_display_name(self):
        for bank in self:
            bank.display_name = bank.bic + ' ' + bank.street

    def name_get(self):
        res = []
        for record in self:
            if record.bic and record.street:
                name = record.bic + ' ' + record.street
                res.append((record.id, name))
        return res