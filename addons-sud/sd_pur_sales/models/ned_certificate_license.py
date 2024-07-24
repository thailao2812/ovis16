# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

DATE_FORMAT = "%Y-%m-%d"
import time
import datetime
from datetime import date
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class NedCertificateLicense(models.Model):
    _inherit = 'ned.certificate.license'
    _desrciption = 'Supplier Certificate License'
    _order = 'expired_date ASC'
    
    type = fields.Selection([('sucden_coffee_license', 'Sucden Coffee License'),
                               ('independent_license', '3rd Party License'),
                               ], string='Type') # Guatemala

    name = fields.Char('License Number', required=True)
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', required=True)
    partner_id = fields.Many2one('res.partner', string='Supplier', required=True,
                                 domain="[('is_supplier_coffee','=',True)]")
    state = fields.Selection(
        [('draft', 'Draft'),
         ('active', 'Active'),
         ('expired', 'Expired'),
         ('deactive', 'Deactive')],
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
    available_amount = fields.Float(
        string='Available for Purchase', digits=(12, 0),
        help="Available amount for purchase bases on Quota",
        compute='_compute_available_amount', store =True)
    purchase_contract_ids = fields.One2many('purchase.contract', 'license_id', string='Purchase Contracts')
    stock_allocation_ids = fields.One2many('stock.allocation', 'license_id', string='GRN Allocations')
    allocated_purchase_contract_ids = fields.One2many('purchase.contract',
                                                      compute='_compute_allocated_purchase_contract_ids')
    s_contract_line_ids = fields.One2many('s.contract.line', 'license_id', string='S Contract Lines')
    
    sales_allocation_ids = fields.One2many('s.contract.license.allocation', 'license_id',
                                           string='Sales Allocations')
    
    purchased_amount = fields.Float('Purchased Qty', digits=(12, 0), store=True,
                                    compute='_compute_purchased_amount')
    sales_amount = fields.Float('Sales Qty', digits=(12, 0), store=True,
                                compute='_compute_sales_amount')
    
    
    balance = fields.Float('Balance', digits=(12, 0), store=True, compute='_compute_balance')
    
    parent_id = fields.Many2one('ned.certificate.license', string='From Certificate')
    
    # Initial Amount
    g1_s16_initial = fields.Float(string='Initial Amount G1-S16', digits=(12, 0))
    g1_s18_initial = fields.Float(string='Initial Amount G1-S18', digits=(12, 0))
    g2_initial = fields.Float(string='Initial Amount G2', digits=(12, 0))
    
    count_date_expired = fields.Integer(string='Calculate Date Expired')
    crop_id = fields.Many2one('ned.crop', string='Crop')
    
    
    lock_purchase = fields.Boolean(string="Lock Purchase", copy = False)
    
    def btt_lock_purchase(self):
        self.lock_purchase = True
    



    @api.model
    def cron_update_count_date_expired(self):
        for record in self.search([]):
            asa = date.today()
            record.count_date_expired = (record.expired_date - date.today()).days
                                        
            
    @api.onchange('initial_amount', 'consumed_amount')
    def onchange_initial_amount(self):
        if self.initial_amount:
            consumed = self.initial_amount + self.consumed_amount
            if consumed > self.quota:
                raise UserError('Initial amount and consumed amount must not exceed license quota')

    @api.depends('stock_allocation_ids.qty_allocation', 'stock_allocation_ids.state',
                 'allocated_purchase_contract_ids.qty_unreceived', 'g1_s16_initial', 'g1_s18_initial', 'g2_initial')
    def _compute_purchased_amount(self):
        for license in self:
            if license.allocated_purchase_contract_ids:
                license.faq_tobe_received = sum(license.allocated_purchase_contract_ids.filtered(
                    lambda x: x.grade_id.code == 'FAQ').mapped('qty_unreceived'))
                license.g1_s18_tobe_received = sum(license.allocated_purchase_contract_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S18').mapped('qty_unreceived'))
                license.g1_s16_tobe_received = sum(license.allocated_purchase_contract_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S16').mapped('qty_unreceived'))
                license.g2_tobe_received = sum(license.allocated_purchase_contract_ids.filtered(
                    lambda x: x.grade_id.code == 'G2').mapped('qty_unreceived'))
                stock_allocations = license.stock_allocation_ids.filtered(lambda sa: sa.state == 'approved')
                if stock_allocations:
                    license.purchased_amount = sum(stock_allocations.mapped('qty_allocation'))
                    license.faq_purchase = sum(
                        stock_allocations.filtered(lambda x: x.grade_id.code == 'FAQ').mapped('qty_allocation'))
                    license.g1_s18_purchase = sum(
                        stock_allocations.filtered(lambda x: x.grade_id.code == 'G1-S18').mapped('qty_allocation'))
                    license.g1_s16_purchase = sum(
                        stock_allocations.filtered(lambda x: x.grade_id.code == 'G1-S16').mapped('qty_allocation'))
                    license.g2_purchase = sum(
                        stock_allocations.filtered(lambda x: x.grade_id.code == 'G2').mapped('qty_allocation'))
                else:
                    license.purchased_amount = 0
                    license.faq_purchase = 0
                    license.g1_s18_purchase = 0
                    license.g1_s16_purchase = 0
                    license.g2_purchase = 0
            else:
                # Purchase amount
                license.purchased_amount = 0
                license.faq_purchase = 0
                license.g1_s18_purchase = 0
                license.g1_s16_purchase = 0
                license.g2_purchase = 0
                # To be received amount
                license.faq_tobe_received = 0
                license.g1_s18_tobe_received = 0
                license.g1_s16_tobe_received = 0
                license.g2_tobe_received = 0
            license.g1_s18_purchase += license.g1_s18_initial
            license.g1_s16_purchase += license.g1_s16_initial
            license.g2_purchase += license.g2_initial
            

    @api.depends('stock_allocation_ids.contract_id')
    def _compute_allocated_purchase_contract_ids(self):
        for license in self:
            allocated_purchase_contract_ids = license.purchase_contract_ids.filtered(
                lambda contract: contract.type == 'purchase'
                or (contract.type == 'ptbf')
                or (contract.type == 'consign' and contract.qty_unfixed > 0)
            )
            license.allocated_purchase_contract_ids = allocated_purchase_contract_ids

    @api.depends('sales_allocation_ids', 'sales_allocation_ids.allocation_qty',
                 'shipping_instruction_allocation_ids', 'shipping_instruction_allocation_ids.allocation_qty')
    def _compute_sales_amount(self):
        for license in self:
            sales_allocations = license.sales_allocation_ids
            shipping_allocation = license.shipping_instruction_allocation_ids
            license.sales_amount = sum(sales_allocations.mapped('allocation_qty')) + sum(shipping_allocation.mapped('allocation_qty'))
            

    @api.depends('quota', 'consumed_amount', 'purchased_amount', 'allocated_purchase_contract_ids', 'allocated_purchase_contract_ids.total_qty')
    def _compute_available_amount(self):
        for license in self:
            license.available_amount = license.quota \
                - license.consumed_amount - sum(license.allocated_purchase_contract_ids.mapped('total_qty'))
    
    
    #SUCDEN VN ####################
    @api.depends('purchased_amount', 'sales_amount')
    def _compute_balance(self):
        for license in self:
            license.balance = license.purchased_amount - license.sales_amount + license.initial_amount
        return True

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
        valid_balance_expired_licenses.write({
            'state': 'expired',
            'lock_purchase': True
        })

        zero_balance_expired_licenses = self.search(
            [('state', 'in', ['active', 'expired']), ('expired_date', '<', today), ('balance', '<=', 0)])
        zero_balance_expired_licenses.write({'state': 'deactive'})
    
    
    
    ###################### NED VN ############################################################################
    def expire_cert(self):
        return self.write({'state': 'expired'})
    
    parent_id = fields.Many2one('ned.certificate.license', string='From Certificate')
    state = fields.Selection(
        [('draft', 'Draft'),
         ('active', 'Active'),
         ('expired', 'Expired'),
         ('deactive', 'Deactive'),
         ('transfered', 'Transfered')],
        string="Status", default='draft')

    def copy_license(self):
        idd = []
        for re in self:
            idd.append(re.copy({
                'name': 'Extended_%s' % re.name,
                'initial_amount': re.balance,
                'parent_id': re.id,
                'balance': re.balance
            }))
            re.write({
                'state': 'transfered'
            })
        return {
            'name': 'Certificate License',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', [i.id for i in idd])],
            'res_model': 'ned.certificate.license',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': idd[0].id,
        }
    
    
    shipping_instruction_allocation_ids = fields.One2many('shipping.instruction.license.allocation', 'license_id',
                                                          string='Shipping Instruction Allocations')
    remark_cert = fields.Char(string='Remark')
    # Purchase

    # 30/11 Thai Lao
    allocated_p_contract_ids = fields.One2many('s.contract', 'license_id')

    # 30/11 Thai lao
    type_license = fields.Selection([
        ('non_bonded', 'Non-Bonded'),
        ('bonded', 'Bonded')
    ], string='Type License', default="non_bonded")
    
    faq_purchase = fields.Float(string='FAQ Purchase', compute='_compute_purchased_amount', store=True)
    g1_s18_purchase = fields.Float(string='G1-S18 Purchase', compute='_compute_purchased_amount', store=True)
    g1_s16_purchase = fields.Float(string='G1-S16 Purchase', compute='_compute_purchased_amount', store=True)
    g2_purchase = fields.Float(string='G2 Purchase', compute='_compute_purchased_amount', store=True)
    
    @api.depends('shipping_instruction_allocation_ids.allocation_qty', 'shipping_instruction_allocation_ids',
                 'sales_allocation_ids', 'sales_allocation_ids.allocation_qty',
                 'shipping_instruction_allocation_ids.state', 'g1_s16_initial', 'g1_s18_initial', 'g2_initial')
    def _compute_total_allocated_amount(self):
        for record in self:
            faq_allocated = g1_s18_allocated = g1_s16_allocated = g2_allocated = 0
            faq_allocated_out = g1_s18_allocated_out = g1_s16_allocated_out = g2_allocated_out = 0
            if record.shipping_instruction_allocation_ids:
                # faq allocated and allocated out
                faq_allocated = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'FAQ').mapped('allocation_qty'))
                faq_allocated_out = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'FAQ' and x.state == 'done').mapped('allocation_qty'))

                # g1 s18 allocated and allocated out
                g1_s18_allocated = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S18').mapped('allocation_qty'))
                g1_s18_allocated_out = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S18' and x.state == 'done').mapped('allocation_qty'))

                # g1 s16 allocated and allocated out
                g1_s16_allocated = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S16').mapped('allocation_qty'))
                g1_s16_allocated_out = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S16' and x.state == 'done').mapped('allocation_qty'))

                # g2 allocated and allocated out
                g2_allocated = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G2').mapped('allocation_qty'))
                g2_allocated_out = sum(record.shipping_instruction_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G2' and x.state == 'done').mapped('allocation_qty'))

            if record.sales_allocation_ids:
                # doesn't have state => always is out
                faq_allocated += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'FAQ').mapped('allocation_qty'))
                faq_allocated_out += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'FAQ').mapped('allocation_qty'))

                g1_s18_allocated += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S18').mapped('allocation_qty'))
                g1_s18_allocated_out += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S18').mapped('allocation_qty'))

                g1_s16_allocated += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S16').mapped('allocation_qty'))
                g1_s16_allocated_out += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G1-S16').mapped('allocation_qty'))

                g2_allocated += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G2').mapped('allocation_qty'))
                g2_allocated_out += sum(record.sales_allocation_ids.filtered(
                    lambda x: x.grade_id.code == 'G2').mapped('allocation_qty'))

            # Allocated Total
            record.faq_allocated = faq_allocated
            record.g1_s18_allocated = g1_s18_allocated
            record.g1_s16_allocated = g1_s16_allocated
            record.g2_allocated = g2_allocated

            # FAQ Derivable
            faq_derivable = record.faq_purchase - record.faq_allocated
            record.faq_derivable = 0
            record.g1_s18_derivable = record.g1_s18_purchase + (faq_derivable * 25 / 100)
            record.g1_s16_derivable = record.g1_s16_purchase + (faq_derivable * 33 / 100)
            record.g2_derivable = record.g2_purchase + (faq_derivable * 40 / 100)

            # Allocated Out
            record.faq_allocated_out = faq_allocated_out
            record.g1_s18_allocated_out = g1_s18_allocated_out
            record.g1_s16_allocated_out = g1_s16_allocated_out
            record.g2_allocated_out = g2_allocated_out

            # Allocated not out
            record.faq_allocated_not_out = faq_allocated - faq_allocated_out
            record.g1_s18_allocated_not_out = g1_s18_allocated - g1_s18_allocated_out
            record.g1_s16_allocated_not_out = g1_s16_allocated - g1_s16_allocated_out
            record.g2_allocated_not_out = g2_allocated - g2_allocated_out

            # Not Allocated
            record.faq_unallocated = 0
            record.g1_s18_unallocated = record.g1_s18_derivable - g1_s18_allocated
            record.g1_s16_unallocated = record.g1_s16_derivable - g1_s16_allocated
            record.g2_unallocated = record.g2_derivable - g2_allocated

            # Balance
            record.faq_balance = 0
            record.g1_s18_balance = record.g1_s18_derivable - record.g1_s18_allocated_out
            record.g1_s16_balance = record.g1_s16_derivable - record.g1_s16_allocated_out
            record.g2_balance = record.g2_derivable - record.g2_allocated_out

            # Final Balance
            record.final_balance = record.faq_balance + record.g1_s18_balance + record.g1_s16_balance \
                                   + record.g2_balance

            # Position
            record.faq_position = record.faq_balance + record.faq_tobe_received
            record.g1_s18_position = record.g1_s18_balance + record.g1_s18_tobe_received
            record.g1_s16_position = record.g1_s16_balance + record.g1_s16_tobe_received
            record.g2_position = record.g2_balance + record.g2_tobe_received


    
    # Allocated total
    faq_allocated = fields.Float(string='FAQ Allocated', compute='_compute_total_allocated_amount', store=True)
    g1_s18_allocated = fields.Float(string='G1-S18 Allocated', compute='_compute_total_allocated_amount', store=True)
    g1_s16_allocated = fields.Float(string='G1-S16 Allocated', compute='_compute_total_allocated_amount', store=True)
    g2_allocated = fields.Float(string='G2 Allocated', compute='_compute_total_allocated_amount', store=True)
    
    
    # Allocated not out
    faq_allocated_not_out = fields.Float(string='FAQ Tobe Ship',
                                         compute='_compute_total_allocated_amount', store=True)
    
    g1_s18_allocated_not_out = fields.Float(string='G1-S18 Tobe Ship',
                                            compute='_compute_total_allocated_amount', store=True)
    g1_s16_allocated_not_out = fields.Float(string='G1-S16 Tobe Ship',
                                            compute='_compute_total_allocated_amount', store=True)
    g2_allocated_not_out = fields.Float(string='G2 Tobe Ship',
                                        compute='_compute_total_allocated_amount', store=True)

    # Allocated Out
    faq_allocated_out = fields.Float(string='FAQ Shipped',
                                     compute='_compute_total_allocated_amount', store=True)
    g1_s18_allocated_out = fields.Float(string='G1-S18 Shipped',
                                        compute='_compute_total_allocated_amount', store=True)
    g1_s16_allocated_out = fields.Float(string='G1-S16 Shipped',
                                        compute='_compute_total_allocated_amount', store=True)
    g2_allocated_out = fields.Float(string='G2 Shipped',
                                    compute='_compute_total_allocated_amount', store=True)

    # Not Allocated
    faq_unallocated = fields.Float(string='FAQ Un Allocate',
                                   compute='_compute_total_allocated_amount', store=True)
    g1_s18_unallocated = fields.Float(string='G1-S18 Un Allocate',
                                      compute='_compute_total_allocated_amount', store=True)
    g1_s16_unallocated = fields.Float(string='G1-S16 Un Allocate',
                                      compute='_compute_total_allocated_amount', store=True)
    g2_unallocated = fields.Float(string='G2 Un Allocate', compute='_compute_total_allocated_amount', store=True)

    # Balance
    faq_balance = fields.Float(string='FAQ Balance', compute='_compute_total_allocated_amount', store=True)
    g1_s18_balance = fields.Float(string='G1-S18 Balance', compute='_compute_total_allocated_amount', store=True)
    g1_s16_balance = fields.Float(string='G1-S16 Balance', compute='_compute_total_allocated_amount', store=True)
    g2_balance = fields.Float(string='G2 Balance', compute='_compute_total_allocated_amount', store=True)

    # FAQ Derivable
    faq_derivable = fields.Float(string='FAQ Derivable', compute='_compute_total_allocated_amount', store=True)
    g1_s18_derivable = fields.Float(string='G1-S18 Derivable', compute='_compute_total_allocated_amount', store=True)
    g1_s16_derivable = fields.Float(string='G1-S16 Derivable', compute='_compute_total_allocated_amount', store=True)
    g2_derivable = fields.Float(string='G2 Derivable', compute='_compute_total_allocated_amount', store=True)

    # Final balance
    final_balance = fields.Float(string='Final Balance', compute='_compute_total_allocated_amount', store=True)

    # Tobe Received
    faq_tobe_received = fields.Float(string='FAQ Tobe Receive', compute='_compute_purchased_amount', store=True)
    g1_s18_tobe_received = fields.Float(string='G1-S18 Tobe Receive',
                                        compute='_compute_purchased_amount', store=True)
    g1_s16_tobe_received = fields.Float(string='G1-S16 Tobe Receive',
                                        compute='_compute_purchased_amount', store=True)
    g2_tobe_received = fields.Float(string='G2 Tobe Receive', compute='_compute_purchased_amount', store=True)

    # Position
    faq_position = fields.Float(string='FAQ Position', compute='_compute_total_allocated_amount', store=True)
    g1_s18_position = fields.Float(string='G1-S18 Position', compute='_compute_total_allocated_amount', store=True)
    g1_s16_position = fields.Float(string='G1-S16 Position', compute='_compute_total_allocated_amount', store=True)
    g2_position = fields.Float(string='G2 Position', compute='_compute_total_allocated_amount', store=True)
    

   

