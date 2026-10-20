# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

class RequestMaterialLine(models.Model):
    _inherit = 'request.materials.line'

    picking_grn_id = fields.Many2one('stock.picking', string='GRN')
    domain_grn = fields.Many2many('stock.picking', string='GRNs', compute='_compute_grn_domain', store=True)

    @api.depends('stack_id')
    def _compute_grn_domain(self):
        for rec in self:
            if rec.stack_id:
                picking_ids = rec.stack_id.move_line_ids.mapped('picking_id').filtered(lambda x: x.picking_type_id.code in ['incoming', 'production_in'] and x.state == 'done')
                rec.domain_grn = picking_ids