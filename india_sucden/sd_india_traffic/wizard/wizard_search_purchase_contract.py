# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardSearchPurchaseContract(models.TransientModel):
    _name = "wizard.search.purchase.contract"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    purchase_contract_ids = fields.Many2many('purchase.contract', string='Contract')

    def button_search(self):
        if self.date_to < self.date_from:
            raise UserError(_("You can not set date to < date from, please check again!!!"))
        if self.purchase_contract_ids:
            return {
                'name': _('Purchase Contract - FOB Link'),
                'view_type': 'tree',
                'view_mode': 'tree',
                'view': [(self.env.ref('sd_india_traffic.purchase_contract_fob_management_link_india').id, 'tree')],
                'res_model': 'purchase.contract',
                'context': {},
                'domain': [('id', 'in', self.purchase_contract_ids.ids)],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }
        if not self.purchase_contract_ids:
            purchase_contract = self.env['purchase.contract'].search([
                ('date_order', '>=', self.date_from),
                ('date_order', '<=', self.date_to),
                ('type', 'in', ['purchase']),
                ('state_fob', '=', 'draft')
            ])
            return {
                'name': _('Purchase Contract - FOB Link'),
                'view_type': 'tree',
                'view_mode': 'tree',
                'view': [(self.env.ref('sd_india_traffic.purchase_contract_fob_management_link_india').id, 'tree')],
                'res_model': 'purchase.contract',
                'context': {},
                'domain': [('id', 'in', purchase_contract.ids)],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }