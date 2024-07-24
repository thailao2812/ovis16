# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardSearchSaleContractLinkPurchase(models.TransientModel):
    _name = "wizard.search.sale.contract"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    sale_contract_ids = fields.Many2many('sale.contract.india', string='Contract')

    def button_search(self):
        if self.date_to < self.date_from:
            raise UserError(_("You can not set date to < date from, please check again!!!"))
        if self.sale_contract_ids:
            for sale in self.sale_contract_ids:
                item_group_id = sale.item_group_id
                purchase_contract = self.env['purchase.contract'].search([
                    ('product_id.item_group_id', '=', item_group_id.id),
                    ('type', 'in', ['purchase', 'ptbf']),
                    ('open_qty', '>', 0),
                    ('id', 'not in', self.sale_contract_ids.line_purchase_ids.mapped('purchase_contract_id').ids),
                    ('open_qty_check', '=', False)
                ])
                if sale.state in ['draft', 'submit', 'approve']:
                    for pur in purchase_contract:
                        value = {
                            'purchase_contract_id': pur.id,
                            'sale_contract_id': sale.id
                        }
                        psc_pc_link = self.env['psc.to.pc.linked'].create(value)
                        psc_pc_link.onchange_purchase_contract_id()
                return {
                    'name': _('PSC to PC Linked'),
                    'view_type': 'form',
                    'view_mode': 'tree,form',
                    'views': [(self.env.ref('sd_india_traffic.sale_contract_india_tree_link').id, 'tree'), (self.env.ref('sd_india_traffic.sale_contract_india_form_link').id, 'form')],
                    'res_model': 'sale.contract.india',
                    'context': {},
                    'domain': [('id', 'in', self.sale_contract_ids.ids)],
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                }
        if not self.sale_contract_ids:
            sale_contract = self.env['sale.contract.india'].search([
                ('p_date', '>=', self.date_from),
                ('p_date', '<=', self.date_to)
            ])
            return {
                'name': _('PSC to PC Linked'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(self.env.ref('sd_india_traffic.sale_contract_india_tree_link').id, 'tree'), (self.env.ref('sd_india_traffic.sale_contract_india_form_link').id, 'form')],
                'res_model': 'sale.contract.india',
                'context': {},
                'domain': [('id', 'in', sale_contract.ids)],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }