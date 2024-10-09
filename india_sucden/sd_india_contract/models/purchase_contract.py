# -*- coding: utf-8 -*-
import math

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
import time
from datetime import datetime,date, timedelta


class PurchaseContractLine(models.Model):
    _inherit = "purchase.contract.line"

    bag_no = fields.Float(string='Bag Nos.')


class PurchaseContract(models.Model):
    _inherit = 'purchase.contract'

    state = fields.Selection([('draft', 'New'),
                              ('commercial', 'Commercial'),
                              ('accounting', 'Accounting'),
                              ('director', 'Director'),
                              ('approved', 'Approved'),
                              ('done', 'Close'),
                              ('cancel', 'Cancelled')],
                             string='Status',
                             readonly=True, copy=False, index=True, default='draft', tracking=True)

    reject_by_commercial = fields.Text(string='Commercial Reject Reason')
    reject_by_accounting = fields.Text(string='Accounting Reject Reason')
    reject_by_director = fields.Text(string='Director Reject Reason')
    agent_id = fields.Many2one('res.partner', string='Agent')

    qty_received_net = fields.Float(compute='_received_qty_net', string='Received Gross Qty', digits=(12, 0), store=True)
    qty_unreceived_net = fields.Float(compute='_received_qty_net', string='UnReceived Gross Qty', digits=(12, 0), store=True)

    total_deduction_amount = fields.Float(string='Total Deduction Amount', compute='_compute_total_deduction_amount', store=True)
    total_deduction_quantity = fields.Float(string='Total Quantity Adjustment', compute='_compute_total_deduction_amount', store=True)

    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=False, readonly=True
                                   , default=False, compute='_compute_warehouse_id', store=True)
    premium = fields.Float(tracking=True)

    number_of_bags = fields.Float(string='Number of bags', related='contract_line.bag_no', store=True)
    estate_name = fields.Char(string='Estate Name', related='partner_id.estate_name', store=True)

    delivery_place_id = fields.Many2one('delivery.place', string='Delivery Place',
                                        readonly=False, required=True,
                                        domain="[('type', 'in', ['purchase'])]")
    packing_id = fields.Many2one('ned.packing', related='contract_line.packing_id', store=True)

    tds = fields.Float(string='TDS', compute='compute_tds', store=True)
    fixed_gross_qty = fields.Float(string='Fixed Gross Qty', compute='compute_data_fix', store=True)
    unfixed_gross_qty = fields.Float(string='Unfixed Gross Qty', compute='compute_data_fix', store=True)
    gross_price = fields.Float(string='Gross Price', compute='compute_gross_price', store=True)
    remark_note_done = fields.Text(string='Remark')
    unreceive_gross_value = fields.Float(string='Unreceive Gross Value', compute='compute_gross_price', store=True)

    remark = fields.Text(string='Remark')

    gross_qty = fields.Float(string='Gross Quantity', digits=(12,0))
    quality_deduction = fields.Float(string='Quality Deduction', digits=(12,0), compute='compute_quality_deduction', store=True)

    @api.depends('gross_qty', 'total_qty')
    def compute_quality_deduction(self):
        for rec in self:
            rec.quality_deduction = rec.gross_qty - rec.total_qty

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

        deal_line = self.date_order + timedelta(days=15)
        self.update({
            'crop_id': crop_ids and crop_ids.id or False,
            'deadline_date': deal_line
        })

    def button_done(self):
        # kiet bút toán
        for contract in self:
            # if contract.type == 'ptbf':
            #     contract.write({'state': 'done'})
            #     return 1
            # if contract.amount_total != 0:
            #     raise UserError(_('Payable must be 0!'))
            # if contract.type != 'purchase':
            #     contract.write({'state': 'done'})
            #     continue
            #
            # # if self.interest_move_id:
            # #     sql = '''
            # #         DELETE from account_move_line where move_id = %s
            # #     '''%(self.interest_move_id.id)
            # #     self.env.cr.execute(sql)
            # #     self.interest_move_id.write({'line_ids': self.update_advance_interest_entries()})
            # #
            # # if not self.interest_move_id:
            # #     interest_move_id = self.advance_interest_rate_entries()
            # #     self.write({'interest_move_id': interest_move_id})
            if not contract.remark_note_done:
                raise UserError(_("You have to input Remark for setting this Contract Close/Done"))
            contract.write({'state': 'done'})
        return 1

    @api.depends('premium', 'relation_price_unit', 'qty_unreceived_net')
    def compute_gross_price(self):
        for rec in self:
            rec.gross_price = rec.relation_price_unit + rec.premium
            rec.unreceive_gross_value = rec.gross_price * rec.qty_unreceived_net

    @api.depends('qty_received_net', 'qty_received', 'total_qty_fixed')
    def compute_data_fix(self):
        for rec in self:
            fixed_gross_qty = 0
            if rec.total_qty_fixed > 0:
                fixed_gross_qty = rec.qty_received_net - rec.qty_received + rec.total_qty_fixed
            rec.fixed_gross_qty = fixed_gross_qty
            rec.unfixed_gross_qty = rec.qty_received_net - fixed_gross_qty

    @api.depends('request_payment_ids', 'request_payment_ids.request_amount', 'partner_id')
    def compute_tds(self):
        for rec in self:
            rec.tds = 0
            if rec.request_payment_ids:
                financial_year = self.env['financial.year'].search([
                    ('state', '=', 'confirm')
                ], limit=1)
                if financial_year:
                    if sum(rec.request_payment_ids.mapped('request_amount')) >= financial_year.max_value:
                        if rec.partner_id.pan_number:
                            rec.tds = financial_year.max_value * (financial_year.percent_for_pan/100)
                        else:
                            rec.tds = financial_year.max_value * (financial_year.percent_unpan/100)

    @api.depends('stock_allocation_ids', 'stock_allocation_ids.picking_id')
    def _compute_warehouse_id(self):
        for record in self:
            if record.stock_allocation_ids:
                record.warehouse_id = record.stock_allocation_ids[0].picking_id.warehouse_id.id
            else:
                record.warehouse_id = False

    @api.depends('request_payment_ids', 'request_payment_ids.deduction_value', 'request_payment_ids.deduction_quantity')
    def _compute_total_deduction_amount(self):
        for record in self:
            if record.request_payment_ids:
                record.total_deduction_amount = sum(i.deduction_value for i in record.request_payment_ids)
                record.total_deduction_quantity = sum(i.deduction_quantity for i in record.request_payment_ids)
            else:
                record.total_deduction_amount = 0
                record.total_deduction_quantity = 0

    @api.depends('contract_line.product_qty', 'state', 'stock_allocation_ids', 'total_qty',
                 'stock_allocation_ids.state', 'stock_allocation_ids.qty_allocation',
                 'stock_allocation_ids.contract_id', 'stock_allocation_ids.picking_id', 'nvp_ids', 'npe_ids')
    def _received_qty_net(self):
        for contract in self:
            contract.qty_received_net = contract.qty_unreceived_net = 0
            received = 0
            if contract.nvp_ids:
                received = 0
                for line in contract.nvp_ids:
                    received += line.product_qty
            else:
                for line in contract.stock_allocation_ids:
                    if line.state == 'approved':
                        received += line.qty_allocation_net
            contract.qty_received_net = received
            contract.qty_unreceived_net = contract.total_qty - received
            if contract.state == 'done':
                contract.qty_unreceived_net = 0

    @api.constrains('amount_deposit', 'amount_sub_rel_total', 'type')
    def _constrains_payment(self):
        for obj in self:
            if obj.type == 'purchase':
                if obj.amount_deposit > obj.amount_sub_rel_total:
                    raise UserError(_("You can not pay more than %s for this contract!") % obj.amount_sub_rel_total)


    @api.model
    def default_get(self, fields):
        res = super().default_get(fields)
        res['currency_id'] = self.env.user.company_id.currency_id.id
        return res


    @api.depends('contract_line.product_qty', 'state', 'nvp_ids', 'npe_ids',
                 'ptbf_ids', 'npe_ids.product_qty', 'nvp_ids.product_qty', 'stock_allocation_ids',
                 'stock_allocation_ids.state', 'stock_allocation_ids.qty_allocation',
                 'stock_allocation_ids.contract_id', 'stock_allocation_ids.picking_id')
    def _received_qty(self):
        condition = self.env['condition.contract'].search([
            ('active', '=', True)
        ])
        qty_allow = 0
        for contract in self:
            if condition:
                qty_allow = contract.total_qty * condition.name / 100
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
            if contract.qty_received > qty_allow + contract.total_qty:
                raise UserError(_("Quantity Receive can't higher than condition"))

    def approve_commercial(self):
        partner = self.partner_id
        license_checking = self.env['ned.certificate.license'].search([
            ('partner_id', '=', partner.id),
            ('state', '=', 'active')
        ])
        if license_checking and not self.certificate_id:
            raise UserError(_("You have to input Certificate and License before submit"))
        if sum(self.contract_line.mapped('bag_no')) <= 0:
            raise UserError(_("You have to input Bag No, please check again"))
        self.state = 'commercial'

    def approve_account(self):
        self.state = 'accounting'

    def approve_director(self):
        self.state = 'director'

    def button_reject(self):
        print(123)

    def button_cancel(self):
        res = super().button_cancel()
        for record in self:
            if record.qty_received > 0 and any(record.stock_allocation_ids.filtered(lambda x: x.state == 'approved')):
                raise UserError(_("You cannot cancel the contract when it have allocated with GRN!"))
            if (record.npe_ids or record.nvp_ids) and record.type == 'consign':
                raise UserError(_("You cannot cancel the contract when it have transaction with other contract!"))
            request_payment = self.env['request.payment'].search([
                ('purchase_contract_id', '=', record.id)
            ])
            if request_payment:
                raise UserError(_("You cannot cancel the contract when it have transaction with other payment!"))
        return res

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    @api.depends('contract_line.price_total', 'contract_line.price_unit', 'pay_allocation_ids',
                 'pay_allocation_ids.allocation_amount',
                 'request_payment_ids', 'request_payment_ids.total_payment', 'payment_ids', 'payment_ids.amount',
                 'stock_allocation_ids', 'payment_ids.state',
                 'stock_allocation_ids.qty_allocation',
                 'pay_allocation_ids.allocation_line_ids',
                 'ptbf_ids', 'premium', 'total_qty',
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
                sub_rel = sub_rel * price_unit + (contract.premium * sub_rel)
                sub_rel = self.custom_round(sub_rel)
            else:
                sub_rel = amount_untaxed

            for deposit in contract.pay_allocation_ids:
                amount_deposit += deposit.allocation_amount or 0.0
                for interest in deposit.allocation_line_ids:
                    amount += interest.actual_interest_pay

            for deposit in contract.payment_ids.filtered(lambda x: x.state == 'posted'):
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

    def print_cr(self):
        return self.env.ref('sd_india_contract.contract_regular_india_report').report_action(self)

    def print_cs(self):
        return self.env.ref('sd_india_contract.contract_consignment_india_report').report_action(self)

    def print_cs_detail(self):
        if self.npe_ids:
            return self.env.ref('sd_india_contract.contract_consignment_detail_india_report').report_action(self)
        return True

    def print_cr_detail(self):
        if self.nvp_ids:
            return self.env.ref('sd_india_contract.contract_regular_detail_india_report').report_action(self)
        return True

    def button_approve(self):
        for contract in self:
            if not contract.contract_line:
                raise UserError(_('You cannot approve a purchase contract without any purchase contract line.'))

            #  phat sinh phiếu nhâp kho từ Ký gởi -> NVL
            # if contract.nvp_ids and contract.type == 'purchase':
            #     for line in contract.contract_line:
            #         if not line.price_unit or line.price_unit == 0.0:
            #             raise UserError(_('You cannot Approve, Price Unit !=0 '))
            #
            #     picking_type = contract.warehouse_id.int_type_id
            #     if not contract.warehouse_id.int_type_id:
            #         raise UserError(_('You cannot Approve, You must define Picking type'))
            #
            #     var = {
            #         'warehouse_id': picking_type.warehouse_id.id,
            #         'picking_type_id': picking_type.id,
            #         'partner_id': contract.partner_id.id,
            #         'date': contract.date_order,
            #         'date_done': contract.date_order,
            #         'origin': contract.name,
            #         'location_dest_id': picking_type.default_location_dest_id.id,
            #         'location_id': picking_type.default_location_src_id.id,
            #         'purchase_contract_id': contract.id
            #     }
            #     if not contract.cert_type or contract.cert_type != 'quota':
            #         picking = self.env['stock.picking'].create(var)
            #         product_qty = 0
            #         product_qty = contract.qty_received
            #         #                 for i in contract.nvp_ids:
            #         #                     product_qty += i.qty_received
            #
            #         for line in contract.contract_line:
            #             moves = line._create_stock_moves(line, picking, picking_type, product_qty)
            #
            #         picking.button_sd_validate()
            #         # Kiet: cho sinh bút toán luôn
            #         # self.get_entries_picking_nvp(picking)

        self.write({'state': 'approved', 'user_approve': self.env.uid,
                    'date_approve': datetime.now().strftime(DATETIME_FORMAT)})

