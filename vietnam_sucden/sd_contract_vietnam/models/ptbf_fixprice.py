# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class PtbfFixPrice(models.Model):
    _inherit = "ptbf.fixprice"

    contract_p_id = fields.Many2one('s.contract', string="PNo")

    qty_invoice = fields.Float(string="Qty Invoice")
    remain_qty_invoice = fields.Float(string="Remain Qty Invoice", compute='_compute_remain_qty_invoice', store=True)
    invoice_ids = fields.One2many('account.move', 'ptbf_fixprice_id', string='Invoice')

    @api.depends('history_rate_ids', 'history_rate_ids.invoice_ids', 'history_rate_ids.remain_qty_invoice',
                 'history_rate_ids.invoice_ids.state', 'quantity')
    def _compute_remain_qty_invoice(self):
        for record in self:
            record.remain_qty_invoice = sum(record.history_rate_ids.mapped('remain_qty_invoice'))