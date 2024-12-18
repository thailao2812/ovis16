# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardSelectDateRangeSContract(models.TransientModel):
    _name = "wizard.select.date.range.s.contract"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    def action_search(self):
        sale_contract_india = self.env['sale.contract.india'].browse(self.env.context.get('res_id'))
        if sale_contract_india.exists():
            item_group_id = sale_contract_india.item_group_id
            s_contract = self.env['purchase.contract'].search([
                ('product_id.item_group_id', '=', item_group_id.id),
                ('type', 'in', ['export', 'local']),
                ('state', '!=', 'cancel'),
                ('open_qty', '>', 0),
                ('id', 'not in', sale_contract_india.sale_contract_factory_ids.mapped('s_contract').ids),
                ('date', '>=', self.date_from),
                ('date', '<=', self.date_to),
            ])
            for sc in s_contract:
                value = {
                    's_contract': sc.id,
                    'sale_contract_id': sale_contract_india.id
                }
                psc_sc_link = self.env['psc.to.sc.linked'].create(value)
                psc_sc_link.onchange_s_contract()