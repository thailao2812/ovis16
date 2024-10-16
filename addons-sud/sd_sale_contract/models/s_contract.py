# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from datetime import date
from datetime import datetime

from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT 
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
                
from lxml import etree


myear = ['', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
lst_status = ['Paco BWH', 'MBN BWH', 'KTN BWH', '3rd party', 'Ned VN', 'Local sale', 'Spot', 'Unallocated', 'Afloat', 'Factory', 'Cancel']


class SContract(models.Model):
    _name = "s.contract"
    _description = "S-Contract and P-Contract"
    _inherit = ['mail.thread'] #SON Add
    _order = 'id desc'
    
    
    # @api.constrains('name')
    # def _check_duplicate_name(self):
    #     for contract in self:
    #         if not contract.name:
    #             continue
    #         if contract.name =='/':
    #             continue
    #         exist = self.with_context(active_test=False).search([('id', '!=', contract.id),
    #                                                              ('name', '=', contract.name)], limit=1)
    #         if exist:
    #             raise UserError(_('Name contract %s had been exists.') % (contract.name))
    #     return True
    
    
    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id 
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids
    
    @api.model
    def _default_company_id(self):
        company_ids = self.env['res.users'].browse(self.env.uid).company_id.id
        return company_ids
    
    @api.model
    def _default_currency_id(self):
        currency_ids = self.env['res.currency'].search([], limit=1)
        return currency_ids
    
    # @api.multi
    # def button_dummy(self):
    #     return True
    
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

    @api.depends('shipping_ids')
    def _compute_shippings(self):
        for contract in self:
            contract.shipping_count = len(contract.shipping_ids)
            
    @api.depends('contract_ids')
    def _compute_contracts(self):
        for contract in self:
            contract.contract_count = len(contract.contract_ids)
    
    name = fields.Char(string='Sno', required=True, copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True, default='/')
    company_id = fields.Many2one('res.company', string='Company', required=True, change_default=True, readonly=True, default=_default_company_id)
    company_representative = fields.Many2one("res.partner", string="Company Representative", readonly=True, states={'draft': [('readonly', False)]})
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, readonly=True, states={'draft': [('readonly', False)]}, default=_default_warehouse_id)
    picking_policy = fields.Selection([('direct', 'Deliver each product when available'), ('one', 'Deliver all products at once')],
        string='Shipping Policy', required=False, readonly=True, default='direct', states={'draft': [('readonly', False)]})

    state = fields.Selection([('draft', 'New'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
             string='Status', readonly=True, copy=False, index=True, default='draft')
    
    type = fields.Selection([('s-local', 'S-Local'), ('s-export', 'S-Export'), 
                             ('local', 'Local'), ('export', 'Export'),
                             ('p_contract','P Contract')], string='Type', required=True, readonly=True, index=True)
    
      
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True, states={'draft': [('readonly', False)]}, required=True, change_default=True, index=True)
    customer_representative = fields.Many2one('res.partner', string='Customer Representative', readonly=True, states={'draft': [('readonly', False)]}, index=True, )
    
    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=False, states={'draft': [('readonly', False)], 'sent': [('readonly', False)]}, help="Invoice address for current Purchase order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=False, states={'draft': [('readonly', False)]})
    
    date = fields.Date(string='Date', readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    validity_date = fields.Date(string='Validity Date', required=True, readonly=True, index=True, states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    expiration_date = fields.Date(string='Expiration Date', readonly=True, states={'draft': [('readonly', False)]})
    
    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True, states={'draft': [('readonly', False)]}, default=_default_currency_id)
    exchange_rate = fields.Float(string="Exchange Rate", readonly=True, required=True, states={'draft': [('readonly', False)]}, default=1.0)
    
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    bank_id = fields.Many2one('res.bank', string='Bank', readonly=True, copy=False, states={'draft': [('readonly', False)]})
    acc_number = fields.Char(string='Account Number', copy=False, readonly=True, states={'draft': [('readonly', False)]})
    
    contract_line = fields.One2many('s.contract.line', 'contract_id', string='Contract Lines', readonly=True, states={'draft': [('readonly', False)]}, copy=True)
  
    note = fields.Text('Terms and conditions')
    
    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all')
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all', )
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', )
    
    create_date = fields.Date(string='Creation Date', readonly=True, index=True, default=fields.Datetime.now)
    create_uid = fields.Many2one('res.users', 'Responsible', readonly=True , default=lambda self: self._uid)
    date_approve = fields.Date('Approval Date', readonly=True,  copy=False)
    user_approve = fields.Many2one('res.users', string='User Approve', readonly=True)
    date_done = fields.Date('Date Done', readonly=True,  copy=False)
    # S Contract
    trader = fields.Char(string='Trader', copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True)
    dispatch_mode = fields.Selection([('air', 'Air'), ('rail', 'Rail'), ('road', 'Road'), ('sea', 'Sea')], string='Dispatch Mode', readonly=True, states={'draft': [('readonly', False)]}, index=True)
    
    port_of_loading = fields.Many2one('delivery.place', string='Port Of Loading', copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True)
    port_of_discharge = fields.Many2one('delivery.place', string='Port of Discharge', copy=False, readonly=True, states={'draft': [('readonly', False)]}, index=True)
    container_status = fields.Selection([('fcl/fcl', 'FCL/FCL'), ('lcl/fcl', 'LCL/FCL'), ('lcl/lcl', 'LCL/LCL')], string='Container Status', readonly=True, states={'draft': [('readonly', False)]}, index=True)
    weights = fields.Selection([('DW', 'Delivered Weights'), ('NLW', 'Net Landed Weights'),
                                ('NSW', 'Net Shipped Weights'), ('RW', 'Re Weights')], 
                               string='Weigh Condition', readonly=True, states={'draft': [('readonly', False)]}, index=True)
    
    deadline = fields.Date(string='Deadline', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=fields.Datetime.now)

    transportation_charges = fields.Selection([('none', 'None'), ('included', 'Included'), ('exclude', 'Exclude')], string='Transportation Charges', readonly=True, states={'draft': [('readonly', False)]}, copy=False, index=True, default='none')
    delivery_tolerance = fields.Float(string="Delivery Tolerance", default=5.0, readonly=True , states={'draft': [('readonly', False)]})
    
    shipping_count = fields.Integer(compute='_compute_shippings', string='Receptions', default=0)
    shipping_ids = fields.One2many('shipping.instruction', 'contract_id', string='Shipping Instruction List', readonly=True)
    
    contract_count = fields.Integer(compute='_compute_contracts', string='Receptions', default=0)
    contract_ids = fields.One2many('sale.contract', 'scontract_id', string='NLS', readonly=True, copy=True)
    
    qty_condition = fields.Selection([('pss','PSS'), ('none', 'PCS')], string="Quality Condition", default='none')
    marking = fields.Text(string="Shipping Marks")
    p_contract_diff = fields.Float(related='p_contract_line_ids.p_contract_diff', string="P-Contract Differencial", store= True)
    #market_price = fields.Float(related='p_contract_line_ids.market_price', string="Market Price", store= True)
    market_price = fields.Float(string="Market Price", store= True)
    
    
    contract_p_ids = fields.One2many('sale.contract','contract_p_id', string="contract_p_ids")
    
    p_allocated = fields.Float(string="P Allocated", store= True, compute='compute_p_allocated')
    p_unallocated = fields.Float(string="P UnAllocated", store= True, compute='compute_p_allocated')
    
    @api.depends('contract_p_ids',
                 'contract_p_ids.contract_p_id',
                 'contract_p_ids.contract_p_id.contract_line',
                 'contract_p_ids.contract_p_id.contract_line.product_qty',
                 'p_contract_line_ids',
                 'p_contract_line_ids.product_qty')
    def compute_p_allocated(self):
        for p in self:
            p_unallocated = sale_contract = 0
            for i in p.contract_p_ids:
                sale_contract += sum(i.contract_line.mapped('product_qty'))
                
            p_unallocated += sum(p.p_contract_line_ids.mapped('product_qty'))
            p.p_allocated = sale_contract
            p.p_unallocated = sale_contract - p_unallocated
        
    
    
    
    
    char_license = fields.Char(string='License Number', compute='compute_license_char_number', store=True)
    certificate_supplier = fields.Char(string='Certificate Supplier', compute='compute_license_char_number', store=True)
    # char_certificate = fields.Char(string='Char Certificate', default='[]')

    @api.depends('license_allocation_ids')
    def compute_license_char_number(self):
        for record in self:
            record.char_license = ''
            if record.license_allocation_ids:
                record.char_license = ', '.join([kq.license_id.name for kq in record.license_allocation_ids])
                record.certificate_supplier = ', '.join([kq.license_id.partner_id.name for kq in record.license_allocation_ids])
                

                
    
    
    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.contract_line:
                total_qty += line.product_qty
            order.total_qty = total_qty
            
    total_qty = fields.Float(compute='_total_qty', digits=(16, 0) , string='Total Qty')
    
    product_id = fields.Many2one('product.product', related=False, compute='_compute_product_id', string='Product', store = True)

    @api.depends('p_contract_line_ids', 'p_contract_line_ids.product_id',
                 'contract_line', 'contract_line.product_id')
    def _compute_product_id(self):
        for record in self:
            if record.p_contract_line_ids:
                record.product_id = record.p_contract_line_ids[0].product_id.id \
                    if record.p_contract_line_ids[0].product_id else False
            if record.contract_line:
                record.product_id = record.contract_line[0].product_id.id \
                    if record.contract_line[0].product_id else False
    
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        context = self._context
        res = super(SContract, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    
        if view_type in ['tree', 'form']:
            doc = etree.XML(res['arch'])
            type = context.get('default_type', False)
            if type == 'local':
                for node in doc.xpath("//button[@name='create_si']"):
                    node.set('invisible', "1")
                for node in doc.xpath("//button[@name='action_view_shipping']"):
                    node.set('invisible', "1")
                for node in doc.xpath("//page[@name='shipping']"):
                    node.set('invisible', "1")
            if type == 'export':
                for node in doc.xpath("//button[@name='create_nls']"):
                    node.set('invisible', "1")
                for node in doc.xpath("//button[@name='action_view_contract_nls']"):
                    node.set('invisible', "1")
                for node in doc.xpath("//page[@name='nls']"):
                    node.set('invisible', "1")
    
            # xarch, xfields = self._view_look_dom_arch(doc, view_id, context=context)
            # res['arch'] = xarch
            # res['fields'] = xfields
        return res
    
    # @api.model
    # def create(self, vals):
    #     if vals.get('name', False):
    #         name = vals.get('name', False)
    #         contract_ids = self.search([('name', '=', name)])
    #         if len(contract_ids) >= 1:
    #             raise UserError(_("S Contract (%s) was exist.") % (name))
    #
    #     if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id']):
    #         partner = self.env['res.partner'].browse(vals.get('partner_id'))
    #         addr = partner.address_get(['delivery', 'invoice'])
    #         vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
    #         vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])
    #
    #     new_id = super(SContract, self).create(vals)
    #
    #
    #
    #     ############# NED Contract ###################################################
    #     shipment_inf = {
    #         'status': new_id.status and new_id.status or '',
    #         'name': 'SI-%s' % (new_id.name and new_id.name or ''),
    #         'client_ref': new_id.client_ref or '',
    #         'partner_id': new_id.partner_id and new_id.partner_id.id or 0,
    #         'standard_id': new_id.product_id and new_id.product_id.id or (new_id.standard_id and new_id.standard_id.id or 0),
    #         'scertificate_id': new_id.certificate_id and new_id.certificate_id.id or 0,
    #         'incoterms_id': new_id.incoterms_id and new_id.incoterms_id.id or 0,
    #         'contract_id': new_id.id,
    #         'port_of_loading': new_id.port_of_loading and new_id.port_of_loading.id or '',
    #         'port_of_discharge': new_id.port_of_discharge and new_id.port_of_discharge.id or '',
    #         'spacking_id': new_id.packing_id and new_id.packing_id.id or 0,
    #         'no_of_bag': new_id.no_of_pack or 0,
    #         'specs': new_id.p_quality or new_id.standard_id.name,
    #         'request_qty': new_id.p_qty and new_id.p_qty or 0
    #     }
    #     if 'type' in vals or 'default_type' in self.env.context:
    #         if  (vals.get('type', False) == 'p_contract' or self.env.context.get('default_type', False) == 'p_contract') and 'traffic' in self.env.context.keys():
    #             wh_code = new_id.warehouse_id and '%s-' % new_id.warehouse_id.code or ''
    #             shipt_month = new_id.shipt_month and '-%s' % new_id.shipt_month.name or ''
    #             cname = new_id.name and '-%s' % new_id.name or ''
    #             zone_id = self.env['stock.zone'].search([('warehouse_id', '=', vals.get('warehouse_id', 0))], limit=1)
    #             stack_info = {
    #                 'name': '%sWR%s' % (wh_code, cname),
    #                 'tack_type': 'stacked',
    #                 'date': fields.Datetime.now(),
    #                 'p_contract_id': new_id.id,
    #                 'shipper_id': new_id.partner_id and new_id.partner_id.id or 0,
    #                 'product_id': new_id.product_id and new_id.product_id.id or (new_id.standard_id and new_id.standard_id.id or 0),
    #                 'zone_id': zone_id and zone_id.id or 0,
    #             }
    #             self.env['stock.lot'].create(stack_info)
    #         elif vals.get('type', False) in ['export', 'local'] or self.env.context.get('default_type', False) in ['export', 'local']:
    #             shipment = self.env['shipping.instruction'].create(shipment_inf)
    #
    #
    #     return new_id
    
    def write(self, values):    
        if values.get('standard_id'):
            for record in self:
                for p_line in record.p_contract_line_ids:
                    p_line.write({
                        'product_id': values['standard_id']
                    })
                    
        return super(SContract, self).write(values)
    
    
    def unlink(self):
        for line in self:
            if line.state not in ('draft', 'cancel'):
                raise UserError(_('You can only delete draft or cancel contract.'))
        return super(SContract, self).unlink()
    
    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if not self.partner_id:
            self.update({
                'payment_term_id': False,
                'partner_invoice_id': False,
                'partner_shipping_id': False,
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
        self.write({'state': 'draft', 'create_date': self.env.uid, 'create_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
    
    def button_cancel(self):
        if self.state == 'done':
            raise UserError(_('Unable to cancel S Contract %s') % (self.name))
        if self.state == 'approved':
            if self.type == 'export':
                if self.shipping_ids:
                    for shipping in self.shipping_ids:
                        if shipping.state == 'done':
                            raise UserError(_('Unable to cancel S Contract %s as some receptions have already been done.\n\t You must first cancel related SI.') % (self.name))
                    if shipping.contract_ids:
                        for contract in shipping.contract_ids:
                            if contract.state == 'done':
                                raise UserError(_('Unable to cancel S Contract %s as some receptions have already been done.\n\t You must first cancel related NVS.') % (self.name))
                            if contract.picking_ids:
                                for i in contract.picking_ids:
                                    if i.state == 'done':
                                        raise UserError(_('Unable to cancel S Contract %s as some receptions have already been done.\n\t You must first cancel related GDN.') % (self.name))
                            if contract.delivery_ids:
                                for j in contract.delivery_ids:
                                    if i.state == 'done':
                                        raise UserError(_('Unable to cancel S Contract %s as some receptions have already been done.\n\t You must first cancel related DO.') % (self.name))
                    self.env.cr.execute('''
                    DELETE FROM stock_pack_operation WHERE picking_id in (SELECT sp.id FROM stock_picking sp join sale_contract sc on sc.id = sp.sale_contract_id
                         join shipping_instruction si on si.id = sc.shipping_id WHERE si.contract_id = %(contract_id)s);
                    DELETE FROM stock_move WHERE picking_id in (SELECT sp.id FROM stock_picking sp join sale_contract sc on sc.id = sp.sale_contract_id
                         join shipping_instruction si on si.id = sc.shipping_id WHERE si.contract_id = %(contract_id)s);
                    DELETE FROM stock_picking WHERE id in (SELECT sp.id FROM stock_picking sp join sale_contract sc on sc.id = sp.sale_contract_id
                         join shipping_instruction si on si.id = sc.shipping_id WHERE si.contract_id = %(contract_id)s);
                    DELETE FROM delivery_order_line WHERE delivery_id in (SELECT de.id FROM delivery_order de join sale_contract sc on sc.id = de.contract_id 
                        join shipping_instruction si on si.id = sc.shipping_id WHERE si.contract_id = %(contract_id)s);
                    DELETE FROM delivery_order WHERE id in (SELECT de.id FROM delivery_order de join sale_contract sc on sc.id = de.contract_id 
                        join shipping_instruction si on si.id = sc.shipping_id  WHERE si.contract_id = %(contract_id)s);
                    DELETE FROM sale_contract_line WHERE contract_id in (SELECT sc.id FROM sale_contract sc join shipping_instruction si on si.id = sc.shipping_id  WHERE si.contract_id = %(contract_id)s);
                    DELETE FROM sale_contract WHERE id in (SELECT sc.id FROM sale_contract sc join shipping_instruction si on si.id = sc.shipping_id  WHERE si.contract_id = %(contract_id)s);
                    DELETE FROM shipping_instruction_line WHERE shipping_id in (SELECT id FROM shipping_instruction WHERE contract_id = %(contract_id)s);
                    DELETE FROM shipping_instruction WHERE id in (SELECT id FROM shipping_instruction WHERE contract_id = %(contract_id)s); ''' % ({'contract_id': self.id}))
            else:
                if self.contract_ids:
                    for line in self.contract_ids:
                        if line.state == 'done':
                            raise UserError(_('Unable to cancel S Contract %s as some receptions have already been done.\n\t You must first cancel related NLS.') % (self.name))
                        if line.state == 'approved':
                            if line.picking_ids:
                                for i in line.picking_ids:
                                    if i.state == 'done':
                                        raise UserError(_('Unable to cancel S Contract %s as some receptions have already been done.\n\t You must first cancel related GDN.') % (self.name))
                    self.env.cr.execute('''
                        DELETE FROM stock_pack_operation WHERE picking_id in (SELECT sp.id FROM sale_contract sc join stock_picking sp on sp.sale_contract_id = sc.id WHERE sc.scontract_id = %(contract_id)s);
                        DELETE FROM stock_move WHERE picking_id in (SELECT sp.id FROM sale_contract sc join stock_picking sp on sp.sale_contract_id = sc.id WHERE sc.scontract_id = %(contract_id)s);
                        DELETE FROM stock_picking WHERE sale_contract_id in (SELECT id FROM sale_contract WHERE scontract_id = %(contract_id)s);
                        DELETE FROM sale_contract_line WHERE contract_id in (SELECT id FROM sale_contract WHERE scontract_id = %(contract_id)s);
                        DELETE FROM sale_contract WHERE id in (SELECT id FROM sale_contract WHERE scontract_id = %(contract_id)s);''' % ({'contract_id': self.id}))
        self.write({'state': 'cancel'})
    
    def button_approve(self):
        for contract in self:
            if not contract.contract_line:
                raise UserError(_('You cannot approve a S Contract without any S Contract Line.'))
        self.write({'state': 'approved', 'user_approve': self.env.uid,
                    'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
    
    def button_done(self):
        if self.type == 'export' and not self.shipping_ids:
            raise UserError(_('You cannot done a S Contract without any SI.'))
        elif self.type == 'local' and not self.contract_ids:
            raise UserError(_('You cannot done a S Contract without any NLS.'))
        self.write({'state': 'done', 'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        
    def check_qty(self):
        product_qty = new_qty = 0.0
        for line in self.contract_line:
            if self.type == 'export':
                for shipping in self.shipping_ids:
                    if shipping.state != 'cancel':
                        if line.product_id == shipping.product_id:
                            product_qty += line.product_qty
                new_qty = shipping.product_qty - product_qty
    
    def create_si(self):
        if self.type == 'export':
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('sd_sale_contract.action_view_wizard_si')
            form_view_id = imd.xmlid_to_res_id('sd_sale_contract.view_wizard_si')
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'views': [[form_view_id, 'form']],
                'target': action.target,
                'res_model': action.res_model,
                }
        return result
    
    def action_view_shipping(self):
        action = self.env.ref('sd_sale_contract.action_shipping_instruction')
        result = action.read()[0]
        result['context'] = {}
        ship_ids = sum([order.shipping_ids.ids for order in self], [])
        if len(ship_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, ship_ids)) + "]), ('state','!=','cancel')]"
        elif len(ship_ids) == 1:
            res = self.env.ref('sd_sale_contract.view_shipping_instruction_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = ship_ids and ship_ids[0] or False
        return result
    
    def create_nls(self):
        if self.type == 'local':
            imd = self.env['ir.model.data']
            action = imd.xmlid_to_object('sd_sale_contract.action_view_wizard_nls')
            form_view_id = imd.xmlid_to_res_id('sd_sale_contract.view_wizard_nls')
            result = {
                'name': action.name,
                'help': action.help,
                'type': action.type,
                'context': action.context,
                'views': [[form_view_id, 'form']],
                'target': action.target,
                'res_model': action.res_model,
                }
        return result
    
    def action_view_contract_nls(self):
        action = self.env.ref('sd_sale_contract.action_sale_contract_local')
        result = action.read()[0]
        contract_ids = sum([order.contract_ids.ids for order in self], [])
        if len(contract_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, contract_ids)) + "]), ('state','!=','cancel')]"
        elif len(contract_ids) == 1:
            res = self.env.ref('sd_sale_contract.view_sale_contract_form', False)
            result['context'] = action.context
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = contract_ids and contract_ids[0] or False
        return result
    

########################################################################################################################################################################
    
    def split_scontract(self):
        new_record = 0
        for record in self:
            return {
                'name': 'Split Shipment',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'shipping.split',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_scontract_id': record.id},
            }
    
    def get_default_zone(self, warehouse_id):
        zone_obj = self.env['stock.zone']
        warehouse_obj = self.env['stock.warehouse']
        wh_info = warehouse_obj.browse(warehouse_id)
        zone_id = zone_obj.search([('warehouse_id', '=', wh_info.id)], limit=1)
        zone_id = zone_id and zone_id.id or 0
        return zone_id
    
    @api.model
    def _default_crop_id(self):
        crop_ids = self.env['ned.crop'].search([('state', '=', 'current')], limit=1)
        return crop_ids
    
    @api.depends('date','partner_id')
    def _get_franchise(self):
        date_check = '2017-12-1'
        date_check = datetime.strptime(date_check, DEFAULT_SERVER_DATE_FORMAT)
        for this in self:
            if this.partner_id and this.partner_id.name == 'Mitsui':
                this_date = this.date or False
                
                my_time = datetime.min.time()
                this_date = datetime.combine(this_date, my_time)
                
                if  this_date and this_date > date_check:
                    this.allowed_franchise = 0.7
                else:
                    this.allowed_franchise = 0.3
            else:
                this.allowed_franchise = 0.3
                
    
    
    x_final_price = fields.Float(related='p_contract_line_ids.final_price', string='Final Price')
    
    # erro du
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, readonly=True, states={'draft': [('readonly', False)]}, default=_default_warehouse_id)
    
    shipby_id = fields.Many2one('s.ship.by', string='Shipped By')
    crop_id = fields.Many2one('ned.crop', string='Crop', required=True, default=_default_crop_id)
    incoterms_id = fields.Many2one('account.incoterms', string='Term', required=False)
    x_coffee_type = fields.Char(string='Coffee Type', size=128)
    # sort_date = fields.Datetime(string='Sort Date', compute=get_sort_date, store=True)
    
    # Kiet them
    state = fields.Selection([('draft', 'New'), ('open', 'Open'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
             string='Status', readonly=True, copy=False, index=True, default='draft')
    status = fields.Selection([('Paco BWH', 'Paco BWH'), 
                               ('MBN BWH', 'MBN BWH'),
                               ('KTN BWH', 'KTN BWH'),
                               ('3rd party', '3rd party'),
                               ('Ned VN', 'Ned VN'),
                               ('Local sale', 'Local sale'),
                               ('Spot', 'Spot'),
                               ('Unallocated', 'Unallocated'),
                               ('Afloat', 'Afloat'),
                               ('Factory', 'Factory'),
                               ('Cancel', 'Cancel'),],
            string='Shipped By.',  copy=False, index=True)
    
    s_contract_link = fields.Many2one('s.contract', string='S Contract Allocated', domain=[('type','=','export')])
    p_contract_link = fields.Many2many('s.contract', 'scontract_pcontract_rel', 'sid', 'pid', string='P-Allocated')
    traffic_link_id = fields.Many2one('traffic.contract', string='Traffic Link')
    shipper_id = fields.Char(string='Shipper', size=256)

    shipment_date = fields.Date(string="Last shipment Date")
    pss = fields.Boolean(string="PSS")
    differential = fields.Float(string="Differential")
    fob_delivery = fields.Date(string="FOB Delivery")
    buyer_ref = fields.Char(string='Buyer Ref')
    delivery_place_id = fields.Many2one('delivery.place', string='Delivery Place', required=False)
    date_pss = fields.Date(string="Date Pss")

    check_by_cont =fields.Boolean(string="Check by cont")
    si_id = fields.Many2one(related='shipping_ids.contract_id',  string='SI')
    
    #Duy: them Allowed franchise
    allowed_franchise = fields.Float(compute='_get_franchise',string='Franchise', store=True)
    
    date_catalog = fields.Date(string="Date Catalog")
    p_contract_line_ids = fields.One2many('s.contract.line','p_contract_id', string="Product")

    p_quality = fields.Text(string='Quality')
    p_qty = fields.Float(string="Ctr. Q'ty (Kg)", related='p_contract_line_ids.product_qty', store=True)
    no_of_pack = fields.Float(string='No. of bag')
    wr_date = fields.Date(string='WR date')
    allocated_date = fields.Date(string='Allocation Date')
    wr_no = fields.Char(string='WR No.', size=256)
    instored_wei = fields.Float(string='Instored weight (Kg)')
    #   QC
    bb_info = fields.Char(string='BB', size=128)
    fm_info = fields.Char(string='FM', size=128)
    mc_info = fields.Char(string='MC', size=128)
    abv_scr = fields.Char(string='Abv Scr', size=128)
    # Allocate
    # qty_allocated = fields.Float(string='Allocated (Kg)')
    # bag_allocated = fields.Float(string='Allocated Bag No.')
    # tb_qty_alloca = fields.Float(string='To be Allocated (Kg)')
    # -> Sua thanh fuction fiedsl doi addon ned_vn
    # Export
    doc_wei = fields.Float(string='Docs Weight')
    real_wei = fields.Float(string='Real NW ex-BW')
    loss_wei = fields.Float(string='Loss')
    #Kiet: 
    date = fields.Date(string='Entity date', readonly=True,  states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    
    client_ref = fields.Char(string="Client ref.")
    pss_type = fields.Selection([('SAS','SAS'),('SAN','SAN'),('SAP','SAP'),('PSS','PSS'),('PSS+OTS','PSS+OTS'),('No','No')],string=" Pss type", copy = True)
    
    start_of_ship_period = fields.Date(string="Start of Ship. period contract",copy = True )
    end_of_ship_period = fields.Date(string="End of ship. Period contract")
     
    delivery_type= fields.Selection([('50','Shipment'),('10','Delivery')],string="Delivery type")
    end_of_ship_period_actual = fields.Date(string="End of ship. Period (actual)")
    pic_id = fields.Many2one('s.pic', string='PIC')
    precalculated_freight_cost = fields.Float(string="Precalculated freight Cost")
    act_freight_cost = fields.Float(string="Precalculated freight Cost")
    freight = fields.Float(string="freight")
    shipt_month = fields.Many2one('s.period', string="Shipt month")
    

    bill_no = fields.Char(string="B/L no.")
    bill_date = fields.Date(string="ETD/ BL date")
    si_received_date = fields.Date(string="SI received date")
    pss_send_schedule = fields.Date(string="1st PSS sent date")
    si_sent_date = fields.Date(string="SI sent date")
    nominated_etd = fields.Date(string="Nominated ETD")
    od_doc_rec_date = fields.Date(string="O.docs rec. date")
    od_doc_sent_date = fields.Date(string="O.docs Sent. date")
    od_doc_rec_awb = fields.Char(string="O.docs rec. AWB No.", size=256)
    awb_sent_no = fields.Char(string="AWB sent No.", size=256)
    
    
    pss_send_schedule = fields.Date(string="1st PSS sent date")
    pss_sent = fields.Boolean(string="PSS Sent")
    pss_sent_date = fields.Date(string="PSS Sent Date")
    pss_approved = fields.Boolean(string="PSS Approved")
    pss_approved_date = fields.Date(string='PSS approved date')
    pss_amount_send = fields.Char(string='Amount of PSS sent', size=256)
    pss_late_ontime = fields.Char(string='Late/Ontime PSS sending', size=128)
    act_freight_cost = fields.Float(string='Actual Freight Cost')




    shipping_line_id = fields.Many2one('shipping.line', string='Shipping Line')
    factory_etd = fields.Date(string = 'Factory ETD')
    booking_ref_no = fields.Char(string='Booking No./ BL No.', index=True)
    booking_date = fields.Date('Booking date')
    reach_date = fields.Date('Reach Date')
    ico_permit_no = fields.Char(string='ICO No.')
    ico_permit_date = fields.Date('ICO Permit Date')
    transaction = fields.Char(string='Transaction')
    vessel_flight_no = fields.Char(string='Vessel/Flight No.')
    eta = fields.Date(string='ETA')
    late_ship_end = fields.Date(string='Late Ship - BL vs End period')
    late_ship_est = fields.Date(string='Late Ship - BL vs nominated ETD')
    cause_by = fields.Text(string="Caused By")
    remarks = fields.Char(string="Important remarks")
    
    x_is_bonded = fields.Boolean(string='Is Bonded')
    
    
    # nam o addon Ned_stock
    # wr_line = fields.Many2one('stock.stack', string='WR')
    # init_qty = fields.Float(related='wr_line.init_qty', string='In Weight', digits=(12, 0))
    # out_qty = fields.Float(related='wr_line.out_qty', string='Out Weight', digits=(12, 0))
    # remaining_qty = fields.Float(related='wr_line.remaining_qty', string='Balance Weight', digits=(12, 0))
    
    
    @api.depends('p_contract_line_ids','p_contract_line_ids.remainning_qty')
    def _total_remaining_qty(self):
        for order in self:
            total_remaining_qty = 0
            for line in order.p_contract_line_ids:
                total_remaining_qty += line.remainning_qty
            order.total_remaining_qty = total_remaining_qty
    
    total_remaining_qty = fields.Float(compute='_total_remaining_qty', digits=(16, 0) , string='Total Remaining Qty', store =True)

    certificate_id = fields.Many2one('ned.certificate', string='Certificate')
    # packing_id = fields.Many2one('ned.packing', string='Packing')
    packing_id = fields.Many2one(related='p_contract_line_ids.packing_id',  string='Packing', store = True)
    
    standard_id = fields.Many2one('product.product', string='Standard')
    license_allocation_ids = fields.One2many('s.contract.license.allocation', 's_contract_id', 
                                             string='License Allocations')
    
    pss_sent_ids = fields.One2many('pss.sent', 's_contract_id', string='Pss')

    @api.onchange('license_allocation_ids')
    def _onchange_license_allocation_ids_allocation_qty(self):
        for allocation in self.license_allocation_ids:
            license = allocation.license_id
            if license.balance < 0:
                raise Warning(_('Your allocation for license %s may cause a negative balance (%s)' 
                                % (license.name, license.balance)))

        total_allocated_qty = sum(self.license_allocation_ids.mapped('allocation_qty'))
        contract_qty = sum(self.contract_line.mapped('product_qty'))
        if total_allocated_qty > contract_qty:
            raise Warning(_('Total allocated quantity (%s) exceeds the product quantity of this contract (%s)' 
                            % (total_allocated_qty, contract_qty)))

    def _allocate_contract_certificate_license(self, certificate, product_qty, total_allocated_qty=0):
        today = fields.Date.context_today(self)
        # A valid license for S Contract should not be expired, and have a valid balance
        domain = [('certificate_id', '=', certificate.id), ('expired_date', '>', today), ('balance', '>', 0)]
        license = self.env['ned.certificate.license'].search(domain, limit=1, order="expired_date")
        if license:
            if license.balance >= product_qty:
                allocation_qty = product_qty
                spare_qty = 0
            elif license.balance < product_qty:
                allocation_qty = license.balance
                spare_qty = product_qty - license.balance
            self.env['s.contract.license.allocation']\
                .create({'s_contract_id': self.id,
                         'license_id': license.id,
                         'allocation_qty': allocation_qty})
            total_allocated_qty += allocation_qty
            if spare_qty:
                return self._allocate_contract_certificate_license(certificate, spare_qty, total_allocated_qty)
        return total_allocated_qty

    def allocate_s_contract_license(self):
        # contract_line is always singleton even if it is One2many field,
        # due to all those written compute functions use it as singleton.
        # Why don't use mapped()?
        for line in self.contract_line.filtered(lambda line: line.certificate_id):
            total_allocated_qty = sum(self.license_allocation_ids.mapped('allocation_qty'))
            # singleton, contract qty would equal to qty in contract line
            to_allocate_qty = line.product_qty - total_allocated_qty
            if to_allocate_qty > 0:
                total_allocated_qty = self._allocate_contract_certificate_license(
                    line.certificate_id, to_allocate_qty, total_allocated_qty)
                if total_allocated_qty < line.product_qty:
                    raise Warning(_('Allocated quantity (%s) does not fulfil the product quantity (%s)!' 
                                    % (total_allocated_qty, line.product_qty)))
    
################          NED Contract Vn     ###################################################################################################################################
    origin  = fields.Selection([('VN', 'VN'),
                               ('ID', 'ID'),
                               ('IN', 'IN'),
                               ('CO', 'CO'),
                               ('LA', 'LA'),
                               ('CI', 'CI'), # Ivory Coast
                               ('HN', 'HN'), # Honduras
                               ('BR', 'BR'), # Brazil
                               ('GU', 'GU'), # Guatemala
                               ('UG', 'UG'), # Uganda
                               ('PE', 'PE') # Peru
                               ], string='Origin', copy = True) # Guatemala
    
    origin_new  = fields.Many2one('res.country', string="Origin")

    eudr_check = fields.Boolean(string='Is EUDR', default=False)
    combine_check = fields.Boolean(string='Is Combined', default=False)
    certificated_ids = fields.Many2many('ned.certificate', 'certificate_s_contract', 's_contract_id', 'certificate_id',
                                        compute="_compute_list_certificate", store=True, string="Cer Combine")
    # char_certificate = fields.Char(string='Char Certificate', default='[]')

    @api.depends("eudr_check", "combine_check", 'certificate_id')
    def _compute_list_certificate(self):
        if self.certificate_id:
            cer_arr = []
            if self.eudr_check:
                if self.combine_check:
                    cer_list = self.env['ned.certificate'].search(['|', '|', ('name','=',self.certificate_id.name),('name','=','EUDR'),('name','=like',self.certificate_id.name + '-%')])
                    cer_arr = cer_list
                else:
                    cer_list = self.env['ned.certificate'].search(['|', ('name','=',self.certificate_id.name),('name','=','EUDR')])
                    for cer in cer_list:
                        cer_arr.append(cer.id)
            else:
                self.combine_check = False
                cer_arr = self.certificate_id
            self.certificated_ids = cer_arr

    def copy(self, default=None):
        result = super(SContract, self).copy({
            'shipping_ids': False,
            'contract_ids': False,
        })
        return result

# SON dim: Áp loại License cho S Contract từ đó mới load loại License tương ứng trong Line
    # @api.depends('contract_line', 'contract_line.certificate_id')
    # def _compute_list_certificate(self):
    #     if self.contract_line:
    #         for line in self.contract_line:
    #             if line.certificate_id:
    #                 if line.certificate_id.combine:
    #                     another_certificate = self.env['ned.certificate'].search([
    #                         ('combine', '=', True)
    #                     ])
    #                     self.certificated_ids = [(6, 0, another_certificate.ids)]
    #                 else:
    #                     self.certificated_ids = [(6, 0, line.certificate_id.ids)]
    #             else:
    #                 self.certificated_ids = [(5, 0)]

    qty_allocated = fields.Float(string='Allocated (Kg)', compute='_compute_allocated')
    bag_allocated = fields.Float(string='Allocated Bag No.', compute='_compute_allocated')
    tb_qty_alloca = fields.Float(string='To be Allocated (Kg)', compute='_compute_allocated')
    tb_bag_alloca = fields.Float(string='To be Allocated (bag)', compute='_compute_allocated')

    def _compute_allocated(self):
        for record in self:
            sale_contract_detail = self.env['sale.contract.deatail'].search([
                ('p_contract_id', '=', record.id),
                ('sp_id', '!=', False),
                ('sp_id.x_is_bonded', '=', True)
            ])
            stock_stack = self.env['stock.lot'].search([
                ('p_contract_id', '=', record.id)
            ])
            if sale_contract_detail:
                record.qty_allocated = sum(detail.tobe_qty for detail in sale_contract_detail)
                record.bag_allocated = sum(detail.tobe_bag for detail in sale_contract_detail)
            else:
                record.bag_allocated = 0
                record.qty_allocated = 0
            if stock_stack:
                record.tb_qty_alloca = (sum(detail.net_qty for detail in stock_stack)) - \
                                       sum(detail.tobe_qty for detail in sale_contract_detail)
                record.tb_bag_alloca = record.no_of_pack - record.bag_allocated
            else:
                record.tb_qty_alloca = 0
                record.tb_bag_alloca = 0

    # @api.model
    # def create(self, vals):
    #     if 'name' in vals:
    #         p_contract = self.env['s.contract'].search([
    #             ('name', '=', vals['name'].strip())
    #         ])
    #         if p_contract:
    #             raise UserError(_("Duplicate name for P Contract, please check again!"))
    #     return super(SContract, self).create(vals)

#######################################################################################

class SContractLicenseAllocation(models.Model):
    _name = 's.contract.license.allocation'
    _description = 'S Contract License Allocation'

    s_contract_id = fields.Many2one('s.contract', string='SNo.')
    license_id = fields.Many2one('ned.certificate.license', string='License')
    allocation_qty = fields.Float('Allocation Qty', digits=(12, 0))
    
    
    ########################################### ned_vn#########################################
    product_id = fields.Many2one(related='s_contract_id.product_id',  string='Product', store=True)
    grade_id = fields.Many2one(related='product_id.categ_id', store=True, string='Grade')
    
    

    @api.constrains('allocation_qty')
    def _check_allocation_qty(self):
        for i in self:
            if i.allocation_qty <= 0:
                raise ValidationError(_('The allocated quantity must be greater than 0'))
    
    
    
    
    


    

    
    
    
    
    
    
    
    
    
    
    

    
    
    
    
