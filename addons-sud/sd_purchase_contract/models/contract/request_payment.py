# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from pytz import timezone
import time

class RequestPayment(models.Model):
    _name = "request.payment"
    _order = "id desc"
    
    
    
    @api.depends('invoice_ids')  
    def _compute_invoices(self):
        for contract in self:
            invoices = self.env['account.move']
            for line in contract.invoice_ids: 
                invoices = (line.filtered(lambda r: r.state != 'cancel'))
            contract.invoice_ids = invoices
            contract.invoice_count = len(invoices)
    
    @api.model
    def create(self, vals):
        if vals.get('purchase_contract_id'):
            contract = self.env['purchase.contract'].browse(vals.get('purchase_contract_id'))
            vals['name'] = len(contract.request_payment_ids) + 1
        result = super(RequestPayment, self).create(vals)
        return result
    
    def btt_approved(self):
        self.state ='approved'
        
    def btt_cancel(self):
        self.state ='request'
        
    @api.model
    def default_get(self, fields):
        res = {}
        val = []
        month =1
        partner_id = self._context.get('partner_id') or False
        type = self._context.get('type') or False
        while(month<6):
            val.append((0, 0, {
                 'month':str(month),
                 'rate':0.0
                 }))
            month +=1
        res.update({'users_request_id':self.env.uid,'rate_ids':val,'partner_id':partner_id,'type':type,'state':'request'})
        return res
    
    @api.depends('request_payment_ids','request_amount','advance_payment_quantity')
    def _compute_request_payment(self):
        for request in self:
            total_payment = 0.0
            for line in request.request_payment_ids.filtered(lambda x: x.state == 'posted'):
                total_payment += line.amount
            request.total_payment = total_payment   
#             if not request.advance_price:
#                 request.advance_payment_quantity = 0.0
#             else:
#                 request.advance_payment_quantity = request.request_amount / request.advance_price
            
            if not request.advance_payment_quantity:
                request.advance_price = 0.0
            else:
                request.advance_price = request.request_amount / request.advance_payment_quantity
                
            request.total_remain = request.request_amount - total_payment
            if request.total_remain == 0.0:
                if total_payment != 0:
                    request.state = 'paid'
            # else:
            #     request.state = 'approved_director'
    
    def _compute_provisional_amount(self):
        for line in self:
            amount =0.0
            for rate in line.rate_ids:
                amount  += rate.provisional_rate or 0.0
            line.provisional_amount = amount
    
    def _compute_refunded(self):
        for line in self:
            if line.purchase_contract_id.type =='consign':
                payment_refunded = open_advance = 0.0
                for payment in line.request_payment_ids:
                    payment_refunded  += payment.payment_refunded or 0.0
                    open_advance  += payment.open_advance or 0.0
                line.payment_refunded = payment_refunded or 0.0
                line.open_advance = open_advance or 0.0
            else:
                line.payment_refunded =  0.0
                line.open_advance =  0.0
    
    @api.depends('request_payment_ids')
    def _compute_payment(self):
        for request in self:
            orders =False
            for line in request.request_payment_ids: 
                orders = line.filtered(lambda r: r.state != 'draft')
            if not orders:
                request.payment_count = 0
            else:
                request.payment_count = len(orders)
    
    def action_view_payment(self):
        action = self.env.ref('account.action_account_payments_payable')
        result = action.read()[0]
        
        #override the context to get rid of the default filtering
        result['context'] = {'partner_type': 'supplier'}

        result['domain'] = "[('id', 'in', " + str(self.request_payment_ids.ids) + ")]"
        res = self.env.ref('account.account.view_account_payment_register_form', False)
        result['views'] = [(res and res.id or False, 'tree')]
        result['res_id'] = self.request_payment_ids.ids 
        return result
    
    def action_request_register_payment(self):
        
        
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            #'domain':self.request_payment_ids.ids,
            'context': {
                'active_model': 'request.payment',
                'active_ids': self.ids,
                'default_partner_type':'supplier',
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }
    
    def _get_printed_report_name(self):
        self.ensure_one()
        report_name = (_('Request Payment - %s')%(self.name))
        return report_name
        
        
    
    payment_count = fields.Integer(compute='_compute_payment', string='Receptions', default=0)
    name = fields.Char(string='Request payment')
    date = fields.Date('Request Date', default=fields.Datetime.now)
    partner_id = fields.Many2one('res.partner', string='Partner')
    # request_amount = fields.Float(string = 'Request Amount',digits=(12, 0))

    chinhanh = fields.Char(string= 'Chi Nhánh', required=True)
    account_no = fields.Char(string='Account No', required=True)

    songay = fields.Integer(string='Số ngày')          
    advance_price = fields.Float(string='Advance Price',digits=(12, 0),  default=0.0, compute='_compute_request_payment')
    advance_payment_quantity = fields.Float(string='Advance payment quantity',digits=(12, 0))
    company_id = fields.Many2one('res.company', string='Company', required=False,
              default=lambda self: self.env['res.company']._company_default_get('request.payment'))
    purchase_contract_id = fields.Many2one('purchase.contract', 'Purchase contract', required=False)
    request_payment_ids = fields.One2many('account.payment','request_payment_id', string='Payment', copy=False)
    total_payment = fields.Float(string='Total Payment', store=True, readonly=False, compute='_compute_request_payment',digits=(12, 0))
    total_remain = fields.Float(string='Total Remain', store=True, readonly=False, compute='_compute_request_payment',digits=(12, 0))
    users_request_id = fields.Many2one('res.users', string='Users Request',default=lambda self: self._uid)
    # state = fields.Selection([('request', 'Request'), ('approved', 'Approved'),('paid','Paid')],
    #                       string='State',readonly=False, copy=False, index=True,default='request')
    rate_ids = fields.One2many('interest.rate','request_id', string='Request payment')
    partner_bank_id = fields.Many2one('res.partner.bank',string= 'Partner bank', required=False)
    
    provisional_amount = fields.Float(string='Lãi tạm tính',compute='_compute_provisional_amount',digits=(12, 0))
    
    payment_refunded = fields.Float(string='Refunded',compute='_compute_refunded',digits=(12, 0))
    open_advance = fields.Float(string='Open Advance',compute='_compute_refunded',digits=(12, 0)) 
    type = fields.Selection(selection=[('consign', 'Consignment Agreement'), ('purchase', 'Purchase Contract')],
                            related='purchase_contract_id.type',  string='Type',store = True)
    
    amount_approved = fields.Float(string='Amount Approved', digits=(12, 0))
    
    bank_id = fields.Many2one('res.bank',related='partner_bank_id.bank_id',  string='Bank',store = False)
    
    type_payment = fields.Selection(selection=[('advance_payment', 'Advance payment'), ('Payment', 'Payment')],default="Payment", string='Payment Type')
    payment_quantity = fields.Float(string='Payment Quantity')
    fx_price = fields.Float(string='FX')
    
    @api.onchange('partner_bank_id')
    def _onchange_partner_bank(self):
        if not self.partner_bank_id:
            return
        else:
            self.chinhanh = self.partner_bank_id.bank_id.bic
            self.account_no = self.partner_bank_id.acc_number

    def print_payment_request(self):
        return self.env.ref(
            'sd_purchase_contract.payment_npe_report').report_action(self)
    
    
    def print_advance_payment(self):
        return self.env.ref(
            'sd_purchase_contract.advance_payment_report').report_action(self)
    
    def print_printout_payment_npv(self):
        return self.env.ref(
            'sd_purchase_contract.printout_payment_npv_report').report_action(self)

##############################NED Contract  VN###################################################################
    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('request', 'Request'),
    #     ('security', 'Security'),
    #     ('purchasing', 'Purchasing'),
    #     ('approved', 'Accounting 1st'),
    #     ('accounting_2', 'Accounting 2nd'),
    #     ('approved_director', 'Approve by Director'),
    #     ('paid', 'Paid')
    # ], string='State', readonly=False, copy=False, index=True, default='draft')
    state = fields.Selection([
        ('request', 'Request'),
        ('purchasing', 'Purchasing'),
        ('approved', 'Accounting 1st'),
        ('accounting_2', 'Accounting 2nd'),
        ('approved_director', 'Approve by Director'),
        ('paid', 'Paid')
    ], string='State', readonly=False, copy=False, index=True, default='request')
    market_price = fields.Float(string='Market Price')
    provisional_price = fields.Float(string='Provisional Price')
    fixation_amount = fields.Float(string='Fixation Amount')
    full_fixation = fields.Boolean(string='Full Fixation', default=False)
    fix_price = fields.Float(string='Fix Price')
    diff_price = fields.Float(string="Different Price")
    ref_price = fields.Float(string='Reference Price')
    rate = fields.Float(string='Rate')
    ptbt_fix_price = fields.Many2one('ptbf.fixprice')

    @api.depends('acc_number', 'bank_id')
    def name_get(self):
        result = []
        for bank in self:
            name = bank.bank_id.name
            if bank.bank_id.bic:
                name = bank.bank_id.name + ' - ' + bank.bank_id.bic
            result.append((bank.id, name))
        return result

    @api.onchange('market_price')
    def onchange_provisional_price(self):
        if self.market_price:
            self.provisional_price = self.market_price * (70.00 / 100)

    @api.model
    def default_get(self, fields): 
        res = super(RequestPayment, self).default_get(fields)
        if self._context.get('purchase_contract_id'):
            res['purchase_contract_id'] = self._context.get('purchase_contract_id')
            contract_id = self.env['purchase.contract'].browse(self._context.get('purchase_contract_id'))
            count = len(contract_id.request_payment_ids) + 1
            res['partner_id'] = contract_id.partner_id.id
            res['name'] = count
            res['type_payment'] = 'Payment'
        return res
    
    # @api.multi
    # def get_purchase_id(self):
    #     if self.env.context:
    #         print ' default price  >>>>   ', self.env.context
    #         if self.env.context.get('request_id', 'active_id'):
    #             self.purchase_contract_id = self.env.context.get('request_id', 'active_id')

    # purchase_contract_id = fields.Many2one('purchase.contract', )
    line_ids = fields.One2many('request.payment.line', 'request_id', 'Detail of Payment')
    line_ids_npe = fields.One2many('request.payment.line', 'request_id_npe', 'Detail of Payment')
    line_nvp_convert_ids = fields.One2many('request.payment.line.convert', 'request_id', 'Detail of Payment')
    source = fields.Char(string='Source', related='purchase_contract_id.origin')
    request_amount = fields.Float(string='Request Amount', digits=(12, 0), compute='_compute_request_amount', store=True)
    request_amount_temp = fields.Float(string='Input Request Amount')

    @api.depends('line_ids', 'line_ids.amount', 'line_ids_npe', 'line_ids_npe.amount',
                 'line_nvp_convert_ids', 'line_nvp_convert_ids.advance_payment', 'request_amount_temp')
    def _compute_request_amount(self):
        amount = 0
        for i in self:
            i.request_amount = i.request_amount_temp
            if i.line_ids:
                if i.type == 'purchase' and not i.source:
                    for j in i.line_ids:
                        amount += (j.price_unit * j.quantity_payment) * (float(j.percent)/100)
                    i.request_fun_amount = amount
                    i.request_amount = i.request_fun_amount
                if i.type == 'consign':
                    for j in i.line_ids_npe:
                        amount += j.amount
                    i.request_fun_amount = amount
                    i.request_amount = i.request_fun_amount
                if i.type == 'purchase' and i.source:
                    for j in i.line_nvp_convert_ids:
                        amount += j.advance_payment
                    i.request_fun_amount = amount
                    i.request_amount = i.request_fun_amount
                if i.type == 'ptbf':
                    for j in i.line_ids:
                        amount += j.amount
                    i.request_fun_amount = amount
                    i.request_amount = i.request_fun_amount
    request_fun_amount = fields.Float(string="Request Amount", compute= '_compute_request_amount', store= True)
#    price_unit = fields.Float('Price Unit') #, default=get_price_unit)

    # @api.depends('delivery_id')
    # def get_qty_payment(self):
    #     qty_payment = 0
    #     deli_obj = self.env['ned.security.gate.queue']
    #     for i in self:
    #         qty_payment = 0
    #         for idd in i.delivery_id:
    #             qty_payment += deli_obj.browse(idd.id).approx_quantity
    #         unit_price = i.purchase_contract_id.contract_line[0].price_unit
    #         i.request_amount = qty_payment * unit_price * 0.7
    #         i.vehicle_no = i.delivery_id.license_plate

    # @api.onchange('grn_id')
    # def get_qty_paymentgrn(self):
    #     qty_payment = 0
    #     deli_obj = self.env['stock.picking']
    #     for i in self:
    #         qty_payment = 0
    #         for idd in i.grn_id:
    #             qty_payment += deli_obj.browse(idd.id).move_weight[0].init_qty
    #         unit_price = i.purchase_contract_id.contract_line[0].price_unit
    #         i.request_amount = qty_payment * unit_price * 0.7
    #         i.vehicle_no = i.delivery_id.license_plate

    def approve_purchasing(self):
        for record in self:
            record.write({
                'state': 'purchasing'
            })

    def approve_accounting_v2(self):
        for record in self:
            record.write({
                'state': 'accounting_2'
            })

    def approve_by_director(self):
        for record in self:
            record.write({
                'state': 'approved_director'
            })

    def search_data_load(self, delivery_ids):
        # Search delivery registration when it not be DONE by Warehouse -> 70%
        delivery = self.env['ned.security.gate.queue'].search([
            ('state', 'in', ['pur_approved', 'qc_approved']),
            ('arrivial_time', '!=', False),
            ('supplier_id', '=', self.purchase_contract_id.partner_id.id),
            ('id', 'not in', delivery_ids)
        ]).filtered(lambda x: str((datetime.strptime(x.arrivial_time, DATETIME_FORMAT) + timedelta(
            hours=7)).date()) >= self.purchase_contract_id.date_order
                              and self.purchase_contract_id.product_id.id in x.product_ids.ids)
        # Search delivery when it create picking not in state DONE -> 90%
        delivery_approve = self.env['stock.picking'].search([
            ('security_gate_id', '!=', False),
            ('total_init_qty', '>', 0),
            ('state', '!=', 'done'),
            ('partner_id', '=', self.purchase_contract_id.partner_id.id),
        ]).mapped('security_gate_id').filtered(lambda x: x.id not in delivery_ids and x.arrivial_time
                                                         and str(
            (datetime.strptime(x.arrivial_time, DATETIME_FORMAT) + timedelta(
                hours=7)).date()) >= self.purchase_contract_id.date_order
                                                         and self.purchase_contract_id.product_id.id in x.product_ids.ids)
        # Search delivery when it's GRN is DONE -> 100%
        delivery_done = self.env['stock.picking'].search([
            ('security_gate_id', '!=', False),
            ('total_init_qty', '>', 0),
            ('state', '=', 'done'),
            ('partner_id', '=', self.purchase_contract_id.partner_id.id),
        ]).mapped('security_gate_id').filtered(lambda x: x.id not in delivery_ids and x.arrivial_time and str(
            (datetime.strptime(x.arrivial_time, DATETIME_FORMAT) + timedelta(
                hours=7)).date()) >= self.purchase_contract_id.date_order
                                                         and self.purchase_contract_id.product_id.id in x.product_ids.ids)

        return delivery, delivery_approve, delivery_done

    def load_data(self):
        if self.type in ['purchase', 'consign'] and not self.purchase_contract_id.nvp_ids:
            delivery_ids = []
            if self.line_ids:
                delivery_ids = self.line_ids.mapped('delivery_id').ids
            delivery, delivery_approve, delivery_done = self.search_data_load(delivery_ids)

            self.create_70_percent_request_payment_line(delivery)

            self.create_90_percent_request_payment_line(delivery_approve)

            self.create_100_percent_request_payment_line(delivery_done)
        if self.type == 'purchase' and self.purchase_contract_id.nvp_ids:
            nvp = self.env['npe.nvp.relation'].search([
                ('npe_contract_id', 'in', self.purchase_contract_id.nvp_ids.mapped('npe_contract_id').ids),
                ('contract_id', '<', self.purchase_contract_id.id)
            ]).mapped('contract_id').filtered(lambda x: x.type == 'purchase')
            for i in nvp:
                if not i.request_payment_ids:
                    raise UserError(_("You need to start with: %s before load in this contract") % i.name)
                if not i.request_payment_ids.mapped('line_nvp_convert_ids'):
                    raise UserError(_("You need to start with: %s before load in this contract") % i.name)
            if not nvp:
                flag = True
                npe = sorted(self.purchase_contract_id.nvp_ids.mapped('npe_contract_id'), key=lambda x: x.date_order)
                if flag:
                    total_qty = self.purchase_contract_id.total_qty
                    for con in npe:
                        for line in sorted(con.request_payment_ids, key=lambda x: x.name):
                            sum_advance_payment = sum(i.quantity_payment for i in line.line_ids_npe)
                            if total_qty > 0:
                                line.fixation_amount = sum_advance_payment
                                if total_qty >= sum_advance_payment:
                                    rate_interest = self.env['interest.rate'].search([
                                        ('request_id', '=', line.id),
                                    ])
                                    for i in rate_interest:
                                        total_day = (datetime.strptime(i.date_end, '%Y-%m-%d') - datetime.strptime(i.date, '%Y-%m-%d')).days
                                        value = {
                                            'fixation_qty': sum_advance_payment,
                                            'contract_id': con.id,
                                            'provisional': line.provisional_price,
                                            'advance_payment': line.request_amount,
                                            'date_from': i.date,
                                            'date_to': i.date_end,
                                            'total_days': total_day,
                                            'rate_date': i.rate,
                                            'interest': (line.request_amount * total_day *
                                                         i.rate) / 30,
                                            'request_id': self.id
                                        }
                                        self.env['request.payment.line.convert'].create(value)

                                    line.full_fixation = True
                                    total_qty = total_qty - sum_advance_payment
                                    line.fixation_amount = 0
                                    continue
                                if total_qty < sum_advance_payment:
                                    rate_interest = self.env['interest.rate'].search([
                                        ('request_id', '=', line.id)
                                    ])
                                    for i in rate_interest:
                                        total_day = (datetime.strptime(i.date_end, '%Y-%m-%d') - datetime.strptime(
                                            i.date, '%Y-%m-%d')).days
                                        value = {
                                            'fixation_qty': total_qty,
                                            'contract_id': con.id,
                                            'provisional': line.provisional_price,
                                            'advance_payment': total_qty * line.provisional_price,
                                            'date_from': i.date,
                                            'date_to': i.date_end,
                                            'total_days': total_day,
                                            'rate_date': i.rate,
                                            'interest': (total_qty * line.provisional_price * total_day *
                                                         i.rate) / 30,
                                            'request_id': self.id
                                        }
                                        self.env['request.payment.line.convert'].create(value)
                                    line.fixation_amount = sum_advance_payment - total_qty
                                    total_qty = 0

            if nvp:
                npe = sorted(self.purchase_contract_id.nvp_ids.mapped('npe_contract_id'), key=lambda x: x.date_order)
                total_qty = self.purchase_contract_id.total_qty
                for con in npe:
                    for line in sorted(con.request_payment_ids.filtered(
                            lambda x: x.fixation_amount > 0 or not x.full_fixation), key=lambda x: x.name):
                        sum_advance_payment = sum(i.quantity_payment for i in line.line_ids_npe)
                        rate_interest = self.env['interest.rate'].search([
                            ('request_id', '=', line.id),
                        ])
                        if line.fixation_amount > 0:
                            if total_qty >= line.fixation_amount:
                                for i in rate_interest:
                                    total_day = (datetime.strptime(i.date_end, '%Y-%m-%d') -
                                                 datetime.strptime(i.date, '%Y-%m-%d')).days
                                    value = {
                                        'fixation_qty': line.fixation_amount,
                                        'contract_id': con.id,
                                        'provisional': line.provisional_price,
                                        'advance_payment': line.fixation_amount * line.provisional_price,
                                        'date_from': i.date,
                                        'date_to': i.date_end,
                                        'total_days': total_day,
                                        'rate_date': i.rate,
                                        'interest': (line.fixation_amount * line.provisional_price * total_day *
                                                     i.rate) / 30,
                                        'request_id': self.id
                                    }
                                    self.env['request.payment.line.convert'].create(value)
                                line.full_fixation = True
                                total_qty = total_qty - line.fixation_amount
                                line.fixation_amount = 0
                                continue

                            if total_qty < line.fixation_amount:
                                for i in rate_interest:
                                    total_day = (datetime.strptime(i.date_end, '%Y-%m-%d') -
                                                 datetime.strptime(i.date, '%Y-%m-%d')).days
                                    value = {
                                        'fixation_qty': total_qty,
                                        'contract_id': con.id,
                                        'provisional': line.provisional_price,
                                        'advance_payment': total_qty * line.provisional_price,
                                        'date_from': i.date,
                                        'date_to': i.date_end,
                                        'total_days': total_day,
                                        'rate_date': i.rate,
                                        'interest': (total_qty * line.provisional_price * total_day *
                                                     i.rate) / 30,
                                        'request_id': self.id
                                    }
                                    self.env['request.payment.line.convert'].create(value)
                                line.fixation_amount = line.fixation_amount - total_qty
                        if line.fixation_amount == 0 and not line.full_fixation:
                            if total_qty >= sum_advance_payment:
                                for i in rate_interest:
                                    total_day = (datetime.strptime(i.date_end, '%Y-%m-%d') -
                                                 datetime.strptime(i.date, '%Y-%m-%d')).days
                                    value = {
                                        'fixation_qty': sum_advance_payment,
                                        'contract_id': con.id,
                                        'provisional': line.provisional_price,
                                        'advance_payment': line.request_amount,
                                        'date_from': i.date,
                                        'date_to': i.date_end,
                                        'total_days': total_day,
                                        'rate_date': i.rate,
                                        'interest': (line.request_amount * total_day *
                                                     i.rate) / 30,
                                        'request_id': self.id
                                    }
                                    self.env['request.payment.line.convert'].create(value)
                                line.full_fixation = True
                                total_qty = total_qty - sum_advance_payment
                                line.fixation_amount = 0
                                continue
                            if total_qty < sum_advance_payment:
                                for i in rate_interest:
                                    total_day = (datetime.strptime(i.date_end, '%Y-%m-%d') -
                                                 datetime.strptime(i.date, '%Y-%m-%d')).days
                                    value = {
                                        'fixation_qty': total_qty,
                                        'contract_id': con.id,
                                        'provisional': line.provisional_price,
                                        'advance_payment': total_qty * line.provisional_price,
                                        'date_from': i.date,
                                        'date_to': i.date_end,
                                        'total_days': total_day,
                                        'rate_date': i.rate,
                                        'interest': (total_qty * line.provisional_price * total_day *
                                                     i.rate) / 30,
                                        'request_id': self.id
                                    }
                                    self.env['request.payment.line.convert'].create(value)
                                line.fixation_amount = sum_advance_payment - total_qty

    def load_data_2(self):
        if not self.ptbt_fix_price:
            delivery_ids = []
            if self.line_ids:
                delivery_ids = self.line_ids.mapped('delivery_id').ids
            delivery, delivery_approve, delivery_done = self.search_data_load(delivery_ids)

            self.create_70_percent_request_payment_line(delivery)

            self.create_90_percent_request_payment_line(delivery_approve)

            self.create_100_percent_request_payment_line(delivery_done)

    def create_70_percent_request_payment_line(self, delivery):
        if delivery:
            for i in delivery:
                request_payment_line = self.env['request.payment.line'].search([
                    ('delivery_id', '=', i.id)
                ])
                if ((70.00 / 100) * i.approx_quantity) - (
                        sum(j.quantity_payment for j in request_payment_line)) > 0:
                    if self.type == 'purchase':
                        value = {
                            'delivery_id': i.id,
                            'name': i.license_plate,
                            'percent': '70',
                            'estimated_quantity': i.approx_quantity,
                            'limit_quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'price_unit': self.purchase_contract_id.price_unit,
                            'supplier_id': self.purchase_contract_id.partner_id and self.purchase_contract_id.partner_id.id or False,
                            'amount': ((70.00 / 100) * i.approx_quantity) * self.purchase_contract_id.price_unit,
                            'request_id': self.id
                        }
                        self.env['request.payment.line'].create(value)
                    if self.type == 'consign':
                        value = {
                            'delivery_id': i.id,
                            'name': i.license_plate,
                            'percent': '70',
                            'estimated_quantity': i.approx_quantity,
                            'limit_quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'price_unit': self.purchase_contract_id.price_unit,
                            'supplier_id': self.purchase_contract_id.partner_id and self.purchase_contract_id.partner_id.id or False,
                            'amount': ((70.00 / 100) * i.approx_quantity) * self.purchase_contract_id.price_unit,
                            'request_id_npe': self.id
                        }
                        self.env['request.payment.line'].create(value)
                    if self.type == 'ptbf':
                        if not self.ptbt_fix_price:
                            value = {
                                'delivery_id': i.id,
                                'name': i.license_plate,
                                'percent': '70',
                                'estimated_quantity': i.approx_quantity,
                                'limit_quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                    sum(j.quantity_payment for j in request_payment_line)),
                                'quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                    sum(j.quantity_payment for j in request_payment_line)),
                                'request_id': self.id
                            }
                            self.env['request.payment.line'].create(value)
                        if self.ptbt_fix_price:
                            self.fix_price = self.ptbt_fix_price.price_fix
                            self.diff_price = self.purchase_contract_id.contract_line[0].diff_price
                            self.ref_price = self.fix_price + self.diff_price
                            value = {
                                'delivery_id': i.id,
                                'name': i.license_plate,
                                'percent': '70',
                                'estimated_quantity': i.approx_quantity,
                                'limit_quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                    sum(j.quantity_payment for j in request_payment_line)),
                                'quantity_payment': ((70.00 / 100) * i.approx_quantity) - (
                                    sum(j.quantity_payment for j in request_payment_line)),
                                'price_unit': self.ref_price * self.rate,
                                'amount': (self.ref_price * self.rate) * (((70.00 / 100) * i.approx_quantity) - (
                                    sum(j.quantity_payment for j in request_payment_line))),
                                'request_id': self.id
                            }
                            self.env['request.payment.line'].create(value)
        self._compute_request_amount()

    def create_90_percent_request_payment_line(self, delivery):
        if delivery:
            for i in delivery:
                request_payment_line = self.env['request.payment.line'].search([
                    ('delivery_id', '=', i.id)
                ])
                stock_picking = self.env['stock.picking'].search([
                    ('security_gate_id', '=', i.id)
                ])
                if ((90.00 / 100) * stock_picking.total_init_qty) - (
                        sum(j.quantity_payment for j in request_payment_line)) > 0:
                    if self.type == 'purchase':
                        value = {
                            'delivery_id': i.id,
                            'name': i.license_plate,
                            'grn_id': stock_picking.id,
                            'percent': '90',
                            'estimated_quantity': stock_picking.total_init_qty,
                            'limit_quantity_payment': ((90.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'quantity_payment': ((90.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'price_unit': self.purchase_contract_id.price_unit,
                            'supplier_id': self.purchase_contract_id.partner_id and self.purchase_contract_id.partner_id.id or False,
                            'amount': ((
                                                   90.00 / 100) * stock_picking.total_init_qty) * self.purchase_contract_id.price_unit,
                            'request_id': self.id
                        }
                        self.env['request.payment.line'].create(value)
                    if self.type == 'consign':
                        value = {
                            'delivery_id': i.id,
                            'name': i.license_plate,
                            'grn_id': stock_picking.id,
                            'percent': '90',
                            'estimated_quantity': stock_picking.total_init_qty,
                            'limit_quantity_payment': ((90.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'quantity_payment': ((90.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'price_unit': self.purchase_contract_id.price_unit,
                            'supplier_id': self.purchase_contract_id.partner_id and self.purchase_contract_id.partner_id.id or False,
                            'amount': ((
                                                   90.00 / 100) * stock_picking.total_init_qty) * self.purchase_contract_id.price_unit,
                            'request_id_npe': self.id
                        }
                        self.env['request.payment.line'].create(value)
        self._compute_request_amount()

    def create_100_percent_request_payment_line(self, delivery):
        if delivery:
            for i in delivery:
                request_payment_line = self.env['request.payment.line'].search([
                    ('delivery_id', '=', i.id)
                ])
                stock_picking = self.env['stock.picking'].search([
                    ('security_gate_id', '=', i.id)
                ])
                if ((100.00 / 100) * stock_picking.total_init_qty) - (
                        sum(j.quantity_payment for j in request_payment_line)) > 0:
                    if self.type == 'purchase':
                        value = {
                            'delivery_id': i.id,
                            'name': i.license_plate,
                            'grn_id': stock_picking.id,
                            'percent': '100',
                            'estimated_quantity': stock_picking.total_init_qty,
                            'limit_quantity_payment': ((100.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'quantity_payment': ((100.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'price_unit': self.purchase_contract_id.price_unit,
                            'supplier_id': self.purchase_contract_id.partner_id and self.purchase_contract_id.partner_id.id or False,
                            'amount': ((
                                                   100.00 / 100) * stock_picking.total_init_qty) * self.purchase_contract_id.price_unit,
                            'request_id': self.id
                        }
                        self.env['request.payment.line'].create(value)
                    if self.type == 'consign':
                        value = {
                            'delivery_id': i.id,
                            'name': i.license_plate,
                            'grn_id': stock_picking.id,
                            'percent': '100',
                            'estimated_quantity': stock_picking.total_init_qty,
                            'limit_quantity_payment': ((100.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'quantity_payment': ((100.00 / 100) * stock_picking.total_init_qty) - (
                                sum(j.quantity_payment for j in request_payment_line)),
                            'price_unit': self.purchase_contract_id.price_unit,
                            'supplier_id': self.purchase_contract_id.partner_id and self.purchase_contract_id.partner_id.id or False,
                            'amount': ((
                                                   100.00 / 100) * stock_picking.total_init_qty) * self.purchase_contract_id.price_unit,
                            'request_id_npe': self.id
                        }
                        self.env['request.payment.line'].create(value)
        self._compute_request_amount()

#######################################################################################
    