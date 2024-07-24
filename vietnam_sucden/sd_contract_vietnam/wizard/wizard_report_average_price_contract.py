# -*- encoding: utf-8 -*-
from odoo import fields, models, api, _
import base64
import xlrd
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class ReportAveragePrice(models.TransientModel):
    _name = 'report.average.price'

    partner_id = fields.Many2one('res.partner', string='Vendor')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')

    def button_generate(self):
        domain = []
        self.env.cr.execute("""Delete from average_price_contract""")
        if self.partner_id:
            domain += [('partner_id', '=', self.partner_id.id)]
        if self.date_to and not self.date_from:
            raise UserError(_("You need input both From-To Date!!!"))
        if not self.date_to and self.date_from:
            raise UserError(_("You need input both From-To Date!!!"))
        if self.date_to and self.date_from:
            domain += [('date_order', '>=', self.date_from), ('date_order', '<=', self.date_to)]
        domain += [('type', '=', 'purchase'), ('qty_unreceived', '>', 0), ('state', 'not in', ['done', 'cancel'])]
        purchase_contract = self.env['purchase.contract'].search(domain)
        if purchase_contract:
            for part in purchase_contract.mapped('partner_id'):
                total_value = 0
                total_qty = 0
                for line in purchase_contract.filtered(lambda x: x.partner_id.id == part.id):
                    total_value += line.qty_unreceived * line.relation_price_unit
                    total_qty += line.qty_unreceived
                val = {
                    'partner_id': part.id,
                    'total_un_receive': total_qty,
                    'average_price': total_value / total_qty
                }
                self.env['average.price.contract'].create(val)
        action = self.env.ref('sd_contract_vietnam.action_average_price_contract')
        result = action.sudo().read()[0]
        res = self.env.ref('sd_contract_vietnam.average_price_contract_tree', False)
        result['views'] = [(res and res.id or False, 'tree')]
        return result



