# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    fob_management_id = fields.Many2one('fob.management.india', string='FOB Number')
    outturn = fields.Float(string='Outturn %')
    differential_india = fields.Float(string='Differential')
    state_fob = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit')
    ], string='State', default='draft')
    psc_to_pc_linked_ids = fields.One2many('psc.to.pc.linked', 'purchase_contract_id', string='PSC to PC Linked', ondelete='cascade')
    open_qty = fields.Float(string='Open Qty', compute='_compute_open_qty', store=True)
    finished_qty = fields.Float(string='Finished Qty/PC', compute='_compute_finished_qty', store=True)
    finished_receive_qty = fields.Float(string='Finished Qty/Actual Qty', compute='_compute_finished_qty', store=True)
    total_allocated_qty = fields.Float(string='Total Allocated', compute='_compute_allocated_qty', store=True)
    open_qty_check = fields.Boolean(string='Hide Allocation')
    remark_contract = fields.Char(string='Remarks')

    @api.depends('psc_to_pc_linked_ids', 'psc_to_pc_linked_ids.current_allocated', 'psc_to_pc_linked_ids.state')
    def _compute_allocated_qty(self):
        for record in self:
            record.total_allocated_qty = sum(i.current_allocated for i in record.psc_to_pc_linked_ids.filtered(
                lambda x: x.state == 'approve_allocation'))

    @api.depends('total_qty', 'outturn', 'qty_received')
    def _compute_finished_qty(self):
        for record in self:
            record.finished_receive_qty = record.qty_received * (record.outturn/100)
            record.finished_qty = record.total_qty * (record.outturn/100)

    @api.depends('psc_to_pc_linked_ids', 'finished_qty', 'total_qty', 'total_allocated_qty',
                 'psc_to_pc_linked_ids.state')
    def _compute_open_qty(self):
        for record in self:
            currency_allocation = record.total_allocated_qty
            record.open_qty = record.finished_qty - currency_allocation

    def button_submit_fob_link(self):
        for record in self:
            if not record.fob_management_id:
                raise UserError(_("You have to select FOB Number!"))
            record.state_fob = 'submit'

    def button_reset_submit_fob_link(self):
        for record in self:
            record.state_fob = 'draft'

    @api.onchange('certificate_id')
    def onchange_certificate_id(self):
        for rec in self:
            if rec.certificate_id:
                line_premium = rec.certificate_id.purchase_premium_line.filtered(
                    lambda x: x.item_group_id.id == rec.product_id.item_group_id.id)
                if line_premium:
                    rec.premium = line_premium.purchase_premium
                else:
                    rec.premium = 0
            else:
                rec.premium = 0

    @api.onchange('product_id')
    def onchange_for_product_id(self):
        for rec in self:
            if not rec.product_id:
                rec.certificate_id = False
