# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardPSCtoSCLink(models.TransientModel):
    _name = "wizard.psc.to.sc.link"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    sale_contract_ids = fields.Many2many('sale.contract.india', string='Contract')

    def button_search(self):
        if self.date_to < self.date_from:
            raise UserError(_("You can not set date to < date from, please check again!!!"))
        if self.sale_contract_ids:
            for sale in self.sale_contract_ids:
                item_group_id = sale.item_group_id
                s_contract = self.env['s.contract'].search([
                    ('product_id.item_group_id', '=', item_group_id.id),
                    ('type', 'in', ['export', 'local']),
                    ('open_qty', '>', 0),
                    ('id', 'not in', self.sale_contract_ids.sale_contract_factory_ids.mapped('s_contract').ids),
                ])
                for sc in s_contract:
                    value = {
                        's_contract': sc.id,
                        'sale_contract_id': sale.id
                    }
                    psc_sc_link = self.env['psc.to.sc.linked'].create(value)
                    psc_sc_link.onchange_s_contract()
            return {
                'name': _('PSC to SC Linked'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'views': [(self.env.ref('sd_india_traffic.sale_contract_india_tree_psc_to_sc').id, 'tree'),
                          (self.env.ref('sd_india_traffic.sale_contract_india_form_psc_to_sc').id, 'form')],
                'res_model': 'sale.contract.india',
                'context': {},
                'domain': [('id', 'in', self.sale_contract_ids.ids)],
                'type': 'ir.actions.act_window',
                'target': 'current',
            }