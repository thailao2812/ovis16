# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class PscToPcLinked(models.Model):
    _name = 'psc.to.pc.linked'

    sale_contract_id = fields.Many2one('sale.contract.india', ondelete='cascade')
    purchase_contract_id = fields.Many2one('purchase.contract', string='PC No.', ondelete='cascade')
    date_contract = fields.Date(string='PC Date')
    partner_id = fields.Many2one('res.partner', string='Vendor/Supplier Name')
    product_id = fields.Many2one('product.product', string='Item Name - Item Code')
    quantity = fields.Float(string='PC Qty.', compute='compute_pc_qty', store=True)
    receive_qty = fields.Float(string='Receive Qty.')
    outturn = fields.Float(string='Outturn %')
    finished_qty = fields.Float(string='Finished Qty/PC')
    finished_actual_qty = fields.Float(string='Finished Qty /Actual Qty')
    total_allocated = fields.Float(string='Allocated Qty')
    balance_qty = fields.Float(string='Balance Qty.', compute='_compute_transaction_qty', store=True)
    current_allocated = fields.Float(string='Current Allocation')
    state = fields.Selection(related='sale_contract_id.state', store=True)

    @api.depends('purchase_contract_id', 'purchase_contract_id.origin', 'purchase_contract_id.gross_qty', 'purchase_contract_id.total_qty')
    def compute_pc_qty(self):
        for rec in self:
            if rec.purchase_contract_id.origin:
                rec.quantity = rec.purchase_contract_id.gross_qty
            else:
                rec.quantity = rec.purchase_contract_id.total_qty

    @api.onchange('purchase_contract_id')
    def onchange_purchase_contract_id(self):
        if self.purchase_contract_id:
            self.date_contract = self.purchase_contract_id.date_order
            self.partner_id = self.purchase_contract_id.partner_id.id
            self.product_id = self.purchase_contract_id.product_id.id
            # self.quantity = self.purchase_contract_id.gross_qty if self.purchase_contract_id.origin else self.purchase_contract_id.total_qty
            self.receive_qty = self.purchase_contract_id.qty_received
            self.outturn = self.purchase_contract_id.outturn
            self.finished_qty = self.purchase_contract_id.finished_qty
            self.finished_actual_qty = self.purchase_contract_id.finished_receive_qty
            self.total_allocated = self.purchase_contract_id.total_allocated_qty

    @api.depends('finished_qty', 'total_allocated')
    def _compute_transaction_qty(self):
        for record in self:
            record.balance_qty = record.finished_qty - record.total_allocated

    @api.constrains('current_allocated')
    def _constrains_current_allocated(self):
        for obj in self:
            if obj.current_allocated > obj.balance_qty:
                raise UserError(_("Allocation cannot higher than balance quantity for %s") % obj.purchase_contract_id.name)


