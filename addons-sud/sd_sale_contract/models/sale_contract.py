# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

# -*- coding: utf-8 -*-
from datetime import datetime
from pytz import timezone
import datetime

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date





class SaleContract(models.Model):
    _name = "sale.contract"
    _inherit = ['mail.thread'] #SON Add
    
     # Thai 3/1/2023
    certificate_id_list = fields.Many2many('ned.certificate', 'sale_contract_certificate_ref', 'sale_contract_id', 'cert_id', string='Certificate List')
    license_certificate_ids = fields.Many2many('ned.certificate.license', 'license_certificate_sale_contract', 'sale_contract_id', 'license_id', string='License List')
    si = fields.Float(string='SI')
    sd = fields.Float(string='SD')
    
    def get_certificate(self):
        if self.certificate_id_list:
            return ', '.join(i.name for i in self.certificate_id_list)
        else:
            return ''
    
    def get_license(self):
        if self.license_certificate_ids:
            return ', '.join(i.name for i in self.license_certificate_ids)
        else:
            return ''
        
    
    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids
    
    @api.model
    def _default_currency_id(self):
        currency_ids = self.env['res.currency'].search([], limit=1)
        return currency_ids
    
    def button_dummy(self):
        return True
    
    @api.depends('contract_line.price_total')
    def _amount_all(self):
        for contract in self:
            amount_untaxed = amount_tax = 0.0
            for line in contract.contract_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            contract.update({
                'amount_untaxed': contract.currency_id and contract.currency_id.round(amount_untaxed) or amount_untaxed,
                'amount_tax': contract.currency_id and contract.currency_id.round(amount_tax) or amount_tax,
                'amount_total': amount_untaxed + amount_tax,
            })
            
    @api.depends('picking_ids')
    def _compute_pickings(self):
        for contract in self:
            pickings = self.env['stock.picking'] 
            contract.picking_count = len(contract.picking_ids)
            
    @api.depends('delivery_ids')
    def _compute_deliverys(self):
        for contract in self:
            deliverys = self.env['delivery.order']
            contract.delivery_count = len(contract.delivery_ids)
            
    @api.depends('invoice_ids')  
    def _compute_invoices(self):
        for contract in self:
            contract.invoice_count = len(contract.invoice_ids)
    
    name = fields.Char(string='Contract Reference', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default='New')
    company_id = fields.Many2one('res.company', string='Company', required=True, change_default=True, readonly=True, states={'draft': [('readonly', False)]}, default=lambda self: self.env['res.company']._company_default_get('sale.contract'))
    company_representative = fields.Many2one("res.partner", string="Company Representative", readonly=True, states={'draft': [('readonly', False)]})
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=_default_warehouse_id)
    picking_policy = fields.Selection([('direct', 'Deliver each product when available'), ('one', 'Deliver all products at once')],
        string='Shipping Policy', required=True, readonly=True, default='direct', states={'draft': [('readonly', False)]})

    state = fields.Selection([('draft', 'New'), ('approved', 'Approved'),('invoice','Invoice'), ('done', 'Done'), ('cancel', 'Cancelled')],
             string='Status', readonly=True, copy=False, index=True, default='draft')
    type = fields.Selection([('local', 'Local'), ('export', 'Export')], string='Type', required=True)
      
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)]}, required=False, change_default=True, index=True, )
    customer_representative = fields.Many2one('res.partner', string='Customer Representative', readonly=True, states={'draft': [('readonly', False)]}, index=True, )
    
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Invoice address for current Purchase order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=False, states={'draft': [('readonly', False)]})
    
    date = fields.Date(string='NVS Date', readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    validity_date = fields.Date(string='Validity Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    expiration_date = fields.Date(string='Expiration Date', readonly=True, states={'draft': [('readonly', False)]})
    
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=False, states={'draft': [('readonly', False)]}, default=_default_currency_id)
    exchange_rate = fields.Float(string="Exchange Rate", readonly=True, required=False, states={'draft': [('readonly', False)]}, default=1.0)
    
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    bank_id = fields.Many2one('res.bank', string='Bank', readonly=True, copy=False, states={'draft': [('readonly', False)]})
    acc_number = fields.Char(string='Account Number', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    contract_line = fields.One2many('sale.contract.line', 'contract_id', string='Contract Lines', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    note = fields.Text('Terms and conditions')
    origin = fields.Char(string='Source Document')
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', )
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all', )
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', )
    
    create_date = fields.Date(string='Creation Date', readonly=True, index=True, default=fields.Datetime.now)
    create_uid = fields.Many2one('res.users', 'Responsible', readonly=True , default=lambda self: self._uid)
    date_approve = fields.Date('Approval Date', readonly=True, copy=False)
    user_approve = fields.Many2one('res.users', string='User Approve', readonly=True)
    date_done = fields.Date('Date Done', readonly=True, copy=False)

    dispatch_mode = fields.Selection([('air', 'Air'), ('rail', 'Rail'), ('road', 'Road'), ('sea', 'Sea')], string='Dispatch Mode', readonly=True, states={'draft': [('readonly', False)]}, index=True)
    port_of_loading = fields.Many2one('delivery.place', string='Port Of Loading', copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True)
    port_of_discharge = fields.Many2one('delivery.place', string='Port of Destination', copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True)
    container_status = fields.Selection([('fcl/fcl', 'FCL/FCL'), ('lcl/fcl', 'LCL/FCL'), ('lcl/lcl', 'LCL/LCL')], string='Container Status', readonly=True, states={'draft': [('readonly', False)]}, index=True)
    weights = fields.Selection([('DW', 'Net Delivered Weights'), ('NLW', 'Net Landed Weights'),
                                ('NSW', 'Net Shipped Weights'), ('RW', 'Re Weights')],  string='Weights', readonly=True, states={'draft': [('readonly', False)]}, index=True)
    
    deadline = fields.Date(string='Deadline', required=False, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now)
    transportation_charges = fields.Selection([('none', 'None'), ('included', 'Included'), ('exclude', 'Exclude')], string='Transportation Charges', readonly=True, states={'draft': [('readonly', False)]}, copy=False, index=True, default='none')
    delivery_tolerance = fields.Float(string="Delivery Tolerance", default=5.0, readonly=True , states={'draft': [('readonly', False)]})
    
#     picking_count = fields.Integer(compute='_compute_pickings', string='Receptions', default=0)
#     picking_ids = fields.One2many('stock.picking', 'sale_contract_id', string='GDN List', readonly=True, copy=False)
    
    delivery_count = fields.Integer(compute='_compute_deliverys', string='Receptions', default=0)
    delivery_ids = fields.One2many('delivery.order', 'contract_id', string='DO List', readonly=True, copy=False)
    
    invoice_count = fields.Integer(compute='_compute_invoices', string='Receptions', default=0)
    invoice_ids = fields.One2many('account.move', 'sale_contract_id', string='Invoiced List', readonly=True, copy=False)
    
    # shipping_id = fields.Many2one('shipping.instruction', string='SI No.', ondelete='cascade')
    # scontract_id = fields.Many2one('s.contract', string='SNo.', ondelete='cascade' , readonly=True , states={'draft': [('readonly', False)]})
    
    x_is_bonded = fields.Boolean(string='Is Bonded')
    x_p_allocate = fields.Char(string='P Contract', )


    ################################################################## NED Contract ########################################################################
    @api.depends('contract_p_id','p_contract','contract_p_id.name')  
    def get_pcontract(self):
        for order in self:
            if order.contract_p_id:
                order.p_name = order.contract_p_id.name
            else:
                order.p_name = order.p_contract
    
    p_name = fields.Char(compute='get_pcontract', string='P Contract', store = True)
    contract_p_id = fields.Many2one('s.contract', string="PNo")
    
    
    @api.depends('shipping_id','contract_p_id', 'request_qty', 'request_bag')
    def get_quantity_contract(self):
        for record in self:
            if record.shipping_id:
                allocate_id = self.search([
                    ('shipping_id', '=', record.shipping_id.id), 
                    ('state', 'not in', ['draft', 'cancel']),
                ])
                allo_qty = allocate_id and sum([info.request_qty for info in allocate_id]) or 0
                allo_bag = allocate_id and sum([info.request_bag for info in allocate_id]) or 0

                if record.shipping_id.contract_id.contract_line:
                    record.si_qty_contract = sum([float(line.product_qty) for line in record.shipping_id.contract_id.contract_line if line.product_qty])
                    record.si_bag_contract = sum([float(line.number_of_bags) for line in record.shipping_id.contract_id.contract_line if line.number_of_bags])
                    record.s_allocated_qty = allo_qty
                    record.s_allocated_bag = allo_bag
                    record.s_unallocate_qty = record.si_qty_contract - allo_qty
                    record.s_unallocate_bag = record.si_bag_contract - allo_bag
                    
            
            if record.contract_p_id:
                allocate_id = self.search([
                    ('contract_p_id', '=', record.contract_p_id.id), 
                    ('state', 'not in', ['draft', 'cancel'])
                ])
                allo_qty = allocate_id and sum([info.request_qty for info in allocate_id]) or 0
                allo_bag = allocate_id and sum([info.request_bag for info in allocate_id]) or 0
                if record.contract_p_id.p_contract_line_ids:
                    record.p_qty_contract = sum([float(line.product_qty) for line in record.contract_p_id.p_contract_line_ids if line.product_qty])
                    record.p_bag_contract = sum([float(line.number_of_bags) for line in record.contract_p_id.p_contract_line_ids if line.number_of_bags])
                    record.p_allocated_qty = allo_qty
                    record.p_allocated_bag = allo_bag
                    record.p_unallocate_qty = record.p_qty_contract - allo_qty
                    record.p_unallocate_bag = record.p_bag_contract - allo_bag


    p_qty_contract = fields.Float(string='Contract Qty', compute='get_quantity_contract', store=True)
    p_bag_contract = fields.Float(string='Contract Bag', compute='get_quantity_contract', store=True)
    si_qty_contract = fields.Float(string='Contract Qty', compute='get_quantity_contract', store=True)
    si_bag_contract = fields.Float(string='Contract Bag', compute='get_quantity_contract', store=True)

    s_allocated_qty = fields.Float(string='Allocated Qty', compute='get_quantity_contract', store=True)
    s_unallocate_qty = fields.Float(string='Unallocated Qty', compute='get_quantity_contract', store=True)
    s_allocated_bag = fields.Float(string='Allocated Bag', compute='get_quantity_contract', store=True)
    s_unallocate_bag = fields.Float(string='Unallocated Bag', compute='get_quantity_contract', store=True)

    p_allocated_qty = fields.Float(string='Allocated Qty', compute='get_quantity_contract', store=True)
    p_unallocate_qty = fields.Float(string='Unallocated Qty', compute='get_quantity_contract', store=True)
    p_allocated_bag = fields.Float(string='Allocated Bag', compute='get_quantity_contract', store=True)
    p_unallocate_bag = fields.Float(string='Unallocated Bag', compute='get_quantity_contract', store=True)

    request_qty = fields.Float(string='Allocate Qty')
    request_bag = fields.Float(string='Allocate Bag')
    delivery_id = fields.Many2one('delivery.order', string='Ex-Stored')
    
    
    @api.model
    def _default_crop_id(self):
        crop_ids = self.env['ned.crop'].search([('state', '=', 'current')], limit=1)
        return crop_ids
    
    crop_id = fields.Many2one('ned.crop', string='Crop', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=_default_crop_id)
    
    product_id = fields.Many2one(related='contract_line.product_id',  string='Product',store=True)
    price_unit = fields.Float(related='contract_line.price_unit',  string='Price Unit')
    
    entries_id = fields.Many2one('account.move',  string='Entries')
    
    @api.depends('delivery_ids', 'delivery_ids.state','delivery_ids.total_qty','contract_line','contract_line.product_qty', \
    'invoice_ids','invoice_ids.state','invoice_ids.invoice_line_ids','invoice_ids.invoice_line_ids.quantity', \
    'invoice_ids.invoice_line_ids.price_unit')
    def _do_qty(self):
        for order in self:
            total_qty = 0
            total_invoice_qty = 0
            invoiced_amount_total = 0
            date_invoice = False
            total_qty = order.total_qty
            do_qty = 0
            
            # for line in order.delivery_ids:
            #     total_qty += line.total_qty
            for do in order.delivery_ids.filtered(lambda x: x.state != 'cancel'):
                do_qty += do.total_qty
                
            for line in order.invoice_ids:
                if line.state in('draft','cancel'):
                    continue
                
                for i in line.invoice_line_ids:
                    if i.product_uom_id.name == 'Tấn':
                        total_invoice_qty += i.quantity * 1000
                    else:
                        total_invoice_qty += i.quantity
                
                date_invoice = line.invoice_date
                if line.state in('draft','cancel'):
                    continue
                invoiced_amount_total += line.amount_total
                
            order.invoiced_qty = total_invoice_qty
            order.invoiced_amount_total = invoiced_amount_total
            
            order.do_qty = do_qty
            order.remain_qty = order.total_qty - order.do_qty
            order.loss_qty = total_qty - (total_invoice_qty)
            order.date_invoice = date_invoice
            
    do_qty = fields.Float(compute='_do_qty', digits=(12, 0) , string='Do Qty', store=True)
    remain_qty = fields.Float(compute='_do_qty', digits=(12, 0) , string='Remain Do' ,store=True)
    loss_qty = fields.Float(compute='_do_qty', digits=(12, 0) , string='Los Qty',store=True)
    
    invoiced_qty = fields.Float(compute='_do_qty', digits=(12, 3) , string='Invoiced Qty. (Mt)', store=True)
    invoiced_amount_total = fields.Monetary(compute='_do_qty',  string='Invoiced Total',store=True)
    
    date_invoice = fields.Date(compute='_do_qty', string='Date Invoice',store=True)
    
    supplier_id = fields.Many2one(related='contract_p_id.partner_id', string='Supplier')
    pss_type = fields.Selection(related='scontract_id.pss_type', selection=[('SAS','SAS'),('SAP','SAP'),('PSS','PSS'),('PSS+OTS','PSS+OTS'),('No','No')], string='Pss type')
    status = fields.Selection(related='scontract_id.status', selection=[('Paco BWH', 'Paco BWH'), 
        ('MBN BWH', 'MBN BWH'),
        ('KTN BWH', 'KTN BWH'),
        ('3rd party', '3rd party'),
        ('Ned VN', 'Ned VN'),
        ('Local sale', 'Local sale'),
        ('Spot', 'Spot'),
        ('Unallocated', 'Unallocated'),
        ('Afloat', 'Afloat'),
        ('Factory', 'Factory'),
        ('Cancel', 'Cancel'),
        ('Allocated', 'Allocated'), 
        ('FOB', 'FOB'),
        ('Factory', 'Factory'),
        ('MBN', 'MBN'),
        ('Pending', 'Pending')], string='Shipped By')


    @api.depends('scontract_id')
    def get_quality(self):
        for record in self:
            if record.scontract_id:
                record.quanlity = record.scontract_id.contract_line and record.scontract_id.contract_line[0].name
                shipment_date = record.scontract_id.shipt_month and str(record.scontract_id.shipt_month.name) or ''
                record.shipment_date = shipment_date

    quanlity = fields.Text(compute="get_quality", string='Quanlity', store=True)
    shipment_date = fields.Char(compute="get_quality", size=64, string='Shipment Month', store=True)


    @api.depends('invoice_ids','invoice_ids.state','invoice_ids.invoice_line_ids','invoice_ids.invoice_line_ids.quantity','invoice_ids.invoice_line_ids.price_unit')
    def _invoiced_qty(self):
        for order in self:
            total_invoice_qty = 0
            invoiced_amount_total = 0;
            for line in order.invoice_ids:
                if line.state =='draft':
                    continue
                for i in line.invoice_line_ids:
                    total_invoice_qty += i.quantity
                invoiced_amount_total += line.amount_total
            order.invoiced_qty = total_invoice_qty
            order.invoiced_amount_total = invoiced_amount_total
            
    
    
    @api.depends('contract_line','contract_line.product_qty')
    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.contract_line:
                total_qty += line.product_qty
            order.total_qty = total_qty
            
    total_qty = fields.Float(compute='_total_qty', digits=(16, 0) , string='Qty',store =True)
    certificate_id = fields.Many2one(related='contract_line.certificate_id',  string='Certificate', store =True)
    p_contract = fields.Char(string="P Contract")
    clam_ids = fields.One2many('sale.contract.clam', 'contract_id', 'Clam', readonly=False)
    
    def print_printout_nvs(self):
        return {'type': 'ir.actions.report.xml', 'report_name': 'printout_nvs_report'}
    
    #Kiệt ham này ko biết check cái gì ???
    # @api.onchange('contract_line','contract_line.product_qty')
    # def check_qty_allocated(self):
    #     if self.shipping_id.contract_id == self.scontract_id:
    #         self.check_remaing_qty()
    
    
    
    def check_remaing_qty(self):
        mess = ''
        if self.contract_p_id:
            for this in self:
                nvs_ids = self.sudo().search([('contract_p_id','=', this.contract_p_id.id)])
                qty_allocated = sum([x.product_qty for x in [y.contract_line for y in nvs_ids]])
                remaining_qty = sum([x.product_qty for x in this.contract_p_id.p_contract_line_ids]) - qty_allocated
            if remaining_qty < 0:
                mess += _('Total remaining quanlity of P-Contract have only %s Kg(s).\n')%(round(sum([x.remainning_qty*x.product_uom.factor_inv for x in this.contract_p_id.p_contract_line_ids]) + sum([x.product_qty*x.product_uom.factor_inv for x in this.contract_line]),2))

        product_qty = 0.0
        list_contract = self.sudo().search([('shipping_id','=',self.shipping_id.id)])
        for this in self.contract_line:
            qty_nvs = sum([x.product_qty for x in [y.contract_line.filtered(lambda r: r.product_id.id == this.product_id.id) for y in list_contract]])
            total_qty = sum([x.product_qty for x in self.shipping_id.shipping_ids.filtered(lambda r: r.product_id.id == this.product_id.id)])
            if qty_nvs > total_qty:
                mess += _('Quantity remainning of SI have only %s %s.')%(this.product_qty - abs(total_qty - qty_nvs), this.product_uom.name)
        if mess != '':
            raise UserError(_(mess))
    
    def button_load_p_contract(self):
        if self.contract_p_id:
            self.check_remaing_qty()
            var={}
            for line in self.contract_p_id.p_contract_line_ids:
                var = {
                        'final_g2_price': line.market_price or 0.0,
                        'final_g2_diff': line.p_contract_diff or 0.0
                        }
            self.contract_line.write(var)
        
        for record in self:
            if record.shipping_id:
                record.certificate_id_list = [(6, 0, [x.id for x in record.shipping_id.certificated_ids])]
                record.license_certificate_ids = [(6, 0, [x.license_id.id for x in record.shipping_id.license_allocation_ids])]
        return True
    
    @api.constrains('contract_p_id','contract_line')
    def _check_remaining(self):
        if self.contract_p_id and self.shipping_id.contract_id == self.scontract_id:
            self.check_remaing_qty()

    @api.constrains('contract_line','contract_line.product_qty')
    def check_allocated(self):
        if self.shipping_id.contract_id == self.scontract_id:
            self.check_remaing_qty()

    @api.onchange('shipping_id')
    def onchange_si_id(self):
        if self.shipping_id:
            shipping_info = self.env['shipping.instruction'].browse(self.shipping_id.id)
            return {'value': {'scontract_id': shipping_info.contract_id.id}}
        return {'value': {}}
            
    # Dim lại lấy theo contract VN
    # def onchange_scontract_id(self, cr, uid, ids, scontract_id):
    #     if scontract_id:
    #         s_contract_info = self.pool['s.contract'].browse(cr, uid, scontract_id)
    #         s_allocated_id = self.pool['sale.contract'].search(cr, uid, [('scontract_id', '=', scontract_id)])
    #
    #         s_allocated_qty = 0
    #         if s_allocated_id:
    #             s_allocated_qty = sum([self.browse(cr, uid, s).request_qty for s in s_allocated_id])
    #         customer_id = s_contract_info.partner_id.id
    #         return {'value': {'partner_id': customer_id, 
    #                           'quality': s_contract_info.contract_line and s_contract_info.contract_line[0].name or '',
    #                           's_allocated_qty': s_allocated_qty,
    #                           's_unallocate_qty': s_contract_info.contract_line[0].product_qty - s_allocated_qty,
    #                           'pss_type': s_contract_info.pss_type and s_contract_info.pss_type or ''
    #                          },
    #                 'domain': {'contract_p_id': [('p_contract_line_ids.product_id', '=', s_contract_info.contract_line and s_contract_info.contract_line[0].product_id.id or 0), ('type', '=', 'p_contract')]}}
    #     return {'value': {}}
    
    
                
                
    def onchange_pcontract_id(self, cr, uid, ids, pcontract_id):
        if pcontract_id:
            s_contract_info = self.env['s.contract'].browse(cr, uid, pcontract_id)
            s_allocated_id = self.env['sale.contract'].search(cr, uid, [('contract_p_id', '=', pcontract_id)])
            
            qty_allocated = 0
            remaining_qty = 0
           
            s_allocated_qty = 0
            if s_allocated_id:
                s_allocated_qty = sum([self.browse(cr, uid, s).request_qty for s in s_allocated_id])
            customer_id = s_contract_info.partner_id.id
            return {'value': {
                              'quality': s_contract_info.contract_line and s_contract_info.contract_line[0].name or '',
                              'p_allocated_qty': s_allocated_qty,
                              'p_unallocate_qty': s_contract_info.p_qty - s_allocated_qty                             
                             },
                    'domain': {'contract_p_id': [('p_contract_line_ids.product_id', '=', s_contract_info.contract_line and s_contract_info.contract_line[0].product_id.id or 0), ('type', '=', 'p_contract')]}}
        return {'value': {}}

    def allocate_sp(self):
        contract_line_obj = self.env['sale.contract.line']
        do_obj = self.env['delivery.order']
        for record in self:
            if record.shipping_id:
                record.contract_p_id.write({
                    's_contract_link': record.scontract_id.id, 
                    'qty_allocated': record.request_qty + record.p_allocated_qty, 
                    'tb_qty_alloca': record.p_unallocate_qty - record.request_qty,
                    'bag_allocated': record.request_bag + record.p_allocated_bag,
                    'tb_bag_alloca': record.p_unallocate_bag - record.request_bag
                })

                # record.scontract_id.write({
                #     'allowcated_date': fields.Datetime.now()
                # })
                
                if record.contract_p_id:
                    if record.contract_p_id.wr_line:
                        self.env.cr.execute(''' Insert into stack_shipment_rel values(%s, %s) ; ''' % (record.contract_p_id.wr_line.id, record.shipping_id.id))
                
                scontract_line = record.shipping_id.contract_id.contract_line and record.shipping_id.contract_id.contract_line[0] or False
                val_lines = {
                    'contract_id': record.id,
                    'product_id': scontract_line and scontract_line.product_id.id or 0,
                    'name': scontract_line and scontract_line.name or '',
                    'certificate_id': scontract_line and (scontract_line.certificate_id and scontract_line.certificate_id.id or 0) or 0,
                    'packing_id': scontract_line and scontract_line.packing_id.id or 0,
                    'product_qty': record.request_qty and record.request_qty or 0,
                    'product_uom': scontract_line and scontract_line.product_uom.id or 25,
                    'partner_id': record.scontract_id.partner_id.id
                }
                contract_line_obj.create(val_lines)

                do_id = do_obj.create({
                    'contract_id': record.id,
                    'partner_id': record.shipping_id.partner_id.id,
                    'warehouse_id': record.contract_p_id.wr_line and record.contract_p_id.wr_line.zone_id.warehouse_id.id or 19,
                    'real_qty': record.request_qty,
                    'packing_qty': record.request_bag,
                    'type': 'bonded',
                    # 'name': 'EX-%s-%s' % (record.shipping_id.name, record.contract_p_id.name),
                    # 'product_uom': scontract_line.product_uom.id,
                    'product_id': record.contract_p_id.standard_id and record.contract_p_id.standard_id.id or 0
                })
                val ={
                        'name': 'Allocate-S%s-%s' % (record.scontract_id.name, record.contract_p_id.name),
                        'port_of_loading': record.shipping_id.port_of_loading and record.shipping_id.port_of_loading.id or False,
                        'port_of_discharge': record.shipping_id.port_of_discharge and record.shipping_id.port_of_discharge.id or False,
                        'weights':record.shipping_id.contract_id and record.shipping_id.contract_id.weights or False,
                        'deadline': record.shipping_id.shipment_date,
                        'state': 'approved',
                        'delivery_id': do_id.id
                    }
                record.write(val)
        
        
        # NED Contract VN
        for this in self:
            if not this.warehouse_id:
                raise UserError(_('Warehouse is not null'))

            if this.picking_id:
                raise UserError(_('Contract %s đã tạo phiếu xuất kho %s') %(this.contract_p_id.name, this.picking_id.name))
            detail_info = [l for l in this.detail_ids]
            if not detail_info:
                raise UserError(_('Chưa có stack %s được gắn trong hợp đồng S') %(this.contract_p_id.name))
            warehouse = this.detail_ids[0].warehouse_id and this.detail_ids[0].warehouse_id or False

            if this.warehouse_id.id != warehouse.id:
                raise UserError(_('Warehouse %s Khác với Kho được lưu trên stack %s') %(this.warehouse_id.name, this.picking_id.name))
            picking_type_id = this.warehouse_id.out_type_id
            if picking_type_id:
                packing_id = False

                var = {'name': '/',
                       'picking_type_id': picking_type_id.id or False,
                       'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                       'origin':this.name,
                       'warehouse_id': this.warehouse_id.id,
                       'partner_id': this.partner_id.id or False,
                       'picking_type_code': picking_type_id.code or False,
                       'location_id': picking_type_id.default_location_src_id.id or False,
#                        'vehicle_no':this.delivery_id.trucking_no or '',
                       'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                       'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)}
                picking_id = self.env['stock.picking'].create(var)
                for info in detail_info:
                    self.env['stock.move.line'].create({'picking_id': picking_id.id or False,
                       # 'name': info.stack_id.product_id.name or '',
                       'product_id': info.stack_id.product_id.id or False,
                       # 'product_uom': info.stack_id.product_id.uom_id.id or False,
                       # 'product_uom_qty': info.allocated_qty and info.allocated_qty or info.tobe_qty,
                       'init_qty': info.allocated_qty and info.allocated_qty or info.tobe_qty,
                       'bag_no': info.tobe_bag or 0,
                       'price_unit': 0.0,
                       'picking_type_id': picking_type_id.id or False,
                       'location_id': picking_type_id.default_location_src_id.id or False,
                       # 'date_expected': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                       'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                       # 'type': picking_type_id.code or False,
                       'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                       'partner_id': this.partner_id.id or False,
                       'company_id': 1,
                       'state':'draft',
                       # 'scrapped': False,
                       #'grp_id':this.grp_id.id,
                       'zone_id': info.stack_id.zone_id.id,
                       'lot_id': info.stack_id.id,
                       'packing_id': packing_id,
                       'warehouse_id': this.warehouse_id.id or False})
                this.picking_id = picking_id.id

                # this.picking_id.action_confirm()
                # this.picking_id.action_assign()
                # this.picking_id.button_validate()
                this.picking_id.button_qc_assigned()
                this.picking_id.button_sd_validate()

        for i in self.detail_ids.filtered(lambda x: x.stack_id):
            i.stack_id.allocate_qty -= i.allocated_qty
        return self.write({'state': 'approved'})
        

    @api.onchange('s_unallocate_qty', 'p_unallocate_qty')
    def onchange_s_p_qty(self):
        if self.s_unallocate_qty and self.p_unallocate_qty:
            return {'value': {'request_qty': min(self.s_unallocate_qty, self.p_unallocate_qty)}}
        return {'value': {}}
        
    def de_allocate_sp(self):
        return self.write({'state': 'approved'})
    
    confirm_qc = fields.Boolean(string='Confirm by QC', default=False)
    confirm_date = fields.Datetime(string='Confirm Date By Qc')

    def qc_confirm(self):
        for record in self:
            record.write({
                'confirm_qc': True,
                'confirm_date': datetime.today()
            })

    def refuse_qc_confirm(self):
        for record in self:
            record.write({
                'confirm_qc': False,
                'confirm_date': None
            })

    ###############################NED Contract VN ######################################################################################################################################
    #Ned vn
    
    lot_no = fields.Char(string="Lot no")
    picking_id = fields.Many2one('stock.picking',string="Picking")
    # warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse")
    detail_ids = fields.One2many('sale.contract.deatail', 'sp_id', 'Detail', ondelete='cascade')
    scertificate_id = fields.Many2one('ned.certificate', related='scontract_id.certificate_id', string='Certificate', store = True)
    
    scertificate_id = fields.Many2one('ned.certificate', related='scontract_id.certificate_id', string='Certificate', store = True)
    p_ids = fields.Many2many('s.contract', 'sale_contract_scontract_rel', 'sale_id', 'p_id', string='P to allocate list')
    p_quality = fields.Text(related='scontract_id.p_quality', string='Quality')
    # product_id = fields.Many2one('product.product', 'Product')
    product_id1 = fields.Many2one('product.product', 'Product 2')
    product_id2 = fields.Many2one('product.product', 'Product 3')
    
    p_quality = fields.Text(related='scontract_id.p_quality', string='Quality')
    nominated_etd = fields.Date(string="Nominated ETD", related='scontract_id.traffic_link_id.nominated_etd', store= True)
    bill_date = fields.Date(related='scontract_id.traffic_link_id.bill_date', string="ETD/ BL date", store= True)
    booking_ref_no = fields.Char(related='scontract_id.traffic_link_id.booking_ref_no', string='Booking No./ BL No.', store= True)
    nominated_etd = fields.Date(string="Nominated ETD", related='scontract_id.traffic_link_id.nominated_etd', store= True)
    packing_id = fields.Many2one(string="Packing", related='scontract_id.traffic_link_id.packing_id', store= True)
    
    @api.onchange('detail_ids')
    def onchange_pcontract(self):
        for record in self:
            if record.detail_ids:
                record.warehouse_id = record.detail_ids[0].p_contract_id.warehouse_id and record.detail_ids[0].p_contract_id.warehouse_id.id or 0
    
    
    @api.onchange('scontract_id')
    def onchange_scontract_id(self):
        if self.scontract_id:

            s_contract_info = self.env['s.contract'].browse(self.scontract_id.id)
            s_allocated_id = self.env['sale.contract'].search([('scontract_id', '=', self.scontract_id.id)])

            s_allocated_qty = 0
            if s_allocated_id:
                s_allocated_qty = sum([self.browse(s.id).request_qty for s in s_allocated_id])
            customer_id = s_contract_info.partner_id.id
            return {'value': {'partner_id': customer_id,
                              'quality': s_contract_info.contract_line and s_contract_info.contract_line[0].name or '',
                              's_allocated_qty': s_allocated_qty,
                              's_unallocate_qty': s_contract_info.contract_line[0].product_qty - s_allocated_qty,
                              'pss_type': s_contract_info.pss_type and s_contract_info.pss_type or '',
                              'product_id1': s_contract_info.product_id and s_contract_info.product_id.id or 0,
                              'certificate_id': s_contract_info.certificate_id and s_contract_info.certificate_id.id or 0
                             },
                    'domain': {'contract_p_id': [('p_contract_line_ids.product_id', '=', s_contract_info.contract_line and s_contract_info.contract_line[0].product_id.id or 0), ('type', '=', 'p_contract')]}}
        return {'value': {}}
    
    
    ############################################END NED Contract Vn###################################################################


    @api.model
    def create(self, vals): 
        shipping_obj = self.env['shipping.instruction']
        contract_obj = self.env['s.contract']
        if not vals.get('x_is_bonded'):
            if vals.get('type', False) and vals.get('type', False) == 'local':
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.nls')
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('sale.nvs')
        if vals.get('x_is_bonded'):
            vals['name'] = self.env['ir.sequence'].next_by_code('sale.nvs.traffic')
        # else:
        #     name = vals.get('name', False)
        #     contract_ids = self.search([('name', '=', name)])
        #     if len(contract_ids) >= 1:
        #         raise UserError(_("Contract (%s) was exist.") % (name))
            
        #Ned contract
        if 'shipping_id' in vals:
            shipping_info = shipping_obj.browse(vals['shipping_id'])
            contract_id = shipping_info.contract_id and shipping_info.contract_id.id or 0
            status = shipping_info.status or ''
            partner_id = shipping_info.contract_id and shipping_info.contract_id.partner_id.id or 0
            vals.update({
                #Kiet ko thấy fields này
                #'contract_id': contract_id,
                
                #'status': status,
                'partner_id': partner_id
            })
        if 'contract_p_id' in vals:
            sup_id = contract_obj.browse(vals['contract_p_id']).partner_id.id
            vals.update({
                'supplier_id': sup_id
            })
            
        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
            
        # if vals.get('port_of_discharge', False) != False and vals.get('port_of_loading', False) != False:
        #     if vals.get('port_of_discharge', False) == vals.get('port_of_loading', False):
        #         raise ValidationError("Port Of Loading and Port of Discharge is not the same.")
        result = super(SaleContract, self).create(vals)
        return result
    
    def unlink(self):
        if self.state not in ('draft', 'cancel'):
            raise UserError(_('You can only delete draft or cancel Contract.'))
        return super(SaleContract, self).unlink()
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({
                'payment_term_id': False,
                'partner_invoice_id': False,
                'partner_shipping_id': False,
                'currency_id': False,
            })
            return
        addr = self.partner_id.address_get(['delivery', 'invoice'])
        values = {
            'payment_term_id': self.partner_id.property_payment_term_id and self.partner_id.property_payment_term_id.id or False,
            'partner_invoice_id': addr['invoice'],
            'partner_shipping_id': addr['delivery'],
            'currency_id': self.partner_id.property_product_pricelist and self.partner_id.property_product_pricelist.currency_id.id or False,
            }
        self.update(values)
    
    @api.onchange('company_id')
    def company_id_domain(self):
        if not self.company_id:
            return {'domain': {'company_representative': []}}
        domain = {'company_representative': [('parent_id', '=', self.company_id.partner_id.id)]}
        return {'domain':domain}
    
    
    def button_draft(self):
        if sum([x.total_qty for x in self.delivery_ids]) > 0 and not self.user_has_groups('sd_sale_contract.group_sale_contract_button'):
            raise UserError(_('Unable set to draft for Contract %s when DO Qty > 0.\n\t Please contact with your manager.') % (self.name))
        
        if self.state == 'done':
            raise UserError(_('Unable to cancel Contract %s as some receptions have already been done.\n\t You must first cancel related receptions.') % (self.name))
        
        self.write({'state': 'draft'})
    
    def button_approve(self):
        for contract in self:
            if not contract.contract_line:
                raise UserError(_('You cannot approve a Contract without any Contract Line.'))
        self.write({'state': 'approved', 'user_approve': self.env.uid,
                    'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        
    def contract_total_qty(self):
        total_qty = 0.0
        for line in self.contract_line:
            total_qty += line.product_qty
        return total_qty
    
    def button_done(self):
        self.write({'state': 'done', 'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
    
    def action_view_picking(self):
        action = self.env.ref('stock.action_picking_tree')
        result = action.read()[0]
        pick_ids = sum([order.picking_ids.ids for order in self], [])
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result
    
    def create_do(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('sd_sale_contract.action_view_wizard_do')
        form_view_id = imd.xmlid_to_res_id('sd_sale_contract.view_wizard_do')
        
        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'res_model': action.res_model,
            }
        return result
    
    def action_view_do(self):
        action = self.env.ref('sd_sale_contract.action_delivery_order')
        result = action.read()[0]
        pick_ids = sum([order.delivery_ids.ids for order in self], [])
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('sd_sale_contract.view_delivery_order_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result
    
    def action_view_invoice(self):
        # invoice_ids = self.mapped('invoice_ids')
        invoice_ids = sum([order.invoice_ids.ids for order in self], [])
        imd = self.env['ir.model.data']
        action = self.env.ref('account.action_move_out_invoice_type')
        result = action.read()[0]
        if len(invoice_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, invoice_ids)) + "])]"
        elif len(invoice_ids) == 1:
            res = self.env.ref('account.view_move_form', False)
            result['context'] = {}
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = invoice_ids and invoice_ids[0] or False
        return result
    
    def create_invoice(self):
        imd = self.env['ir.model.data']
        
        action = self.env.ref('sd_sale_contract.view_wizard_invoice')
        result = action.read()[0]
        # pick_ids = sum([order.delivery_ids.ids for order in self], [])
        res = self.env.ref('sd_sale_contract.view_delivery_order_form', False)
        result['context'] = {}
        result['views'] = [(res and res.id or False, 'form')]
        # result['res_id'] = pick_ids and pick_ids[0] or False
            
        return result
    
    
    shipping_id = fields.Many2one('shipping.instruction', string='SI No.', ondelete='cascade', readonly=True , states={'draft': [('readonly', False)]})
    scontract_id = fields.Many2one('s.contract', string='SNo.', ondelete='cascade' , readonly=True , states={'draft': [('readonly', False)]})
    
    #Kiet: 17 05/ 2023 thêm fields
    
    shipt_month = fields.Many2one('s.period', related="scontract_id.shipt_month", store= True)
    
    def button_load(self):
        if self.shipping_id:
            self.contract_line.unlink()
            # self.env.cr.execute('''DELETE FROM sale_contract_line WHERE contract_id = %s''' % (self.id))
            product_qty = new_qty = 0.0
            val ={
                    'scontract_id':self.shipping_id.contract_id and self.shipping_id.contract_id.id or False,
                    'partner_id':self.shipping_id.partner_id and self.shipping_id.partner_id.id or False,
                    'currency_id':self.shipping_id.contract_id.currency_id and self.shipping_id.contract_id.currency_id.id or False,
                    'port_of_loading': self.shipping_id.port_of_loading and self.shipping_id.port_of_loading.id or False,
                    'port_of_discharge': self.shipping_id.port_of_discharge and self.shipping_id.port_of_discharge.id or False,
                    'weights':self.shipping_id.contract_id and self.shipping_id.contract_id.weights or False,
                    'deadline': self.shipping_id.shipment_date
                }
            self.write(val)
            
            # for shipping in self.shipping_id.shipping_ids:
            #     for nvs in self.shipping_id.contract_ids:
            #         if nvs.state != 'cancel':
            #             for nvs_line in nvs.contract_line:
            #                 if nvs_line.product_id == shipping.product_id:
            #                     product_qty += nvs_line.product_qty
                                
            
            for shipping in self.shipping_id.shipping_ids:
                nvs_line = self.env['sale.contract.line'].search([('state','!=','cancel'),('product_id','=',shipping.product_id.id),('contract_id.shipping_id','=',self.shipping_id.id)])
                product_qty = sum(nvs_line.mapped('product_qty')) or 0.0
                new_qty = shipping.product_qty - product_qty
                var = {'contract_id': self.id or False, 'name': shipping.name or False, 
                        'product_id': shipping.product_id.id or False,
                        'tax_id': [(6, 0, [x.id for x in shipping.tax_id])] or False, 'price_unit': shipping.price_unit or 0.0,
                        'product_qty': new_qty or 0.0, 'product_uom': shipping.product_uom.id or False,
                        'state': 'draft', 'certificate_id': shipping.certificate_id.id or False, 'packing_id': shipping.packing_id.id or False}
                self.env['sale.contract.line'].create(var)
                
        return True

    
    
    
    
