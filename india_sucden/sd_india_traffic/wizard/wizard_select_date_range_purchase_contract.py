# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardSelectDateRangePurchaseContract(models.TransientModel):
    _name = "wizard.select.date.range.purchase.contract"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    def action_search(self):
        sale_contract_india = self.env['sale.contract.india'].browse(self.env.context.get('res_id'))
        if sale_contract_india.exists():
            item_group_id = sale_contract_india.item_group_id
            purchase_contract = self.env['purchase.contract'].search([
                ('product_id.item_group_id', '=', item_group_id.id),
                ('type', 'in', ['purchase', 'ptbf']),
                ('state', '!=', 'cancel'),
                ('open_qty', '>', 0),
                ('id', 'not in', sale_contract_india.line_purchase_ids.mapped('purchase_contract_id').ids),
                ('open_qty_check', '=', False),
                ('date_order', '>=', self.date_from),
                ('date_order', '<=', self.date_to),
            ])
            if sale_contract_india.state in ['draft', 'submit', 'approve']:
                for pur in purchase_contract:
                    # if pur.finished_qty - pur.total_allocated_qty <= 0:
                    #     continue
                    value = {
                        'purchase_contract_id': pur.id,
                        'sale_contract_id': sale_contract_india.id
                    }
                    psc_pc_link = self.env['psc.to.pc.linked'].create(value)
                    psc_pc_link.onchange_purchase_contract_id()