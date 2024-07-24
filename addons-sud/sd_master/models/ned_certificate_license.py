# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class NedCertificateLicense(models.Model):
    _name = 'ned.certificate.license'
    _desrciption = 'Supplier Certificate License'
    _order = 'expired_date ASC'

    name = fields.Char('License Number', required=True)
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', required=True)
    partner_id = fields.Many2one('res.partner', string='Supplier', required=True)
    
    state = fields.Selection(
        [('draft', 'Draft'),
         ('active', 'Active'),
         ('expired', 'Expired'),
         ('deactive', 'Deactive'),
         ('transfered', 'Transfered')],
        string="Status", default='draft')
    
    active = fields.Boolean('Active', default=True)
    certification_date = fields.Date('Date of Certification')
    expired_date = fields.Date('Expired Date', required=True)
    quota = fields.Float('Quota', digits=(12, 0), help="License Quota", required=True)
    initial_amount = fields.Float(
        string='Initial Amount', digits=(12, 0), default=0,
        help="License initial amount. This amount will be included in purchased amount for sales allocation")
    consumed_amount = fields.Float(
        string='Consumed', digits=(12, 0),
        help="Consumed amount by other parties")
    
    
    
    
    # available_amount = fields.Float(
    #     string='Available for Purchase', digits=(12, 0),
    #     help="Available amount for purchase bases on Quota",
    #     compute='_compute_available_amount')
    # purchase_contract_ids = fields.One2many('purchase.contract', 'license_id', string='Purchase Contracts')
    # stock_allocation_ids = fields.One2many('stock.allocation', 'license_id', string='GRN Allocations')
    # allocated_purchase_contract_ids = fields.One2many('purchase.contract',
    #                                                   compute='_compute_allocated_purchase_contract_ids')
    # s_contract_line_ids = fields.One2many('s.contract.line', 'license_id', string='S Contract Lines')
    # sales_allocation_ids = fields.One2many('s.contract.license.allocation', 'license_id',
    #                                        string='Sales Allocations')
    # purchased_amount = fields.Float('Purchased Amount', digits=(12, 0), store=True,
    #                                 compute='_compute_purchased_amount')
    
    def _compute_sales_amount(self):
        for license in self:
            license.sales_amount = 0.0
            
            
    sales_amount = fields.Float('Sales Amount', digits=(12, 0), store=True,
                                compute='_compute_sales_amount')
    # balance = fields.Float('Balance', digits=(12, 0), store=True, compute='_compute_balance')

    @api.onchange('initial_amount', 'consumed_amount')
    def onchange_initial_amount(self):
        if self.initial_amount:
            consumed = self.initial_amount + self.consumed_amount
            if consumed > self.quota:
                raise UserError('Initial amount and consumed amount must not exceed license quota')


    #lay bên Ned Vn
    # @api.depends('initial_amount', 'stock_allocation_ids.qty_allocation', 'stock_allocation_ids.state')
    # def _compute_purchased_amount(self):
    #     for license in self:
    #         stock_allocations = license.stock_allocation_ids.filtered(lambda sa: sa.state == 'approved')
    #         license.purchased_amount = sum(stock_allocations.mapped('qty_allocation'))
    #         license.purchased_amount += license.initial_amount

    # @api.depends('stock_allocation_ids.contract_id')
    # def _compute_allocated_purchase_contract_ids(self):
    #     for license in self:
    #         allocated_purchase_contract_ids = license.purchase_contract_ids.filtered(
    #             lambda contract: contract.type == 'purchase'
    #             or (contract.type == 'ptbf')
    #             or (contract.type == 'consign' and contract.qty_unfixed > 0)
    #         )
    #         license.allocated_purchase_contract_ids = allocated_purchase_contract_ids

    # @api.depends('sales_allocation_ids', 'sales_allocation_ids.allocation_qty')
    # def _compute_sales_amount(self):
    #     for license in self:
    #         sales_allocations = license.sales_allocation_ids
    #         license.sales_amount = sum(sales_allocations.mapped('allocation_qty'))

    @api.depends('quota', 'consumed_amount', 'purchased_amount')
    def _compute_available_amount(self):
        for license in self:
            license.available_amount = license.quota \
                - license.consumed_amount - license.purchased_amount
    
    # lay ben ned vnvn
    # @api.depends('purchased_amount', 'sales_amount')
    # def _compute_balance(self):
    #     for license in self:
    #         license.balance = license.purchased_amount - license.sales_amount
    #     return True

    def validate_license(self):
        """
        Check license information and change state to active
        """
        if not self.quota > 0:
            raise UserError("License's quota must be stricly positive.")
        self.state = 'active'
        return True

    def reset_draft(self):
        self.state = 'draft'
        return True

    @api.model
    def update_license_status(self):
        today = fields.Date.context_today(self)
        valid_balance_expired_licenses = self.search(
            [('state', '=', 'active'), ('expired_date', '<', today), ('balance', '>', 0)])
        valid_balance_expired_licenses.write({'state': 'expired'})

        zero_balance_expired_licenses = self.search(
            [('state', 'in', ['active', 'expired']), ('expired_date', '<', today), ('balance', '<=', 0)])
        zero_balance_expired_licenses.write({'state': 'deactive'})
##########################################################################################


    # def copy_license(self):
    #     idd = []
    #     for re in self:
    #         idd.append(re.copy({
    #             'name': 'Extended_%s' % re.name,
    #             'initial_amount': re.balance,
    #             'parent_id': re.id,
    #             'balance': re.balance
    #         }))
    #         re.write({
    #             'state': 'transfered'
    #         })
    #     return {
    #         'name': 'Certificate License',
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'domain': [('id', 'in', [i.id for i in idd])],
    #         'res_model': 'ned.certificate.license',
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'res_id': idd[0].id,
    #     }

    @api.depends('initial_amount', 'stock_allocation_ids.qty_allocation', 'stock_allocation_ids.state')
    def _compute_purchased_amount(self):
        for license in self:
            if license.allocated_purchase_contract_ids:
                stock_allocations = license.stock_allocation_ids.filtered(lambda sa: sa.state == 'approved')
                if stock_allocations:
                    license.purchased_amount = sum(stock_allocations.mapped('qty_allocation'))
                else:
                    license.purchased_amount = 0
                # license.purchased_amount += license.initial_amount
            else:
                license.purchased_amount = 0

    # @api.depends('initial_amount', 'stock_allocation_ids.qty_allocation', 'stock_allocation_ids.state')
    # def _compute_purchased_amount(self):
    #     for license in self:
    #         stock_allocations = license.stock_allocation_ids.filtered(lambda sa: sa.state == 'approved')
    #         license.purchased_amount = sum(stock_allocations.mapped('qty_allocation'))
#            license.purchased_amount += license.initial_amount

    @api.depends('purchased_amount', 'sales_amount')
    def _compute_balance(self):
        for license in self:
            license.balance = license.purchased_amount - license.sales_amount + license.initial_amount
        return True

    def action_deactive(self):
        for record in self:
            if record.state in ['expired']:
                record.write({
                    'state': 'deactive'
                })
            else:
                raise UserError(_("The certificate license %s need to be in state "
                                  "Expired to change to Deactive state!") % record.name)
