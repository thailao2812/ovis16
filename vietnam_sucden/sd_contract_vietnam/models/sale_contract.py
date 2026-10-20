# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class SaleContract(models.Model):
    _inherit = "sale.contract"

    total_real_qty = fields.Float(string="Total Real Qty", compute='_compute_total_real_qty', store=True)

    @api.depends('detail_ids', 'state', 'detail_ids.allocated_qty', 'detail_ids.state')
    def _compute_total_real_qty(self):
        for rec in self:
            rec.total_real_qty = sum(rec.detail_ids.mapped('allocated_qty'))