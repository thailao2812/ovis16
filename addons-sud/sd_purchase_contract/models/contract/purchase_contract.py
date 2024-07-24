# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime
from pytz import timezone
import time
from datetime import timedelta


class PurchaseContract(models.Model):
    _name = "purchase.contract"
    _inherit = ['mail.thread']
    _order = 'date_order desc, id desc'

    def create_interest_move_rate(self):
        purchase_contract_id = self

        if purchase_contract_id.interest_move_entries_id:
            purchase_contract_id.interest_move_entries_id.button_draft()
            purchase_contract_id.interest_move_entries_id.name = '/'
            purchase_contract_id.interest_move_entries_id.unlink()

        if purchase_contract_id.interest_move_id:
            sql = '''
                DELETE from account_move_line where move_id = %s 
            ''' % (purchase_contract_id.interest_move_id.id)
            self.env.cr.execute(sql)
            purchase_contract_id.interest_move_id.write(
                {'line_ids': purchase_contract_id.update_advance_interest_entries()})

        if not purchase_contract_id.interest_move_id:
            interest_move_id = purchase_contract_id.advance_interest_rate_entries()
            purchase_contract_id.write({'interest_move_id': interest_move_id})
            purchase_contract_id.interest_move_id.date = purchase_contract_id.date_payment_final

        if purchase_contract_id.type != 'purchase':
            purchase_contract_id.write({'state': 'done'})

        if purchase_contract_id.interest_move_entries_id:
            purchase_contract_id.interest_move_entries_id.date = purchase_contract_id.date_payment_final

        new_id = purchase_contract_id.done_interest_rate_entries()
        account_move = self.env['account.move'].browse(new_id)
        if new_id:
            purchase_contract_id.write({'interest_move_entries_id': new_id})

    def action_request_register_payment(self):
        return {
            'name': _('Register Payment'),
            'res_model': 'account.payment',
            'view_mode': 'form',
            # 'domain':self.request_payment_ids.ids,
            'context': {
                'active_model': 'purchase.contract',
                'active_ids': self.ids,
                'final_payment': True,
                'default_partner_type': 'supplier',
                # 'currency_id':
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def _prepare_account_move_line_for_general(self, cost, credit_account_id, debit_account_id, description):
        valuation_amount = cost or 0.0
        if self.company_id.currency_id.is_zero(valuation_amount):
            raise UserError(
                _("The found valuation amount for product %s is zero. Which means there is probably a configuration error. Check the costing method and the standard price") % (
                self.name,))
        partner_id = (self.partner_id and self.env['res.partner']._find_accounting_partner(self.partner_id).id) or False

        aml_obj = self.env['account.move.line'].with_context(check_move_validity=False)
        debit, credit, amount_currency, currency_id = aml_obj.with_context(date=self.date_order).compute_amount_fields(
            valuation_amount, self.currency_id, self.company_id.currency_id)

        debit_line_vals = {
            'name': description,
            'product_id': False,
            'quantity': 1,
            'product_uom_id': False,
            'ref': description,
            'partner_id': partner_id,
            'debit': debit or 0,
            'credit': 0,
            # 'second_ex_rate':self.currency_id.rate or 0.0,
            'amount_currency': amount_currency,
            'account_id': debit_account_id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False
        }
        credit_line_vals = {
            'name': description,
            'product_id': False,
            'quantity': 1,
            'product_uom_id': False,
            'ref': description,
            'partner_id': partner_id,
            'credit': debit,
            'debit': 0,
            # 'second_ex_rate':self.currency_id.rate or 0.0,
            'amount_currency': (-1) * amount_currency,
            'account_id': credit_account_id,
            'currency_id': self.currency_id != self.company_id.currency_id and self.currency_id.id or False
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

    @api.onchange('date_order')
    def onchange_date_order(self):
        deal_line = False
        if not self.date_order:
            return True
        crop_ids = self.env['ned.crop'].search(
            [('start_date', '<=', self.date_order), ('to_date', '>=', self.date_order)], limit=1)
        # sql ='''
        #     SELECT '%s'::Date +7 as deal_line
        # '''%(self.date_order)
        # self.env.cr.execute(sql)
        # for line in self.env.cr.dictfetchall():
        #     deal_line = line['deal_line']

        deal_line = self.date_order + timedelta(days=7)
        self.update({
            'crop_id': crop_ids and crop_ids.id or False,
            'deadline_date': deal_line
        })

    @api.model
    def _default_warehouse_id(self):
        company = self.env.user.company_id.id
        warehouse_ids = self.env['stock.warehouse'].search([('company_id', '=', company)], limit=1)
        return warehouse_ids

    @api.model
    def _default_currency_id(self):
        currency_ids = self.env.user.company_id.second_currency_id.id
        return currency_ids

    def button_dummy(self):
        return True

    @api.depends('picking_ids')
    def _compute_picking(self):
        for order in self:
            order.picking_count = len(order.picking_ids)

    signed_by_gm = fields.Boolean(string="Signed By Gm")
    signed_by_supplier = fields.Boolean(string="Signed By Supplier")

    picking_count = fields.Integer(compute='_compute_picking', string='Receptions', default=0)
    picking_ids = fields.One2many('stock.picking', 'purchase_contract_id', 'Picking Line', readonly=True)

    name = fields.Char(string='Contract Reference', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True, default='New')
    company_id = fields.Many2one('res.company', string='Company', required=True, change_default=True,
                                 ondelete='restrict', readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env['res.company']._company_default_get('purchase.contract'))
    company_representative = fields.Many2one("res.partner", string="Company Representative", readonly=True,
                                             states={'draft': [('readonly', False)]})

    partner_invoice_id = fields.Many2one('res.partner', string='Invoice Address', readonly=True, required=True,
                                         states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                         help="Invoice address for current Purchase order.")
    partner_shipping_id = fields.Many2one('res.partner', string='Delivery Address', readonly=True, required=True,
                                          states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
                                          help="Delivery address for current Purchase order.")

    state = fields.Selection([('draft', 'New'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
                             string='Status',
                             readonly=True, copy=False, index=True, default='draft')

    partner_id = fields.Many2one('res.partner', string='Supplier', readonly=True,
                                 states={'draft': [('readonly', False)]}, required=True,
                                 change_default=True, index=True, )

    supplier_representative = fields.Many2one('res.partner', string='Supplier Representative',
                                              readonly=True, states={'draft': [('readonly', False)]}, index=True, )

    validity_date = fields.Date(string='Validate Date', required=True, readonly=True, index=True,
                                states={'draft': [('readonly', False)]}, copy=False, default=fields.Datetime.now)
    expiration_date = fields.Date(string='Expiration Date', readonly=True, states={'draft': [('readonly', False)]})
    date_order = fields.Date(string='Date Contract', readonly=True, copy=False, states={'draft': [('readonly', False)]},
                             default=fields.Datetime.now)
    deadline_date = fields.Date(string='Deadline Date', readonly=False, copy=False)
    price_estimation_date = fields.Date(string='Price Estimation Date', readonly=True,
                                        states={'draft': [('readonly', False)]})

    currency_id = fields.Many2one("res.currency", string="Currency", readonly=True, required=True,
                                  states={'draft': [('readonly', False)]}, default=_default_currency_id)
    exchange_rate = fields.Float(string="Exchange Rate", readonly=True, required=True,
                                 states={'draft': [('readonly', False)]}, default=1.0)

    bank_id = fields.Many2one('res.bank', string='Bank', readonly=True, copy=False,
                              states={'draft': [('readonly', False)]})
    acc_number = fields.Char(string='Account Number', copy=False, readonly=True,
                             states={'draft': [('readonly', False)]})
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Term', copy=False, readonly=True,
                                      states={'draft': [('readonly', False)]})
    payment_description = fields.Text('Payment Term Description', copy=False, readonly=True,
                                      states={'draft': [('readonly', False)]})

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, readonly=False,
                                   states={'draft': [('readonly', False)]}, default=_default_warehouse_id)
    transportation_charges = fields.Selection([('none', 'None'), ('included', 'Included'), ('exclude', 'Exclude')],
                                              string='Transportation Charges', readonly=True,
                                              states={'draft': [('readonly', False)]}, copy=False, index=True,
                                              default='none')
    delivery_from = fields.Date(string='From Date', readonly=True, copy=False, states={'draft': [('readonly', False)]},
                                default=fields.Datetime.now)
    delivery_to = fields.Date(string='To Date', readonly=True, copy=False, states={'draft': [('readonly', False)]})

    contract_line = fields.One2many('purchase.contract.line', 'contract_id', string='Contract Lines', copy=True)

    type = fields.Selection([('consign', 'Consignment Agreement'),
                             ('ptbf', 'PTBF'),
                             ('OWH', 'OWH'),
                             ('purchase', 'Purchase Contract')], string="Type", required=True, default="consign")
    note = fields.Text('Terms and conditions')
    origin = fields.Char(string='Source Document', copy=False)

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', )
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all', )
    amount_total = fields.Monetary(string='Total', store=True, readonly=True, compute='_amount_all', )

    create_date = fields.Date(string='Creation Date', readonly=True, index=True, default=fields.Datetime.now)
    create_uid = fields.Many2one('res.users', 'Responsible', readonly=True, default=lambda self: self._uid)
    date_approve = fields.Date('Approval Date', readonly=True, copy=False)
    user_approve = fields.Many2one('res.users', string='User Approve', readonly=True)
    date_done = fields.Date('Date Done', readonly=True, copy=False)

    check_qty = fields.Boolean(string='Check Qty', readonly=True, states={'draft': [('readonly', False)]})
    check_price_unit = fields.Boolean(string='Check Unit Price', readonly=True, states={'draft': [('readonly', False)]})

    npe_contract_id = fields.Many2one('purchase.contract', string='NPE', readonly=True,
                                      states={'draft': [('readonly', False)]})
    nvp_ids = fields.One2many('npe.nvp.relation', 'contract_id', string='Nvp', readonly=True,
                              states={'draft': [('readonly', False)]})
    npe_ids = fields.One2many('npe.nvp.relation', 'npe_contract_id', string='Npe', readonly=True,
                              states={'draft': [('readonly', False)]})

    payment_ids = fields.One2many('account.payment', 'purchase_contract_id', string='Payment', )
    # group_id = fields.Many2one('procurement.group', string="Procurement Group")

    picking_count = fields.Integer(compute='_compute_picking', string='Receptions', default=0)
    # picking_ids = fields.One2many('stock.picking', 'purchase_contract_id' , 'Picking Line', readonly=True)

    product_id = fields.Many2one(related='contract_line.product_id', string='Product', store=True)

    @api.depends('contract_line.product_qty', 'contract_line')
    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.contract_line:
                total_qty += line.product_qty
            order.total_qty = total_qty

    total_qty = fields.Float(compute='_total_qty', digits=(16, 0), string='Total Qty', store=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            if vals.get('type', 'purchase') == 'purchase':
                if vals.get('cert_type') == 'quota' and vals.get('certificate_id'):
                    vals['name'] = self.env['ir.sequence'].next_by_code('purchase.contract.quota')
                    str_name = vals['name'].split('-')
                    certification_id = self.env['ned.certificate'].browse(vals.get('certificate_id'))
                    if certification_id:
                        str_name = str_name[0] + '-' + certification_id.name + '-' + str_name[1]
                        vals['name'] = str_name

                if vals.get('cert_type') == 'normal':
                    vals['name'] = self.env['ir.sequence'].next_by_code('purchase.contract') or 'New'

            elif vals.get('type', 'ptbf') == 'ptbf':
                vals['name'] = self.env['ir.sequence'].next_by_code('ptbf.contract') or 'New'
            else:
                vals['name'] = self.env['ir.sequence'].next_by_code('npe.contract') or 'New'

        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])

        result = super(PurchaseContract, self).create(vals)
        return result

    def unlink(self):
        for contract in self:
            if contract.state not in ('draft', 'cancel'):
                raise UserError(_('You can only delete draft or cancel contract.'))
            picking_ids = self.env['stock.picking'].search(
                [('purchase_contract_id', '=', contract.id), ('state', 'not in', ('draft', 'cancel'))])
            if picking_ids:
                raise UserError(_('You can only delete draft contract!'))
        return super(PurchaseContract, self).unlink()

    def action_view_picking(self):
        action = self.env.ref('stock.stock_picking_action_picking_type')
        result = action.read()[0]
        result['context'] = {}
        pick_ids = sum([order.picking_ids.ids for order in self], [])
        if len(pick_ids) > 1:
            result['domain'] = "[('id','in',[" + ','.join(map(str, pick_ids)) + "])]"
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            result['views'] = [(res and res.id or False, 'form')]
            result['res_id'] = pick_ids and pick_ids[0] or False
        return result

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
        }

        self.update(values)

    ## Errr Kiet
    # @api.onchange('company_id')
    # def company_id_domain(self):
    #     if not self.company_id:
    #         return {'domain': {'company_representative': []}}
    #     domain = {'company_representative': [('parent_id', '=', self.company_id.partner_id.id)]}
    #     return {'domain':domain}

    def button_draft(self):
        self.write({'state': 'draft'})

    def _get_destination_location(self):
        return self.picking_type_id.default_location_dest_id.id

    # Dim lại theo NED Contract
    # def button_approve(self):
    #     for contract in self:
    #         self._account_entry_move()
    #         if not contract.contract_line:
    #             raise UserError(_('You cannot approve a purchase contract without any purchase contract line.'))
    #
    #     self.write({'state': 'approved', 'user_approve': self.env.uid,
    #                 'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

    # Kiet dim lấy theo NED Contract
    # def button_done(self):
    #     self.write({'state': 'done', 'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

    # def button_cancel(self):
    #     picking = self.env['stock.picking']
    #
    #     if self.picking_ids:
    #         for picking in self.picking_ids:
    #             if picking.state in ('assigned', 'done'):
    #                 raise UserError(_('Unable to cancel contract %s as some receptions have already been done.\n\t You must first cancel related receptions.') % (self.name))
    #
    #     self.env.cr.execute('''
    #         DELETE FROM stock_move WHERE picking_id in (SELECT id FROM stock_picking WHERE purchase_contract_id = %(contract_id)s);
    #         DELETE FROM stock_picking WHERE purchase_contract_id = %(contract_id)s;''' % ({'contract_id': self.id}))
    #     self.write({'state': 'cancel'})

    ######################### NED CONTRACT  #####################################################################################################################

    fixation_deadline = fields.Date(string="Fixation deadline")
    interest = fields.Char(string="Interest", size=256)
    # x_premium = fields.Float(related='contract_line.premium', string='Subsidy')
    cert_type = fields.Selection([('normal', 'Normal'), ('quota', 'Quota')], string='Certificate type',
                                 default='normal')
    no_copute = fields.Boolean(string='No Compute Stock', default=False)

    license_id = fields.Many2one('ned.certificate.license', string='License', copy=False)

    npe_nvp_invoice_ids = fields.One2many('npe.nvp.invoice', 'contract_id', string='Allocation')
    allocation_ids = fields.One2many('stock.allocation', 'contract_id', string='Allocation')
    crop_id = fields.Many2one('ned.crop', string='Crop', required=True, readonly=True,
                              states={'draft': [('readonly', False)]})
    from_date_rate = fields.Date('From Rate')
    to_date_rate = fields.Date('To Rate')
    number = fields.Integer('Number')
    state_id = fields.Many2one('res.country.state', 'State', readonly=True, states={'draft': [('readonly', False)]})

    @api.depends('contract_line.price_total', 'contract_line.price_unit', 'pay_allocation_ids',
                 'pay_allocation_ids.allocation_amount',
                 'request_payment_ids', 'request_payment_ids.total_payment', 'payment_ids', 'payment_ids.amount',
                 'stock_allocation_ids',
                 'stock_allocation_ids.qty_allocation',
                 'pay_allocation_ids.allocation_line_ids',
                 'ptbf_ids',
                 'ptbf_ids.history_rate_ids.total_amount_vn'
                 )
    def _amount_all(self):
        for contract in self:
            price_unit = 0.0
            amount_untaxed = 0
            amount_tax = 0.0

            amount = 0.0
            amount_deposit = 0.0
            sub_rel = 0.0

            if contract.type == 'ptbf':
                amount_untaxed = 0
                for i in contract.ptbf_ids:
                    for j in i.history_rate_ids:
                        amount_untaxed += j.total_amount_vn
                        amount_tax = 0

            else:
                for line in contract.contract_line:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
                    price_unit = line.price_unit

            if not contract.nvp_ids:
                for stock in contract.stock_allocation_ids:
                    sub_rel += stock.qty_allocation
            else:
                for alls in contract.contract_line:
                    sub_rel += alls.product_qty
            if contract.type != 'ptbf':
                sub_rel = sub_rel * price_unit
            else:
                sub_rel = amount_untaxed

            for deposit in contract.pay_allocation_ids:
                amount_deposit += deposit.allocation_amount or 0.0
                for interest in deposit.allocation_line_ids:
                    amount += interest.actual_interest_pay

            for deposit in contract.payment_ids:
                amount_deposit += deposit.amount

            amount = abs(amount) * (-1)
            amount_deposit = abs(amount_deposit) * (-1)

            contract.update({
                'amount_untaxed': contract.currency_id.round(amount_untaxed),
                'amount_tax': contract.currency_id.round(amount_tax),
                'amount_sub_total': amount_untaxed + amount_tax,
                'amount_total': sub_rel + amount + amount_deposit,
                'amount_sub_rel_total': sub_rel,
                'total_interest_pay': abs(amount),
                'amount_deposit': abs(amount_deposit)
            })

    total_interest_pay = fields.Monetary(compute='_amount_all', string='Interest', readonly=True, store=True, )

    amount_untaxed = fields.Monetary(string='Untaxed Amount', store=True, readonly=True, compute='_amount_all', )
    amount_tax = fields.Monetary(string='Taxes', store=True, readonly=True, compute='_amount_all', )
    amount_total = fields.Monetary(string='Total Payable', store=True, readonly=True, compute='_amount_all', )
    amount_sub_total = fields.Monetary(string='Sub total', store=True, readonly=True, compute='_amount_all', )
    amount_sub_rel_total = fields.Monetary(string='Sub Rel total', store=True, readonly=True, compute='_amount_all', )
    amount_deposit = fields.Monetary(string='Paid', store=True, readonly=True, compute='_amount_all', )
    # Qty Allocation StockPicking

    songay = fields.Integer(string="Số ngày")

    pay_allocation_ids = fields.One2many('payment.allocation', 'contract_id', string='Payment Allocation')
    delivery_place_id = fields.Many2one('delivery.place', string='Delivery Place',
                                        readonly=True, states={'draft': [('readonly', False)]}, required=False,
                                        domain="[('type', 'in', ['purchase'])]")
    move_ids = fields.Many2many('account.move', 'move_contract_ref', 'move_id', 'contract_id', string='Move Entries',
                                readonly=True)
    relation_price_unit = fields.Float(related='contract_line.price_unit', string='Price', store=True)
    total_invoice = fields.Float(string='Total Invoice')

    relation_premium = fields.Float(related='contract_line.premium', string='Subsidy (USD/Mt)', store=True)

    invoice_ids = fields.One2many('account.move', 'contract_id', string='Invoice')
    price_unit = fields.Float(related='contract_line.price_unit', string='Price unit')
    interest_move_id = fields.Many2one('account.move', string="Interest Entries")
    interest_move_entries_id = fields.Many2one('account.move', string="Interest Entries 2")
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', )
    premium = fields.Integer(string='Premium Certificate')
    g2diff = fields.Integer(string='G2Diff')
    packing_terms_id = fields.Many2one('packing.terms', string="Packing terms")
    contract_type = fields.Selection(string='Contract type', selection=[('PTBF', 'PTBF'), ('OR', 'Outright')])

    @api.depends('contract_line.product_qty', 'state', 'nvp_ids', 'npe_ids',
                 'ptbf_ids', 'npe_ids.product_qty', 'nvp_ids.product_qty', 'stock_allocation_ids',
                 'stock_allocation_ids.state', 'stock_allocation_ids.qty_allocation',
                 'stock_allocation_ids.contract_id', 'stock_allocation_ids.picking_id')
    def _received_qty(self):
        for contract in self:
            # Ký gửi đem wa
            if contract.nvp_ids:
                received = 0

                for line in contract.nvp_ids:
                    received += line.product_qty
                if contract.state == 'done':
                    contract.qty_unreceived = 0
                else:
                    contract.qty_unreceived = contract.total_qty - received
                contract.qty_received = received
            else:
                received = 0
                for line in contract.stock_allocation_ids:
                    if line.state == 'approved':
                        received += line.qty_allocation or 0.0
                if contract.state == 'done':
                    contract.qty_unreceived = 0
                else:
                    contract.qty_unreceived = contract.total_qty - received
                contract.qty_received = received

            fix = 0.0
            if contract.type == 'ptbf':
                for line in contract.ptbf_ids:
                    fix += line.quantity or 0
            else:
                for line in contract.npe_ids:
                    fix += line.product_qty
            # SON: tính cho TH PTBF
            if contract.type == 'ptbf':
                if contract.total_qty - contract.qty_received > 2000 or contract.total_qty - contract.qty_received < -2000:
                    contract.qty_unfixed = contract.total_qty - fix
                else:
                    contract.qty_unfixed = contract.qty_received - fix
            else:
                contract.qty_unfixed = received - fix
            contract.total_qty_fixed = fix

    qty_received = fields.Float(string='Received', digits=(12, 0))
    qty_unreceived = fields.Float(compute='_received_qty', string='UnReceived', digits=(12, 0), store=True)

    @api.depends('total_qty', 'stock_allocation_ids.qty_allocation', 'stock_allocation_ids')
    def _compute_pending_allocation_qty(self):
        total_allocation = 0.0
        for this in self:
            total_allocation = sum(this.stock_allocation_ids.mapped('qty_allocation'))
            this.pending_allocation_qty = this.total_qty - total_allocation

    pending_allocation_qty = fields.Float(string='Pending Allocation', compute='_compute_pending_allocation_qty',
                                          digits=(12, 0), store=True)

    print_count = fields.Integer(string="Print Contract Count", readonly="1", default=0)

    compute = fields.Boolean(string="Compute", default=False)

    def compute_amount(self):
        if self.compute == True:
            return
        self._compute_amount()
        self.compute = True

    @api.depends('payment_ids', 'payment_ids.amount', 'payment_ids.state', 'pay_allocation_ids',
                 'pay_allocation_ids.allocation_amount')
    def _compute_amount(self):
        for contract in self:
            contract.total_advance = 0.0
            contract.total_payment_remain = 0.0
            contract.total_payment_received = 0.0

            payment_remain = payment_received = amount = 0.0
            if contract.type == 'consign':
                for pay in contract.payment_ids:
                    amount += pay.amount or 0.0
                    payment_received += pay.payment_refunded or 0.0
                    payment_remain += pay.open_advance or 0.0

                    contract.total_advance = amount or 0.0
                    contract.total_payment_remain = payment_remain or 0.0
                    contract.total_payment_received = payment_received or 0.0

            if contract.type != 'consign':
                for rate_pay in contract.pay_allocation_ids.filtered(lambda r: r.allocation_amount != 0):
                    rate_pay._compute_payment_received()
                    rate_pay.pay_id._compute_payment_received()
                    rate_pay.relation_contract_id._compute_amount()

    total_advance = fields.Float(compute='_compute_amount', string='Total Advance', digits=(12, 0), store=True)
    total_payment_received = fields.Float(compute='_compute_amount', string='Refunded', digits=(12, 0), store=True)
    total_payment_remain = fields.Float(compute='_compute_amount', string='Open Advance', digits=(12, 0), store=True)

    @api.depends('state', 'qty_received', 'nvp_ids', 'npe_ids', 'contract_line.product_qty', 'ptbf_ids', 'total_qty',
                 'ptbf_ids.quantity', 'ptbf_ids.quantity_fixed', 'type')
    def _total_qty_fixed(self):
        for order in self:
            fix = 0.0
            if order.type != 'ptbf':
                for line in order.npe_ids:
                    fix += line.product_qty

                order.qty_unfixed = order.qty_received - fix
                order.total_qty_fixed = fix
            else:
                for line in order.ptbf_ids:
                    fix += line.quantity
                order.qty_unfixed = order.total_qty - fix
                order.total_qty_fixed = fix

    total_qty_fixed = fields.Float(compute='_total_qty_fixed', string='Fixed', digits=(12, 0), store=True)
    qty_unfixed = fields.Float(compute='_total_qty_fixed', string='UnFixed', digits=(12, 0), store=True)

    @api.depends('request_payment_ids', 'request_payment_ids.request_amount')
    def _compute_advance_amount(self):
        for line in self:
            amount = 0.0
            for i in line.request_payment_ids:
                if i.type_payment == 'advance_payment':
                    amount += i.request_amount or 0.0
            line.advance_amount = amount

    advance_amount = fields.Float(string="Advance payment", compute='_compute_advance_amount', store=True)
    request_payment_ids = fields.One2many('request.payment', 'purchase_contract_id', string='Request Payment')

    def button_cancel(self):
        picking = self.env['stock.picking']

        if self.picking_ids:
            for picking in self.picking_ids:
                if picking.state in ('assigned', 'done'):
                    raise UserError(
                        _('Unable to cancel contract %s as some receptions have already been done.\n\t You must first cancel related receptions.') % (
                            self.name))

        self.env.cr.execute('''
            DELETE FROM stock_move WHERE picking_id in (SELECT id FROM stock_picking WHERE purchase_contract_id = %(contract_id)s);
            DELETE FROM stock_picking WHERE purchase_contract_id = %(contract_id)s;''' % ({'contract_id': self.id}))
        self.write({'state': 'cancel'})

    def printf_npe(self):
        self.print_count += 1
        return self.env.ref(
            'sd_purchase_contract.npe_report').report_action(self)

    # def do_print_picking(self):
    #     return self.env.ref(
    #         'reach_stock_base.template_picking_order').report_action(self)

    def printf_nvp(self):
        self.print_count += 1
        if self.nvp_ids:
            return self.env.ref(
                'sd_purchase_contract.npe_nvp_report').report_action(self)
        else:
            return self.env.ref(
                'sd_purchase_contract.nvp_report').report_action(self)

    def printf_liquidation(self):
        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'nvp_liquidation_report',
        }

    def advance_interest_rate_entries(self):
        for contract in self:
            move_obj = self.env['account.move']
            credit_account_id = contract.company_id.incomce_from_advance_payment_id.id
            if not contract.company_id.interest_income_shipment_id.id:
                raise UserError(
                    _('You cannot Validate, You must define Account Interest Income Shipment in Company Configuration '))
            debit_account_id = contract.company_id.interest_income_shipment_id.id
            journal_id = False
            interest_pay = 0.0
            for pay_allocation in contract.pay_allocation_ids:
                interest_pay += pay_allocation.total_interest_pay or 0.0
            journal_id = journal_id = self.env['account.journal'].search([('code', '=', 'BILL')], limit=1)
            if not interest_pay:
                return False

            name = '''Bút toán lãi suất (Theo ngày hợp đồng): %s''' % (self.name)
            move_lines = contract._prepare_account_move_line_for_general(interest_pay, credit_account_id,
                                                                         debit_account_id, name)
            date = contract.date_order

            if not journal_id:
                raise
            new_move_id = move_obj.create({'journal_id': journal_id.id,
                                           'account_analytic_id': contract.warehouse_id and contract.warehouse_id.account_analytic_id.id,
                                           'line_ids': move_lines,
                                           'partner_id':contract.partner_id and contract.partner_id.id or False,
                                           'date': time.strftime(DATE_FORMAT),
                                           'ref': name,
                                           'narration': name})
            new_move_id.action_post()
        return new_move_id.id

    def _create_stock_moves(self, line, picking, picking_type, qty):
        moves = self.env['stock.move.line']
        #         price_unit = line.price_unit * picking.total_qty / picking.total_init_qty
        price_unit = line.price_unit
        # if line.tax_id:
        #     price_unit = line.tax_id.compute_all(price_unit, currency=line.contract_id.currency_id, quantity=1.0)['total_excluded']
        # if line.product_uom.id != line.product_id.uom_id.id:
        #     price_unit = price_unit * (line.product_uom.factor / line.product_id.uom_id.factor)

        # Quy doi ra USD
        price_unit = self.env.user.company_id.second_currency_id.with_context(date=line.contract_id.date_order).compute(
            price_unit,
            self.env.user.company_id.currency_id)
        vals = {
            'warehouse_id': picking_type.warehouse_id.id,
            'picking_id': picking.id,
            # 'name': line.name or '',
            'product_id': line.product_id.id,
            'product_uom_id': line.product_uom.id,
            'init_qty': qty,
            'qty_done': qty or 0.0,
            'price_unit': price_unit,
            # 'tax_id': [(6, 0, [x.id for x in i.tax_id])],
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'date': line.contract_id.date_order,
            # 'exchange_rate':this.purchase_contract_id.exchange_rate or 1,
            'currency_id': line.contract_id.currency_id.id or False,
            # 'type': picking_type.code,
            'state': 'draft',
            # 'scrapped': False,
            'price_currency': line.price_unit or 0.0,
        }

        move_id = moves.create(vals)
        return move_id

    def _prepare_account_move_faq_line(self, line, qty, amount_usd, amount_vn, debit_account_id, credit_account_id):
        debit = credit = amount_usd
        partner_id = line.picking_id.partner_id.id
        com = line.picking_id.company_id
        # name =''
        #         if line.picking_id:
        #             name = line.picking_id.origin + ' - ' +line.product_id.default_code
        #         else:
        name = line.product_id.default_code
        debit_line_vals = {
            'name': name,
            'product_id': line.product_id.id,
            'quantity': qty,
            'product_uom_id': line.product_id.uom_id.id,
            'partner_id': partner_id,
            'debit': debit or 0.0,
            'credit': 0.0,
            # 'second_ex_rate':second_ex_rate or 0.0,
            'amount_currency': amount_vn,
            'account_id': debit_account_id,
            'currency_id': com.second_currency_id.id
        }
        credit_line_vals = {
            'name': name,
            'product_id': line.product_id.id,
            'quantity': qty,
            'product_uom_id': line.product_id.uom_id.id,
            'partner_id': partner_id,
            'debit': 0.0,
            'credit': credit or 0.0,
            # 'second_ex_rate':second_ex_rate or 0.0,
            'amount_currency': (-1) * amount_vn,
            'account_id': credit_account_id,
            'currency_id': com.second_currency_id.id
        }
        return [(0, 0, debit_line_vals), (0, 0, credit_line_vals)]

    def _get_accounting_faq_data(self, line):
        product_obj = self.env['product.template']
        accounts = product_obj.browse(line.product_id.product_tmpl_id.id).get_product_accounts()

        acc_src = accounts['stock_input'].id
        acc_dest = accounts.get('stock_valuation', False)

        journal_id = accounts['stock_journal'].id
        return journal_id, acc_dest.id, acc_src

    def get_entries_picking_nvp(self, pick):
        move_obj = self.env['account.move']
        move_lines = []

        for move_line_ids in pick.move_line_ids_without_package:
            amount_vn = amount_usd = 0.0
            for move in move_line_ids:
                amount_vn = move.qty_done * move.price_currency
                amount_usd = move.qty_done * move.price_unit

            if amount_vn and amount_vn != 0:
                journal_id, acc_src, acc_dest = self._get_accounting_faq_data(move_line_ids)
                move_lines = self._prepare_account_move_faq_line(move_line_ids, move_line_ids.qty_done, amount_usd,
                                                                 amount_vn, acc_src, acc_dest)
                if move_lines:
                    if move_line_ids.entries_id:
                        return False
                    ref = move_line_ids.picking_id.name
                    date = move_line_ids.date
                    new_move_id = move_obj.create({'journal_id': journal_id,
                                                   'account_analytic_id': pick.warehouse_id and pick.warehouse_id.account_analytic_id.id,
                                                   'line_ids': move_lines,
                                                   'date': date,
                                                   'ref': ref,
                                                   'warehouse_id': pick.warehouse_id and pick.warehouse_id.id or False,
                                                   'narration': False})
                    new_move_id.action_post()
                    move_line_ids.entries_id = new_move_id.id
                    return True
            else:
                return False

    def button_approve(self):
        for contract in self:
            if not contract.contract_line:
                raise UserError(_('You cannot approve a purchase contract without any purchase contract line.'))

            #  phat sinh phiếu nhâp kho từ Ký gởi -> NVL
            if contract.nvp_ids and contract.type == 'purchase':
                for line in contract.contract_line:
                    if not line.price_unit or line.price_unit == 0.0:
                        raise UserError(_('You cannot Approve, Price Unit !=0 '))

                picking_type = contract.warehouse_id.int_type_id
                if not contract.warehouse_id.int_type_id:
                    raise UserError(_('You cannot Approve, You must define Picking type'))

                var = {
                    'warehouse_id': picking_type.warehouse_id.id,
                    'picking_type_id': picking_type.id,
                    'partner_id': contract.partner_id.id,
                    'date': contract.date_order,
                    'date_done': contract.date_order,
                    'origin': contract.name,
                    'location_dest_id': picking_type.default_location_dest_id.id,
                    'location_id': picking_type.default_location_src_id.id,
                    'purchase_contract_id': contract.id
                }
                if not contract.cert_type or contract.cert_type != 'quota':
                    picking = self.env['stock.picking'].create(var)
                    product_qty = 0
                    product_qty = contract.qty_received
                    #                 for i in contract.nvp_ids:
                    #                     product_qty += i.qty_received

                    for line in contract.contract_line:
                        moves = line._create_stock_moves(line, picking, picking_type, product_qty)

                    picking.button_sd_validate()
                    # Kiet: cho sinh bút toán luôn
                    # self.get_entries_picking_nvp(picking)

        self.write({'state': 'approved', 'user_approve': self.env.uid,
                    'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

    def btt_load_payment(self):
        if self.pay_allocation_ids:
            # sql_del = """DELETE from payment_allocation where contract_id = %s""" % (self.id)
            # self.env.cr.execute(sql_del)
            self.pay_allocation_ids.unlink()
        npe_ids = []
        for i in self.nvp_ids:
            npe_ids.append(i.npe_contract_id.id)

        where = ''
        if npe_ids:
            where = '''and pc.id in (%s)''' % (','.join(map(str, npe_ids)))
        if not npe_ids:
            return True

        sql = '''
                SELECT ap.id 
                FROM account_payment as ap
                    join purchase_contract pc on pc.id = ap.purchase_contract_id
                WHERE ap.partner_id = %s
                    and ap.purchase_contract_id is not null
                    and ap.extend_payment = 'payment'
                    and ap.allocated != true
                    and pc.type = 'consign'
                    %s
                    and ap.id not in (
                        SELECT pay_id
                        FROM payment_allocation
                        WHERE contract_id = %s
                    )
            ''' % (self.partner_id.id, where, self.id)
        print(sql)
        self.env.cr.execute(sql)
        for contract in self.env.cr.dictfetchall():
            payment_allocation = self.env['payment.allocation'].create(
                {'pay_id': contract['id'], 'contract_id': self.id})
            payment_allocation.btt_load_interest()
        return True

    def button_lai(self):
        if self.interest_move_id:
            sql = '''
                DELETE from account_move_line where move_id = %s 
            ''' % (self.interest_move_id.id)
            self.env.cr.execute(sql)
            self.interest_move_id.write({'line_ids': self.update_advance_interest_entries()})

        if not self.interest_move_id:
            interest_move_id = self.advance_interest_rate_entries()
            self.write({'interest_move_id': interest_move_id})

    def update_advance_interest_entries(self):
        for contract in self:
            credit_account_id = contract.company_id.incomce_from_advance_payment_id.id
            if not contract.company_id.interest_income_shipment_id.id:
                raise UserError(
                    _('You cannot Validate, You must define Account Interest Income Shipment in Company Configuration '))
            debit_account_id = contract.company_id.interest_income_shipment_id.id
            interest_pay = 0.0
            for pay_allocation in contract.pay_allocation_ids:
                interest_pay += pay_allocation.total_interest_pay or 0.0
            if not interest_pay:
                return False

            name = u'''lãi ứng tiền cà phê gửi kho: %s''' % (self.name)
            move_lines = contract._prepare_account_move_line_for_general(interest_pay, credit_account_id,
                                                                         debit_account_id, name)

        return move_lines

    def done_interest_rate_entries(self):
        for contract in self:
            move_obj = self.env['account.move']
            debit_account_id = contract.partner_id.property_account_payable_id.id
            if not contract.company_id.interest_income_shipment_id.id:
                raise UserError(
                    _('You cannot Validate, You must define Account Interest Income Shipment in Company Configuration '))
            credit_account_id = contract.company_id.interest_income_shipment_id.id
            journal_id = False
            interest_pay = 0.0
            for pay_allocation in contract.pay_allocation_ids:
                interest_pay += pay_allocation.total_interest_pay or 0.0
            journal_id = self.env['account.journal'].search([('code', '=', 'BILL')], limit=1)

            if not interest_pay:
                return False

            name = u'''lãi ứng tiền cà phê gửi kho: %s''' % (self.name)
            move_lines = contract._prepare_account_move_line_for_general(interest_pay, credit_account_id,
                                                                         debit_account_id, name)

            if not journal_id:
                raise
            new_move_id = move_obj.create({'journal_id': journal_id.id,
                                           'account_analytic_id': contract.warehouse_id and contract.warehouse_id.account_analytic_id.id,
                                           'line_ids': move_lines,
                                           'partner_id':contract.partner_id and contract.partner_id.id or False,
                                           'date': contract.deadline_date or time.strftime(DATE_FORMAT),
                                           'ref': name,
                                           'narration': name})
            new_move_id.action_post()
        return new_move_id.id

    def button_ketchuyen_lai(self):
        return
        for contract in self:
            if contract.interest_move_id:
                dt = contract.interest_move_id.date
                # period = self.env['account.period'].find(dt)
                if contract.type != 'purchase':
                    contract.write({'state': 'done'})
                    continue

                # if period.state !='done':
                sql = '''
                    DELETE from account_move_line where move_id = %s 
                ''' % (contract.interest_move_id.id)
                contract.env.cr.execute(sql)
                contract.interest_move_id.write({'line_ids': contract.update_advance_interest_entries()})
            if not contract.interest_move_id:
                interest_move_id = contract.advance_interest_rate_entries()
                contract.write({'interest_move_id': interest_move_id})

            if contract.interest_move_entries_id:
                return 1
            new_id = contract.done_interest_rate_entries()
            if new_id:
                contract.write({'interest_move_entries_id': new_id})
        return 1

    def button_done(self):
        # kiet bút toán 
        for contract in self:
            if contract.type == 'ptbf':
                contract.write({'state': 'done'})
                return 1
            if contract.amount_total != 0:
                raise UserError(_('Payable must be 0!'))
            if contract.type != 'purchase':
                contract.write({'state': 'done'})
                continue

            # if self.interest_move_id:
            #     sql = '''
            #         DELETE from account_move_line where move_id = %s 
            #     '''%(self.interest_move_id.id)
            #     self.env.cr.execute(sql)
            #     self.interest_move_id.write({'line_ids': self.update_advance_interest_entries()})
            #
            # if not self.interest_move_id:
            #     interest_move_id = self.advance_interest_rate_entries()
            #     self.write({'interest_move_id': interest_move_id})

            contract.write({'state': 'done'})
        return 1

    ######################### NED CONTRACT ACCOunt VN #####################################################################################################################

    stock_allocation_ids = fields.One2many('stock.allocation', 'contract_id', 'Allocation')
    invoice_allocation_ids = fields.One2many('invoiced.allocation', 'contract_id', string='Invoice Allocation')

    ######################### END NED CONTRACT Account VN #####################################################################################################################

    ######################### NED CONTRACT VN #####################################################################################################################

    trader_id = fields.Many2one('res.users', string='Trader')
    lifffe_line = fields.Float(string='LIFFE', related='contract_line.hedged_fixed_level', store=True)
    lifffe_line_ptbf = fields.Float(string='LIFFE PTBF', compute='_compute_lifffe_ptbf', store=True)
    difams = fields.Float(string='DIFF AMS', related='contract_line.difams', store=True)
    ex = fields.Float(string='FX', related='contract_line.ex', store=True)
    diff_price = fields.Float(string='Diff Supplier', related='contract_line.diff_price', store=True)
    is_temp_quota = fields.Boolean(string='Is Temp Quota')
    date_payment_final = fields.Date(string='Final Payment Date')

    is_according = fields.Boolean(string='Is According')
    according_id = fields.Many2one('purchase.contract.according', string='According Letter of attorney')

    @api.depends('ptbf_ids', 'ptbf_ids.quantity', 'ptbf_ids.price_fix', 'state')
    def _compute_lifffe_ptbf(self):
        for record in self:
            if len(record.ptbf_ids) == 1:
                record.lifffe_line_ptbf = sum(i.price_fix for i in record.ptbf_ids)
            elif len(record.ptbf_ids) > 1:
                record.lifffe_line_ptbf = sum(i.price_fix * i.quantity for i in record.ptbf_ids) / sum(
                    i.quantity for i in record.ptbf_ids)
            else:
                record.lifffe_line_ptbf = 0
######################### END NED CONTRACT  VN #####################################################################################################################
