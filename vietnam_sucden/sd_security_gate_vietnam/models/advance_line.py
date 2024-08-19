# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class AdvanceLine(models.Model):
    _name = 'advance.line'

    request_id = fields.Many2one('request.payment')
    request_payment_id = fields.Many2one('request.payment', string='Request Payment')
    advance_qty = fields.Integer(string='Advance Quantity', related='request_payment_id.quantity_advance', store=True)
    fixed_quantity = fields.Integer(string='Fixed Quantity', compute='compute_fixed_qty', store=True)
    remain_qty = fields.Integer(string='Remain Qty Advance', compute='compute_remain_qty', store=True)
    quantity_fix = fields.Integer(string='Quantity Fix')

    @api.depends('request_payment_id')
    def compute_fixed_qty(self):
        for rec in self:
            fixed_quantity = 0
            if self.env.context.get('seq'):
                request_fixation_advance_current_contract = self.env['request.payment'].search([
                    ('purchase_contract_id', '=', self.env.context.get('purchase_contract_id')),
                    ('name', '<', int(self.env.context.get('seq'))),
                    ('type_of_ptbf_payment', '=', 'fixation_advance')
                ])
                if request_fixation_advance_current_contract:
                    advance_line_current = request_fixation_advance_current_contract.mapped('fixation_advance_line_ids').filtered(
                        lambda x: x.request_payment_id.id == rec.request_payment_id.id)
                    if advance_line_current:
                        fixed_quantity = sum(advance_line_current.mapped('quantity_fix'))

                request_fixation_advance_other_contract = self.env['request.payment'].search([
                    ('purchase_contract_id', '!=', self.env.context.get('purchase_contract_id')),
                    ('type_of_ptbf_payment', '=', 'fixation_advance'),
                    ('purchase_contract_id.type', '=', 'ptbf')
                ])
                if request_fixation_advance_other_contract:
                    advance_line_other = request_fixation_advance_other_contract.mapped('fixation_advance_line_ids').filtered(
                        lambda x: x.request_payment_id.id == rec.request_payment_id.id)
                    if advance_line_other:
                        fixed_quantity = sum(advance_line_other.mapped('quantity_fix'))
                rec.fixed_quantity = fixed_quantity
            else:
                if isinstance(rec.request_id.id, int):
                    request_payment = rec.request_id
                    request_fixation_advance_current_contract = self.env['request.payment'].search([
                        ('purchase_contract_id', '=', request_payment.purchase_contract_id.id),
                        ('name', '<', int(request_payment.name)),
                        ('type_of_ptbf_payment', '=', 'fixation_advance'),
                        ('id', '!=', request_payment.id)
                    ])
                    request_fixation_advance_other_contract = self.env['request.payment'].search([
                        ('purchase_contract_id', '!=', request_payment.purchase_contract_id.id),
                        ('type_of_ptbf_payment', '=', 'fixation_advance'),
                        ('purchase_contract_id.type', '=', 'ptbf')
                    ])
                    if request_fixation_advance_current_contract:
                        advance_line_current = request_fixation_advance_current_contract.mapped(
                            'fixation_advance_line_ids').filtered(
                            lambda x: x.request_payment_id.id == rec.request_payment_id.id)
                        if advance_line_current:
                            fixed_quantity = sum(advance_line_current.mapped('quantity_fix'))

                    if request_fixation_advance_other_contract:
                        advance_line_other = request_fixation_advance_other_contract.mapped(
                            'fixation_advance_line_ids').filtered(
                            lambda x: x.request_payment_id.id == rec.request_payment_id.id)
                        if advance_line_other:
                            fixed_quantity = sum(advance_line_other.mapped('quantity_fix'))
                rec.fixed_quantity = fixed_quantity

    @api.depends('quantity_fix', 'fixed_quantity', 'advance_qty')
    def compute_remain_qty(self):
        for rec in self:
            rec.remain_qty = rec.advance_qty - rec.fixed_quantity - rec.quantity_fix
            if rec.remain_qty < 0:
                raise UserError(_("Remain Quantity cannot < 0!!!"))