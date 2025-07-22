# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class AdjustmentSupplier(models.Model):
    _name = 'supplier.adjustment'
    _inherit = ['mail.thread']
    _order = 'id desc'

    name = fields.Char(string='Adjustment', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default='New')

    state = fields.Selection([
        ('draft', 'New'),
        ('validated', 'Validated'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected')
    ], string='Status', tracking=True,
       readonly=True, copy=False, index=True, default='draft')

    contract_type = fields.Selection([
        ('regular', 'Regular Contract'),
        ('consignment', 'Consignment Contract')
    ], string='Contract Type', default='consignment', required=True)

    contract_ids = fields.Many2many(
        'purchase.contract',
        'supplier_adjustment_contract_rel',
        'adjustment_id', 'contract_id',
        string = 'Contracts',
        domain="[('id', 'in', available_contract_ids)]")
    picking_ids = fields.Many2many('stock.picking', string='Pickings')
    request_payment_ids = fields.Many2many('request.payment', string='Request Payments')
    npe_contract_ids = fields.Many2many(
        'purchase.contract',
        'supplier_adjustment_npe_contract_rel',
        'adjustment_id', 'contract_id',
        string='NPE Contracts')

    allocation_ids = fields.Many2many('stock.allocation', string='Stock Allocations')

    available_contract_ids = fields.Many2many(
        'purchase.contract', compute='_compute_available_contracts', string='Available Contracts')

    current_supplier_id = fields.Many2one(
        'res.partner', string='Current Supplier', readonly=True, tracking=True)

    new_supplier_id = fields.Many2one(
        'res.partner', string='New Supplier', required=True)

    @api.depends('contract_type')
    def _compute_available_contracts(self):
        Contract = self.env['purchase.contract']
        for rec in self:
            if rec.contract_type == 'regular':
                domain = [('type', '=', 'purchase')]
            else:
                domain = [('type', '=', 'consign')]
            rec.available_contract_ids = Contract.search(domain).ids

    @api.onchange('contract_ids')
    def _onchange_contract_ids(self):
        if self.contract_ids:
            suppliers = self.contract_ids.mapped('partner_id')
            if len(suppliers) > 1:
                raise UserError(_("All selected contracts must belong to the same supplier!"))
            self.current_supplier_id = suppliers[0].id
        else:
            self.current_supplier_id = False
        for rec in self:
            allocations = rec.contract_ids.mapped('stock_allocation_ids')
            pickings = allocations.mapped('picking_id')
            rec.picking_ids = pickings or False
            rec.allocation_ids = allocations or False

        req_payments = self.env['request.payment']
        npe_contracts = self.env['purchase.contract']
        for contract in self.contract_ids:
            req_payments |= contract.request_payment_ids
            npe_contracts |= contract.npe_contract_id
        self.request_payment_ids = req_payments
        self.npe_contract_ids = npe_contracts

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('supplier.adjustment') or 'New'

        result = super(AdjustmentSupplier,self).create(vals)
        return result

    def action_validate(self):
        for rec in self:
            if not rec.contract_ids or not rec.new_supplier_id:
                raise UserError(_("You need to select contracts and new supplier."))
            partners = rec.contract_ids.mapped('partner_id')
            if len(partners) > 1:
                raise UserError(_("All selected contracts must belong to the same supplier!"))
            rec.contract_ids.write({'partner_id': rec.new_supplier_id.id})
            rec.contract_ids.write({'estate_name': rec.new_supplier_id.estate_name})
            if rec.contract_ids.contract_line:
                for line in rec.contract_ids.contract_line:
                    line.write({'partner_id': rec.new_supplier_id.id})
            if rec.contract_ids.psc_to_pc_linked_ids:
                for psc_to_pc_linked in rec.contract_ids.psc_to_pc_linked_ids:
                    psc_to_pc_linked.write({'partner_id': rec.new_supplier_id.id})

            if rec.picking_ids:
                for picking in rec.picking_ids:
                    picking.write({'partner_id': rec.new_supplier_id.id})
                    if picking.move_line_ids:
                        for move_line in picking.move_line_ids:
                            move_line.write({'partner_id': rec.new_supplier_id.id if move_line.partner_id != False else False})
                    if picking.move_line_ids_without_package:
                        for line in picking.move_line_ids_without_package:
                            line.write({'partner_id': rec.new_supplier_id.id if line.partner_id != False else False})

            if rec.request_payment_ids:
                for request_payment in rec.request_payment_ids:
                    request_payment.write({'partner_id': rec.new_supplier_id.id})
                    request_payment.write({'partner_bank_id': rec.new_supplier_id.bank_ids[0].id})
                    request_payment.write({'related_holder': rec.new_supplier_id.bank_ids[0].related_holder})
                    request_payment.write({'account_no': rec.new_supplier_id.bank_ids[0].acc_number})
                    request_payment.write({'bank_id': rec.new_supplier_id.bank_ids[0].bank_id.id})
                    request_payment.write({'chinhanh': rec.new_supplier_id.bank_ids[0].bank_id.bic})
                    request_payment.write({'branch': rec.new_supplier_id.bank_ids[0].branch})
                    for line in request_payment.request_payment_ids:
                        line.write({'partner_id': rec.new_supplier_id.id})
            if rec.allocation_ids:
                for allocation in rec.allocation_ids:
                    allocation.write({'partner_id': rec.new_supplier_id.id})
            if rec.npe_contract_ids:
                for npe_contract in rec.npe_contract_ids:
                    npe_contract.write({'partner_id': rec.new_supplier_id.id})
                    npe_contract.write({'estate_name': rec.new_supplier_id.estate_name})

            rec.state = 'validated'

    def action_approved(self):
        self.state = 'approved'

    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        for rec in self:
            rec.contract_ids.write({'partner_id': rec.current_supplier_id.id})
            rec.contract_ids.write({'estate_name': rec.current_supplier_id.estate_name})
            if rec.contract_ids.contract_line:
                for line in rec.contract_ids.contract_line:
                    line.write({'partner_id': rec.current_supplier_id.id})
            if rec.contract_ids.psc_to_pc_linked_ids:
                for psc_to_pc_linked in rec.contract_ids.psc_to_pc_linked_ids:
                    psc_to_pc_linked.write({'partner_id': rec.current_supplier_id.id})

            if rec.picking_ids:
                for picking in rec.picking_ids:
                    picking.write({'partner_id': rec.current_supplier_id.id})
                    if picking.move_line_ids:
                        for move_line in picking.move_line_ids:
                            move_line.write({'partner_id': rec.current_supplier_id.id if move_line.partner_id != False else False})
                    if picking.move_line_ids_without_package:
                        for line in picking.move_line_ids_without_package:
                            line.write({'partner_id': rec.current_supplier_id.id if line.partner_id != False else False})

            if rec.request_payment_ids:
                for request_payment in rec.request_payment_ids:
                    request_payment.write({'partner_id': rec.current_supplier_id.id})
                    request_payment.write({'partner_bank_id': rec.current_supplier_id.bank_ids[0].id})
                    request_payment.write({'related_holder': rec.current_supplier_id.bank_ids[0].related_holder})
                    request_payment.write({'account_no': rec.current_supplier_id.bank_ids[0].acc_number})
                    request_payment.write({'bank_id': rec.current_supplier_id.bank_ids[0].bank_id.id})
                    request_payment.write({'chinhanh': rec.current_supplier_id.bank_ids[0].bank_id.bic})
                    request_payment.write({'branch': rec.current_supplier_id.bank_ids[0].branch})
                    for line in request_payment.request_payment_ids:
                        line.write({'partner_id': rec.current_supplier_id.id})
            if rec.allocation_ids:
                for allocation in rec.allocation_ids:
                    allocation.write({'partner_id': rec.current_supplier_id.id})
            if rec.npe_contract_ids:
                for npe_contract in rec.npe_contract_ids:
                    npe_contract.write({'partner_id': rec.current_supplier_id.id})
                    npe_contract.write({'estate_name': rec.current_supplier_id.estate_name})

            rec.state = 'draft'

    def action_cancel(self):
        self.action_draft()
        self.state = 'cancel'

    def action_reject(self):
        self.action_draft()
        self.state = 'rejected'