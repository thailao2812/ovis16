DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import math
from datetime import datetime, date, timedelta, time
import math


class RequestPayment(models.Model):
    _inherit = 'request.payment'

    delivery_registration_ids = fields.Many2many('ned.security.gate.queue', string='Delivery Registration Factory 70%')

    delivery_70_ktn_ids = fields.One2many('delivery.ktn', 'request_payment_id', string='Delivery KTN',
                                      ondelete='cascade', )
    delivery_ktn_array = fields.Char(string='Delivery Array', compute='compute_delivery_ktn_array', store=True)

    delivery_70_ids = fields.One2many('delivery.ready', 'request_payment_id', string='Delivery 70%', ondelete='cascade',)
    delivery_array = fields.Char(string='Delivery Array', compute='compute_delivery_array', store=True)

    grn_90_ids = fields.One2many('grn.ready', 'request_payment_id', string='GRN 90%', ondelete='cascade',)
    grn_90_array = fields.Char(string='Delivery Array', compute='compute_grn_90_array', store=True)

    grn_100_factory_ids = fields.One2many('grn.done.factory', 'request_payment_id', string='GRN 100% Factory', ondelete='cascade',)
    grn_100_factory_array = fields.Char(string='Delivery Array', compute='compute_grn_100_factory_array', store=True)

    grn_100_fot_ids = fields.One2many('grn.done.fot', 'request_payment_id', string='GRN 100% FOT', ondelete='cascade',)
    grn_100_fot_array = fields.Char(string='Delivery Array', compute='compute_grn_100_fot_array', store=True)

    status_goods_ids = fields.One2many('status.goods', 'request_payment_id', compute='compute_status_goods', store=True, readonly=True, ondelete='cascade',)
    parent_id_purchase_contract = fields.Integer(string='Parent Id')
    hide_delivery = fields.Boolean(string='Hide Delivery', default=True)
    hide_delivery_ktn = fields.Boolean(string='Hide Delivery KTN', default=True)
    hide_grn_ready = fields.Boolean(string='Hide GRN Ready', default=True)
    hide_grn_done = fields.Boolean(string='Hide GRN Done', default=True)
    hide_grn_fot_done = fields.Boolean(string='Hide GRN FOT Done', default=True)

    payment_quantity = fields.Float(string='Payment Quantity', compute='compute_payment_quantity', store=True, digits=(12, 0))

    history_quantity_payment = fields.One2many('history.payment.quantity', 'request_payment_id', compute='compute_history_payment', store=True, ondelete='cascade',)
    balance = fields.Float(string='Balance Quantity', compute='compute_balance_quantity', store=True)
    current_balance = fields.Float(string='Current Balance', compute="current_balance_qty", store=True)
    is_converted = fields.Boolean(string='Convert from NPE', default=False)

    converted_line_ids = fields.One2many('converted.line', 'request_payment_id', string='Converted Data', ondelete='cascade')
    advance_payment_converted = fields.Float(string='Advance Payment', compute='compute_advance_payment_converted', store=True)
    total_interest = fields.Float(string='Interest', compute='compute_advance_payment_converted', store=True)
    request_amount = fields.Float(string='Request Amount', digits=(12, 0), compute='_compute_request_amount',
                                  store=True, readonly=False)
    mirror_request_amount = fields.Float(string='Request Amount', compute='compute_payment_quantity', store=True)
    is_dr_request = fields.Boolean(string='Is Dr Request', compute='compute_dr_request', store=True)

    state = fields.Selection(selection='_get_new_state', string='State', readonly=False, copy=False, index=True, default='draft')

    user_process_ids = fields.One2many('user.process.state', 'request_payment_id')

    reason = fields.Text(string="Reason")

    attachment_ids = fields.Many2many('ir.attachment', 'request_payment_attachment_rel', 'request_id',
                                      'attachment_id', 'Attachments')
    is_attach_file = fields.Char(string='File Attachment', compute='compute_count_file', store=True)

    have_dr_ktn = fields.Boolean(string='Have DR KTN', compute='compute_data_invisible', store=True)
    have_dr = fields.Boolean(string='Have DR', compute='compute_data_invisible', store=True)
    have_grn_90 = fields.Boolean(string='Have GRN 90', compute='compute_data_invisible', store=True)
    have_grn_100 = fields.Boolean(string='Have GRN 100', compute='compute_data_invisible', store=True)
    have_grn_fot = fields.Boolean(string='Have GRN FOT', compute='compute_data_invisible', store=True)

    # PTBF Fields for fixation
    type_of_ptbf_payment = fields.Selection([
        ('fixation', 'Fixation'),
        ('advance', 'Advance'),
        ('fixation_advance', 'Fixation For Advance')
    ], string='Type Of PTBF Payment', default='fixation')
    price_tobe_fix = fields.Many2one('ptbf.fixprice', string='PTBF Fix Price No.')
    quantity_of_price_tobe_fix = fields.Float(string='Quantity Price To Be Fix', related='price_tobe_fix.quantity', store=True)
    price_usd = fields.Float(string='Price USD', related='price_tobe_fix.price_fix', store=True, digits=(12, 2))
    price_diff = fields.Float(string='DIFF', related='purchase_contract_id.diff_price', store=True, digits=(12, 0))
    final_price_usd = fields.Float(string='Final Price USD', compute='compute_price', store=True, digits=(12, 2))
    final_price_vnd = fields.Float(string='Final Price VND', compute='compute_price', store=True, digits=(12, 0))

    # PTBF Field for advance
    quantity_advance = fields.Integer(string='Advance Quantity')
    quantity_fix_advance = fields.Integer(string='Quantity Fix') # khong dung
    liffe_price = fields.Float(string='Liffe Price', digits=(12, 0))
    differencial_price = fields.Float(string='Differencial Price', compute='compute_price', store=True, digits=(12, 0))
    advance_price_usd = fields.Float(string='Advance Price (USD)', compute='compute_price', store=True, digits=(12, 2))
    total_advance_payment_usd = fields.Float(string='Total Advance Payment (USD)', compute='compute_price', store=True, digits=(12, 2))
    fx_rate = fields.Integer(string='FX')
    advance_price_vnd = fields.Integer(string='Advance Price (VND)', compute='compute_price', store=True)
    remain_qty_advance = fields.Integer(string='Remain Qty Advance')

    # PTBF Field for fixation for advance
    # khong dung
    fixation_advance_ids = fields.Many2many('request.payment', 'request_payment_advance_payment_rel', 'request_main_id', 'request_second_id', string='Fixation For Advance No.')

    fixation_advance_line_ids = fields.One2many('advance.line', 'request_id', string='Advance Line')
    reference_information_line_ids = fields.One2many('reference.information',  'request_id', string='Reference Information')
    qty_advance_fix = fields.Integer(string='Fix Quantity', compute='compute_total_qty', store=True)
    total_amount_usd = fields.Float(string='Total Amount USD', compute='compute_price', store=True, digits=(12, 2))
    average_rate = fields.Float(string='Average Rate', digits=(12, 0), compute='compute_price', store=True)
    rate = fields.Float(string='Rate', digits=(12, 0))

    def generate_advance_line(self):
        for rec in self:
            if not self.env.context.get('total'):
                if rec.qty_advance_fix == 0:
                    raise UserError(_("Hãy nhập số lượng muốn fix cho từng Advance mà bạn chọn!"))
                if not any(rec.fixation_advance_line_ids.filtered(lambda x: x.name)):
                    # Remain
                    value = {
                        'name': 'Phần còn lại/ Remain Payment:',
                        'request_id': rec.id,
                        'request_date': rec.date,
                        'total_advance_payment_usd': rec.total_amount_usd - sum(
                            rec.fixation_advance_line_ids.filtered(lambda x: not x.name).mapped('total_advance_payment_usd')),
                    }
                    self.env['advance.line'].create(value)
            if self.env.context.get('total'):
                advance_remain_line = self.fixation_advance_line_ids.filtered(lambda x: x.name == 'Phần còn lại/ Remain Payment:')
                advance_remain_line.write({
                    'request_amount': rec.request_amount - sum(self.fixation_advance_line_ids.filtered(lambda x: x.id != advance_remain_line.id).mapped('request_amount'))
                })
                # Total
                value = {
                    'name': 'Total:',
                    'request_id': rec.id,
                    'total_advance_payment_usd': sum(rec.fixation_advance_line_ids.mapped('total_advance_payment_usd')),
                    'request_amount': sum(rec.fixation_advance_line_ids.mapped('request_amount')),
                    'rate': sum(rec.fixation_advance_line_ids.mapped('request_amount')) / sum(rec.fixation_advance_line_ids.mapped('total_advance_payment_usd'))
                }
                self.env['advance.line'].create(value)

    def generate_reference_information(self):
        for rec in self:
            rec.reference_information_line_ids = [(5, 0)]
            check_advance_line = rec.fixation_advance_line_ids.filtered(lambda x: x.name and x.rate > 0)
            if not check_advance_line:
                raise UserError(_("Hãy nhập rate cho phần còn lại cần thanh toán!"))
            for line in rec.fixation_advance_line_ids:
                if not line.name:
                    value = {
                        'request_id': line.request_id.id,
                        'request_payment_id': line.request_payment_id.id
                    }
                    self.env['reference.information'].create(value)
                else:
                    value = {
                        'name': 'Phần còn lại/ Remain Payment:',
                        'request_id': line.request_id.id,
                        'total_advance_payment_usd': line.total_advance_payment_usd,
                        'rate': line.rate,
                        'request_amount': line.total_advance_payment_usd * line.rate
                    }
                    self.env['reference.information'].create(value)
            value = {
                'name': 'Total:',
                'request_id': rec.id,
                'total_advance_payment_usd': sum(rec.reference_information_line_ids.mapped('total_advance_payment_usd')),
                'rate': sum(rec.reference_information_line_ids.mapped('request_amount')) / sum(rec.reference_information_line_ids.mapped('total_advance_payment_usd')),
                'request_amount': sum(rec.reference_information_line_ids.mapped('request_amount'))
            }
            self.env['reference.information'].create(value)
            self.with_context(total=True).generate_advance_line()

    def get_date(self, date):
        if not date:
            date = time.strftime(DATE_FORMAT)
        date = datetime.strptime(date, DATE_FORMAT)
        return date.strftime('%d/%m/%Y')

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, 'Payment ' + str(rec.name) + ' at ' + str(self.get_date(str(rec.date)))))
        return result

    @api.depends('fixation_advance_line_ids', 'fixation_advance_line_ids.quantity_fix')
    def compute_total_qty(self):
        for rec in self:
            rec.qty_advance_fix = sum(rec.fixation_advance_line_ids.mapped('quantity_fix'))

    @api.depends('price_usd', 'price_diff', 'rate', 'type_of_ptbf_payment', 'liffe_price', 'quantity_advance', 'fixation_advance_line_ids',
                 'fixation_advance_line_ids.rate', 'fixation_advance_line_ids.request_amount', 'request_amount', 'payment_quantity',
                 'qty_advance_fix', 'rate', 'reference_information_line_ids', 'reference_information_line_ids.request_amount')
    def compute_price(self):
        for rec in self:
            if rec.type_of_ptbf_payment == 'fixation':
                rec.final_price_usd = rec.price_usd + rec.price_diff
                rec.final_price_vnd = self.custom_round((rec.final_price_usd * rec.rate)/ 1000)
            if rec.type_of_ptbf_payment == 'advance':
                rec.quantity_advance = rec.payment_quantity
                rec.differencial_price = rec.liffe_price + rec.price_diff
                rec.advance_price_usd = rec.differencial_price * rec.purchase_contract_id.percent_advance_price
                rec.total_advance_payment_usd = round((rec.advance_price_usd * rec.payment_quantity) / 1000, 2)
                if rec.payment_quantity > 0:
                    rec.advance_price_vnd = self.custom_round(rec.request_amount / rec.payment_quantity)
                else:
                    rec.advance_price_vnd = 0
            if rec.type_of_ptbf_payment == 'fixation_advance':
                rec.final_price_usd = rec.price_usd + rec.price_diff
                rec.total_amount_usd = self.custom_round(rec.final_price_usd * rec.qty_advance_fix)
                rec.average_rate = rec.fixation_advance_line_ids.filtered(lambda x: x.name == 'Total:').rate
                if rec.qty_advance_fix > 0:
                    rec.final_price_vnd = round(rec.reference_information_line_ids.filtered(lambda x: x.name == 'Total:').request_amount / rec.qty_advance_fix)
                else:
                    rec.final_price_vnd = 0

    @api.depends('delivery_70_ktn_ids', 'delivery_70_ids', 'grn_90_ids', 'grn_100_factory_ids', 'grn_100_fot_ids')
    def compute_data_invisible(self):
        for rec in self:
            rec.have_dr_ktn = False
            rec.have_dr = False
            rec.have_grn_90 = False
            rec.have_grn_100 = False
            rec.have_grn_fot = False
            if rec.delivery_70_ktn_ids:
                rec.have_dr_ktn = True
            if rec.delivery_70_ids:
                rec.have_dr = True
            if rec.grn_90_ids:
                rec.have_grn_90 = True
            if rec.grn_100_factory_ids:
                rec.have_grn_100 = True
            if rec.grn_100_fot_ids:
                rec.have_grn_fot = True

    @api.depends('attachment_ids')
    def compute_count_file(self):
        for rec in self:
            if rec.attachment_ids:
                rec.is_attach_file = '%s Files' % len(rec.attachment_ids)
            else:
                rec.is_attach_file = '0 File'

    def action_refuse(self):
        for rec in self:
            self.env['user.process.state'].create({
                'request_payment_id': rec.id,
                'user_id': self.env.user.id,
                'date': datetime.today(),
                'state': 'Refuse by %s' % self.env.user.name
            })
            rec.state = 'draft'

    def _get_new_state(self):
        return [
            ('draft', 'Draft'),
            ('request', 'Request'),
            ('security', 'Security'),
            ('purchasing', 'Purchasing'),
            ('approved', 'Accounting 1st'),
            ('accounting_2', 'Accounting 2nd'),
            ('approved_director', 'Approve by Director'),
            ('paid', 'Paid')
        ]

    @api.depends('request_payment_ids', 'request_amount', 'advance_payment_quantity')
    def _compute_request_payment(self):
        for request in self:
            total_payment = 0.0
            for line in request.request_payment_ids.filtered(lambda x: x.state == 'posted'):
                total_payment += line.amount
            request.total_payment = total_payment

            if not request.advance_payment_quantity:
                request.advance_price = 0.0
            else:
                request.advance_price = request.request_amount / request.advance_payment_quantity

            request.total_remain = request.request_amount - total_payment
            if request.total_remain == 0.0:
                if total_payment != 0:
                    if request.state != 'paid':
                        request.state = 'paid'

    def _create_stock_moves(self, picking, picking_type):
        moves = self.env['stock.move.line']
        price_unit = self.price_tobe_fix.final_price / 1000
        vals = {
            'warehouse_id': picking_type.warehouse_id.id,
            'picking_id': picking.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_id.uom_id.id,
            'init_qty': self.payment_quantity,
            'qty_done': self.payment_quantity or 0.0,
            'price_unit': price_unit,
            'picking_type_id': picking_type.id,
            'location_id': picking_type.default_location_src_id.id,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'date': self.date,
            'currency_id': self.purchase_contract_id.currency_id.id or False,
            'state': 'draft',
        }
        move_id = moves.sudo().create(vals)
        return move_id

    def create_picking(self, history_rate_id):
        contract_id = self.purchase_contract_id

        picking_type = self.env['stock.picking.type'].sudo().search([('name', '=', 'NPE -> NVP')])

        purchase_contract_id = contract_id

        var = {
            'warehouse_id': picking_type.warehouse_id.id,
            'picking_type_id': picking_type.id,
            'partner_id': purchase_contract_id.partner_id.id,
            'date': self.date,
            'date_done': self.date,
            'origin': purchase_contract_id.name,
            'location_dest_id': picking_type.default_location_dest_id.id,
            'location_id': picking_type.default_location_src_id.id,
            'purchase_contract_id': purchase_contract_id.id,
            'rate_ptbf': self.rate
        }
        picking = self.env['stock.picking'].sudo().create(var)
        history_rate_id.grn_id = picking.id

        self._create_stock_moves(picking, picking_type)

        picking.button_sd_validate()

    def approve_by_director(self):
        for record in self:
            self.env['user.process.state'].create({
                'request_payment_id': record.id,
                'user_id': self.env.user.id,
                'date': datetime.today(),
                'state': 'Approve by Director: %s' % self.env.user.name
            })
            value = False
            if self.type == 'ptbf' and self.type_of_ptbf_payment == 'fixation_advance':
                ptpf_fix_price = self.price_tobe_fix
                value = {
                    'date_receive': self.date,
                    'product_id': self.product_id.id,
                    'qty_receive': self.payment_quantity,
                    'qty_price': self.payment_quantity,
                    'final_price_en': self.final_price_usd,
                    'rate': self.average_rate,
                    'final_price_vn': self.final_price_vnd,
                    'total_amount_en': self.final_price_usd * self.payment_quantity,
                    'total_amount_vn': self.final_price_vnd * self.payment_quantity,
                    'history_id': ptpf_fix_price.id
                }
            if self.type == 'ptbf' and self.type_of_ptbf_payment == 'fixation':
                ptpf_fix_price = self.price_tobe_fix
                value = {
                    'date_receive': self.date,
                    'product_id': self.product_id.id,
                    'qty_receive': self.payment_quantity,
                    'qty_price': self.payment_quantity,
                    'final_price_en': self.final_price_usd,
                    'rate': self.rate,
                    'final_price_vn': self.final_price_vnd,
                    'total_amount_en': self.final_price_usd * self.payment_quantity,
                    'total_amount_vn': self.final_price_vnd * self.payment_quantity,
                    'history_id': ptpf_fix_price.id
                }
            if value:
                history = self.env['history.rate'].create(value)
                self.create_picking(history)
            record.write({
                'state': 'approved_director'
            })

    def approve_accounting_v2(self):
        for record in self:
            self.env['user.process.state'].create({
                'request_payment_id': record.id,
                'user_id': self.env.user.id,
                'date': datetime.today(),
                'state': 'Accounting 2nd'
            })
            record.write({
                'state': 'accounting_2'
            })

    def btt_approved(self):
        for record in self:
            self.env['user.process.state'].create({
                'request_payment_id': record.id,
                'user_id': self.env.user.id,
                'date': datetime.today(),
                'state': 'Accounting 1st'
            })
            record.state = 'approved'

    def approve_purchasing(self):
        for record in self:
            self.env['user.process.state'].create({
                'request_payment_id': record.id,
                'user_id': self.env.user.id,
                'date': datetime.today(),
                'state': 'Purchasing'
            })
            record.write({
                'state': 'purchasing'
            })

    def request_payment(self):
        for rec in self:
            self.env['user.process.state'].create({
                'request_payment_id': rec.id,
                'user_id': self.env.user.id,
                'date': datetime.today(),
                'state': 'Request'
            })
            rec.state = 'request'

    @api.depends('delivery_70_ids', 'delivery_array')
    def compute_dr_request(self):
        for rec in self:
            if rec.delivery_70_ids:
                rec.is_dr_request = True
            else:
                rec.is_dr_request = False

    @api.depends('payment_quantity', 'fix_price', 'liquidation_amount', 'deposit_amount', 'advance_payment_converted',
                 'total_interest', 'is_converted', 'type', 'type_of_ptbf_payment', 'final_price_vnd', 'total_advance_payment_usd',
                 'rate', 'qty_advance_fix')
    def _compute_request_amount(self):
        for rec in self:
            if rec.type == 'purchase':
                if rec.is_converted:
                    rec.request_amount = (rec.payment_quantity * rec.fix_price) - rec.advance_payment_converted - rec.total_interest - rec.liquidation_amount
                else:
                    rec.request_amount = (rec.payment_quantity * rec.fix_price) - rec.deposit_amount - rec.liquidation_amount
            if rec.type == 'consign':
                rec.request_amount = (rec.payment_quantity * rec.fix_price) - rec.deposit_amount - rec.liquidation_amount
            if rec.type == 'ptbf':
                if rec.type_of_ptbf_payment == 'fixation':
                    rec.request_amount = rec.payment_quantity * rec.final_price_vnd
                if rec.type_of_ptbf_payment == 'advance':
                    rec.request_amount = self.custom_round(rec.total_advance_payment_usd * rec.rate)
                if rec.type_of_ptbf_payment == 'fixation_advance':
                    rec.request_amount = rec.final_price_vnd * rec.qty_advance_fix

    @api.depends('converted_line_ids', 'converted_line_ids.advance_payment', 'converted_line_ids.interest')
    def compute_advance_payment_converted(self):
        for rec in self:
            rec.advance_payment_converted = sum(rec.converted_line_ids.mapped('advance_payment'))
            rec.total_interest = sum(rec.converted_line_ids.mapped('interest'))

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    def format_to_decimal(self, num):
        if not (1e-4 <= abs(num) < 1e4):
            return float("{:.5f}".format(num))
        return num

    def populate_converted_line_ids(self):
        for rec in self:
            rec.converted_line_ids = [(5, 0)]
            purchase_contract_origin = rec.purchase_contract_id
            npe_allocation = purchase_contract_origin.mapped('nvp_ids.npe_contract_id').sorted(lambda x: x.date_order)
            for npe in npe_allocation:
                qty_fix = purchase_contract_origin.mapped('nvp_ids').filtered(
                    lambda x: x.npe_contract_id.id == npe.id).product_qty - purchase_contract_origin.mapped('nvp_ids').filtered(
                    lambda x: x.npe_contract_id.id == npe.id).open_qty
                point_qty = qty_fix
                for line in npe.request_payment_ids.filtered(
                        lambda x: x.mirror_request_amount > 0).sorted(lambda x: int(x.name)):
                    seq = 0
                    for i in line.rate_ids.sorted(lambda x: x.date):
                        seq += 1
                        total_date = (i.date_end - i.date).days
                        rate = i.rate / 30 / 100
                        if seq == 1:
                            if point_qty - line.mirror_request_amount >= 0:
                                value = {
                                    'request_payment_id': rec.id,
                                    'request_origin_id': line.id,
                                    'fixation_qty': line.mirror_request_amount,
                                    'purchase_contract_id': line.purchase_contract_id.id,
                                    'fixation_price': line.fix_price,
                                    'advance_payment': line.mirror_request_amount * line.fix_price,
                                    'advance_date': i.date,
                                    'interest_rate': rate,
                                    'total_days': total_date,
                                    'interest': self.custom_round((line.mirror_request_amount * line.fix_price) * rate * total_date)
                                }
                                self.env['converted.line'].create(value)
                                point_qty -= line.mirror_request_amount
                                line.mirror_request_amount = 0
                            if point_qty > 0 > point_qty - line.mirror_request_amount:
                                convert_qty = point_qty
                                value = {
                                    'request_payment_id': rec.id,
                                    'request_origin_id': line.id,
                                    'fixation_qty': convert_qty,
                                    'purchase_contract_id': line.purchase_contract_id.id,
                                    'fixation_price': line.fix_price,
                                    'advance_payment': convert_qty * line.fix_price,
                                    'advance_date': i.date,
                                    'interest_rate': rate,
                                    'total_days': total_date,
                                    'interest': self.custom_round((convert_qty * line.fix_price) * rate * total_date)
                                }
                                self.env['converted.line'].create(value)
                                point_qty -= convert_qty
                                line.mirror_request_amount = line.mirror_request_amount - convert_qty
                        if seq > 1:
                            checking_line = self.env['converted.line'].search([
                                ('request_payment_id', '=', rec.id),
                                ('purchase_contract_id', '=', line.purchase_contract_id.id),
                                ('fixation_qty', '>', 0),
                                ('request_origin_id', '=', line.id)
                            ])
                            value = {
                                'request_payment_id': rec.id,
                                'request_origin_id': line.id,
                                'fixation_qty': 0,
                                'purchase_contract_id': line.purchase_contract_id.id,
                                'fixation_price': 0,
                                'advance_payment': 0,
                                'advance_date': i.date,
                                'interest_rate': rate,
                                'total_days': total_date,
                                'interest': self.custom_round((checking_line.fixation_qty * line.fix_price) * rate * total_date)
                            }
                            self.env['converted.line'].create(value)
                checking_convert_line = purchase_contract_origin.list_open_qty.filtered(lambda x: x.contract_id.id == npe.id)
                if checking_convert_line:
                    value = {
                        'request_payment_id': rec.id,
                        'request_origin_id': False,
                        'fixation_qty': checking_convert_line.qty,
                        'purchase_contract_id': npe.id,
                        'fixation_price': 0,
                        'advance_payment': 0,
                        'advance_date': False,
                        'interest_rate': 0,
                        'total_days': 0,
                        'interest': 0
                    }
                    self.env['converted.line'].create(value)
                if point_qty == 0:
                    continue

    @api.depends('history_quantity_payment', 'history_quantity_payment.quantity', 'purchase_contract_id', 'purchase_contract_id.total_qty', 'name')
    def compute_balance_quantity(self):
        for rec in self:
            other_request_payment = self.search([
                ('name', '<', int(rec.name)),
                ('purchase_contract_id', '=', rec.parent_id_purchase_contract)
            ], order='name asc')
            purchase_contract = self.env['purchase.contract'].browse(rec.parent_id_purchase_contract)
            rec.balance = purchase_contract.total_qty - sum(other_request_payment.mapped('payment_quantity'))

    @api.depends('balance', 'payment_quantity')
    def current_balance_qty(self):
        for rec in self:
            rec.current_balance = rec.balance - rec.payment_quantity

    @api.depends('name')
    def compute_history_payment(self):
        for rec in self:
            other_request_payment = self.search([
                ('name', '<', int(rec.name)),
                ('purchase_contract_id', '=', rec.parent_id_purchase_contract)
            ], order='name asc')
            for line in other_request_payment:
                date = str(line.date)
                dt = datetime.strptime(date, '%Y-%m-%d')
                new_date_str = dt.strftime('%d-%m-%Y')
                value = {
                    'request_payment_id': rec.id,
                    'name': 'Lần ' + str(line.name) + '\n' + str(new_date_str),
                    'quantity_char': 'Payment Quantity',
                    'quantity': line.payment_quantity
                }
                self.env['history.payment.quantity'].create(value)

    @api.depends('status_goods_ids', 'status_goods_ids.request_quantity', 'is_converted', 'quantity_contract', 'quantity_of_price_tobe_fix')
    def compute_payment_quantity(self):
        for rec in self:
            rec.payment_quantity = 0
            rec.mirror_request_amount = 0
            if rec.status_goods_ids:
                if rec.quantity_of_price_tobe_fix < sum(rec.status_goods_ids.mapped('request_quantity')):
                    raise UserError(_("Bạn không thể fix lớn hơn số lượng trong PTBF Price Fix: %s") % rec.quantity_of_price_tobe_fix)
                rec.payment_quantity = sum(rec.status_goods_ids.mapped('request_quantity'))
                rec.mirror_request_amount = rec.payment_quantity
            if rec.is_converted:
                rec.payment_quantity = rec.quantity_contract
                rec.mirror_request_amount = 0

    def action_hide_delivery(self):
        for rec in self:
            rec.hide_delivery = True

    def action_hide_delivery_ktn(self):
        for rec in self:
            rec.hide_delivery_ktn = True

    def action_hide_grn_ready(self):
        for rec in self:
            rec.hide_grn_ready = True

    def action_hide_grn_done(self):
        for rec in self:
            rec.hide_grn_done = True

    def action_hide_grn_fot_done(self):
        for rec in self:
            rec.hide_grn_fot_done = True

    def action_open_hide_delivery(self):
        for rec in self:
            rec.hide_delivery = False

    def action_open_hide_delivery_ktn(self):
        for rec in self:
            rec.hide_delivery_ktn = False

    def action_open_grn_ready(self):
        for rec in self:
            rec.hide_grn_ready = False

    def action_open_grn_done(self):
        for rec in self:
            rec.hide_grn_done = False

    def action_open_grn_fot_done(self):
        for rec in self:
            rec.hide_grn_fot_done = False

    @api.depends('delivery_70_ktn_ids', 'delivery_70_ktn_ids.delivery_id')
    def compute_delivery_ktn_array(self):
        for rec in self:
            rec.delivery_ktn_array = rec.delivery_70_ktn_ids.mapped('delivery_id').ids

    @api.depends('delivery_70_ids', 'delivery_70_ids.delivery_id')
    def compute_delivery_array(self):
        for rec in self:
            rec.delivery_array = rec.delivery_70_ids.mapped('delivery_id').ids

    @api.depends('grn_90_ids', 'grn_90_ids.picking_id')
    def compute_grn_90_array(self):
        for rec in self:
            rec.grn_90_array = rec.grn_90_ids.mapped('picking_id').ids

    @api.depends('grn_100_fot_ids', 'grn_100_fot_ids.picking_id')
    def compute_grn_100_fot_array(self):
        for rec in self:
            rec.grn_100_fot_array = rec.grn_100_fot_ids.mapped('picking_id').ids

    @api.depends('grn_100_factory_ids', 'grn_100_factory_ids.picking_id')
    def compute_grn_100_factory_array(self):
        for rec in self:
            rec.grn_100_factory_array = rec.grn_100_factory_ids.mapped('picking_id').ids

    @api.depends('delivery_70_ids', 'delivery_array', 'grn_90_ids', 'grn_90_array',
                 'grn_100_factory_ids', 'grn_100_factory_array', 'grn_100_fot_ids', 'grn_100_fot_array', 'delivery_70_ktn_ids', 'delivery_ktn_array')
    def compute_status_goods(self):
        for rec in self:
            delivery_status_goods = rec.status_goods_ids.filtered(lambda x: x.payment_percent == 70)
            grn_ready_status_goods = rec.status_goods_ids.filtered(lambda x: x.payment_percent == 90)
            grn_done_factory_status_goods = rec.status_goods_ids.filtered(lambda x: x.payment_percent == 100 and x.code == 4)
            grn_done_fot_status_goods = rec.status_goods_ids.filtered(lambda x: x.payment_percent == 100 and x.code == 5)

            if rec.delivery_70_ids or rec.delivery_70_ktn_ids:
                deliver = rec.delivery_70_ids.mapped('delivery_id').ids + rec.delivery_70_ktn_ids.mapped('delivery_id').ids
                delivery_status_goods.delivery_registration_ids = [(6, 0, deliver)]
                delivery_status_goods.paid_quantity = sum(rec.delivery_70_ids.mapped('paid_quantity')) + sum(rec.delivery_70_ktn_ids.mapped('paid_quantity'))
                delivery_status_goods.request_quantity = sum(rec.delivery_70_ids.mapped('request_qty')) + sum(rec.delivery_70_ktn_ids.mapped('request_qty'))

            if rec.grn_90_ids:
                grn_ready_status_goods.picking_ids = [(6, 0, rec.grn_90_ids.mapped('picking_id').ids)]
                grn_ready_status_goods.paid_quantity = sum(rec.grn_90_ids.mapped('paid_quantity'))
                grn_ready_status_goods.request_quantity = sum(rec.grn_90_ids.mapped('request_qty'))

            if rec.grn_100_factory_ids:
                grn_done_factory_status_goods.picking_ids = [(6, 0, rec.grn_100_factory_ids.mapped('picking_id').ids)]
                grn_done_factory_status_goods.paid_quantity = sum(rec.grn_100_factory_ids.mapped('paid_quantity'))
                grn_done_factory_status_goods.request_quantity = sum(rec.grn_100_factory_ids.mapped('request_qty'))

            if rec.grn_100_fot_ids:
                grn_done_fot_status_goods.picking_ids = [(6, 0, rec.grn_100_fot_ids.mapped('picking_id').ids)]
                grn_done_fot_status_goods.description_name_fot = '; '.join(i.description_name for i in rec.grn_100_fot_ids.mapped('picking_id'))
                grn_done_fot_status_goods.paid_quantity = sum(rec.grn_100_fot_ids.mapped('paid_quantity'))
                grn_done_fot_status_goods.request_quantity = sum(rec.grn_100_fot_ids.mapped('request_qty'))

            if not rec.delivery_70_ids and not rec.delivery_70_ktn_ids:
                delivery_status_goods.delivery_registration_ids = [(5, )]
                delivery_status_goods.paid_quantity = sum(rec.delivery_70_ids.mapped('paid_quantity')) + sum(
                    rec.delivery_70_ktn_ids.mapped('paid_quantity'))
                delivery_status_goods.request_quantity = sum(rec.delivery_70_ids.mapped('request_qty')) + sum(
                    rec.delivery_70_ktn_ids.mapped('request_qty'))
            if not rec.grn_90_ids:
                grn_ready_status_goods.picking_ids = [(5, )]
            if not rec.grn_100_factory_ids:
                grn_done_factory_status_goods.picking_ids = [(5, )]
            if not rec.grn_100_fot_ids:
                grn_done_fot_status_goods.picking_ids = [(5, )]
                grn_done_fot_status_goods.description_name_fot = ''



    @api.model
    def default_get(self, fields):
        res = super(RequestPayment, self).default_get(fields)
        if self.env.context.get('default_parent_id', False):
            res['parent_id_purchase_contract'] = self.env.context.get('default_parent_id', False)
            purchase_contract = self.env['purchase.contract'].browse(self.env.context.get('default_parent_id', False))
            if purchase_contract.type == 'purchase' and purchase_contract.nvp_ids:
                res['is_converted'] = True
        purchase_contract = self.env['purchase.contract'].browse(self.env.context.get('default_parent_id', False))
        if 'status_goods_ids' in fields:
            status_goods_1 = self.env['status.goods.name'].search([
                ('code', '>=', 0),
                ('code', '<=', 3)
            ])

            status_goods_2 = self.env['status.goods.name'].search([
                ('code', '>', 3),
                ('code', '<', 10)
            ])
            status_goods_section_1 = self.env['status.goods.name'].search([
                ('code', '=', 10),
            ])
            status_goods_section_2 = self.env['status.goods.name'].search([
                ('code', '=', 11),
            ])


            res.update({
                'status_goods_ids':
                # First Section
                    [(0, 0, {
                        "name": i.id,
                        "display_type": 'line_section',
                    }) for i in status_goods_section_1]
                    +
                    # Records for first section
                    [(0, 0, {
                        "name": i.id,
                        "payment_percent": i.payment_percent,
                        'sequence': len(purchase_contract.request_payment_ids) + 1
                    }) for i in status_goods_1]
                    +
                    # Second section
                    [(0, 0, {
                        "name": i.id,
                        "display_type": 'line_section',
                    }) for i in status_goods_section_2]
                    +
                    # Records for second section
                    [(0, 0, {
                        "name": i.id,
                        "payment_percent": i.payment_percent,
                        'sequence': len(purchase_contract.request_payment_ids) + 1
                    }) for i in status_goods_2]
            })
        return res

    def unlink(self):
        for rec in self:
            for line in rec.converted_line_ids:
                line.request_origin_id.mirror_request_amount += line.fixation_qty
            if rec.state != 'draft':
                raise UserError(_("You cannot delete the request payment, it's not in Draft state!"))
        return super(RequestPayment, self).unlink()

    def security_approve(self):
        for rec in self:
            self.env['user.process.state'].create({
                'request_payment_id': rec.id,
                'user_id': self.env.user.id,
                'date': datetime.today(),
                'state': 'Security'
            })
            rec.state = 'security'

    def print_nvp_fix_from_npe(self):
        return self.env.ref('sd_security_gate_vietnam.printout_payment_npv_fixed_by_npe_report').report_action(self)

    def print_request_payment_npe(self):
        return self.env.ref('sd_security_gate_vietnam.printout_request_payment_npe_report').report_action(self)

class StatusGoods(models.Model):
    _name = 'status.goods'

    name = fields.Many2one('status.goods.name', string='Status of Goods')
    code = fields.Integer(related='name.code', store=True)
    display_type = fields.Selection(
        selection=[
            ('line_section', "Section"),
            ('line_note', "Note"),
        ],
        default=False)
    request_payment_id = fields.Many2one('request.payment')
    purchase_contract_id = fields.Integer('purchase.contract', related='request_payment_id.parent_id_purchase_contract', store=True)
    sequence = fields.Char(string='Sequence')
    payment_percent = fields.Integer(string='Payment %')
    picking_ids = fields.Many2many('stock.picking', 'status_goods_picking_rel', 'status_goods_id', 'picking_id', string='Document GRN')
    delivery_registration_ids = fields.Many2many('ned.security.gate.queue', 'status_goods_security_rel', 'status_goods_id', 'security_id',  string='Document DR')
    description_name_fot = fields.Text(string='FOT Name')
    total_quantity = fields.Float(string='Total Quantity', compute='compute_total_quantity', store=True, digits=(12, 0))
    paid_quantity = fields.Float(string='Paid Quantity', digits=(12, 0))
    request_quantity = fields.Float(string='Request Quantity', digits=(12, 0))

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    @api.depends('delivery_registration_ids', 'picking_ids', 'delivery_registration_ids.approx_quantity', 'picking_ids.total_qty', 'picking_ids.total_init_qty', 'payment_percent')
    def compute_total_quantity(self):
        for rec in self:
            if rec.delivery_registration_ids or rec.picking_ids:
                if rec.payment_percent == 70:
                    rec.total_quantity = self.custom_round((sum(i.approx_quantity for i in rec.delivery_registration_ids)))
                if rec.payment_percent == 90:
                    rec.total_quantity = self.custom_round((sum(i.total_init_qty for i in rec.picking_ids)))
                if rec.payment_percent == 100:
                    rec.total_quantity = self.custom_round((sum(i.total_qty for i in rec.picking_ids)))
            else:
                rec.total_quantity = 0


class StatusGoodsName(models.Model):
    _name = 'status.goods.name'

    name = fields.Text(string='Status of Goods')
    code = fields.Integer(string='Code')
    payment_percent = fields.Integer(string='Payment %')