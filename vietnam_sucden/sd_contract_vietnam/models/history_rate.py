# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class HistoryRate(models.Model):
    _inherit = "history.rate"

    qty_invoice = fields.Float(string="Qty Invoice")
    remain_qty_invoice = fields.Float(string="Remain Qty Invoice",
                                      compute='compute_remain_qty_invoice', store=True)
    invoice_ids = fields.One2many('account.move', 'history_rate_id', string='Invoice')

    @api.depends('invoice_ids', 'invoice_ids.state', 'qty_receive', 'qty_price')
    def compute_remain_qty_invoice(self):
        for rec in self:
            rec.remain_qty_invoice = rec.qty_receive - sum(rec.invoice_ids.filtered(lambda x: x.state != 'cancel').mapped('total_quantity'))

    def name_get(self):
        result = []
        for rec in self:
            if rec.history_id and rec.date_receive:
                name = "No " + rec.history_id.no + " Date: " + rec.date_receive.strftime(DATE_FORMAT)
                result.append((rec.id, name))
        return result