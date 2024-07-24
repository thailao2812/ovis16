# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime, date, timedelta

    
class PurchaseContractLine(models.Model):
    _name = "purchase.contract.line"
    _inherit = ['mail.thread']
    
    def _compute_tax_id(self):
        for line in self:
            fpos = line.contract_id.partner_id.property_account_position_id
            if fpos:
                if self.env.uid == SUPERUSER_ID and line.contract_id.company_id:
                    taxes = fpos.map_tax(line.product_id.taxes_id).filtered(lambda r: r.company_id == line.contract_id.company_id)
                else:
                    taxes = fpos.map_tax(line.product_id.taxes_id)
                line.tax_id = taxes
            else:
                line.tax_id = line.product_id.taxes_id if line.product_id.taxes_id else False
                
    @api.depends('product_qty', 'price_unit', 'tax_id')
    def _compute_amount(self):
        for line in self:
            price = line.price_unit
            taxes = line.tax_id.compute_all(price, line.contract_id.currency_id, line.product_qty, product=line.product_id, partner=line.contract_id.partner_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })
    
    contract_id = fields.Many2one('purchase.contract', string='Contract Reference', ondelete='cascade', index=True, copy=False)
    name = fields.Text(string='Description', required=True)
    sequence = fields.Integer(string='Sequence', default=10)

    
    company_id = fields.Many2one(related='contract_id.company_id', string='Company', store=True, readonly=True)
    partner_id = fields.Many2one(related='contract_id.partner_id', store=True, string='Customer')
    
    state = fields.Selection(selection=[('draft', 'New'), ('approved', 'Approved'), ('done', 'Done'), ('cancel', 'Cancelled')],
         related='contract_id.state', string='Status', readonly=True, copy=False, store=True, default='draft')
    
    currency_id = fields.Many2one(related='contract_id.currency_id', store=True, string='Currency', readonly=True)
    
    product_id = fields.Many2one('product.product', string='Product', domain=[('sale_ok', '=', True)], change_default=True, ondelete='restrict', required=True)
    product_qty = fields.Float(string='Qty', digits=(12, 0), required=True, default=1.0)
    product_uom = fields.Many2one('uom.uom', string='UoM', required=True)
    price_unit = fields.Float('Unit Price', required=True, default=0.0)
    tax_id = fields.Many2many('account.tax', string='Taxes',)
    
    price_subtotal = fields.Float(compute='_compute_amount', string='Subtotal', readonly=True, store=True,digits=(16, 0))
    price_tax = fields.Monetary(compute='_compute_amount', string='Taxes', readonly=True, store=True)
    price_total = fields.Monetary(compute='_compute_amount', string='Total', readonly=True, store=True)
    delivery_tolerance = fields.Float(string="Delivery Tolerance", default=0.0)
    

    @api.onchange('product_id')
    def product_id_change(self):
        if not self.product_id:
            return {'domain': {'product_uom': []}}

        vals = {}
        domain = {'product_uom': [('category_id', '=', self.product_id.uom_id.category_id.id)]}
        if not (self.product_uom and (self.product_id.uom_id.category_id.id == self.product_uom.category_id.id)):
            vals['product_uom'] = self.product_id.uom_id

        product = self.product_id.with_context(
            lang=self.contract_id.partner_id.lang,
            partner=self.contract_id.partner_id.id,
            quantity=self.product_qty,
            uom=self.product_uom.id
        )

        name = product.name_get()[0][1]
        if product.description_sale:
            name += '\n' + product.description_sale
        
        if not self.name:
            vals['name'] = name

        self._compute_tax_id()

        # if self.contract_id.partner_id:
        #     vals['price_unit'] = self.env['account.tax']._fix_tax_included_price(product.price, product.taxes_id, self.tax_id)
        self.update(vals)
        return {'domain': domain}
    
    def _create_stock_moves(self, line, picking,picking_type, qty):
        moves = self.env['stock.move.line']
#         price_unit = line.price_unit * picking.total_qty / picking.total_init_qty
        price_unit = line.price_unit
        if line.tax_id:
            price_unit = line.tax_id.compute_all(price_unit, currency=line.contract_id.currency_id, quantity=1.0)['total_excluded']
        # if line.product_uom.id != line.product_id.uom_id.id:
        #     price_unit = price_unit * (line.product_uom.factor / line.product_id.uom_id.factor)
        
        #Quy doi ra USD
        price_unit = self.env.user.company_id.second_currency_id.with_context(date=line.contract_id.date_order).compute(price_unit, 
                                                                                                 self.env.user.company_id.currency_id)
        
        vals = {
                'warehouse_id':picking_type.warehouse_id.id,
                'picking_id': picking.id,
                # 'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'init_qty':qty,
                'qty_done': qty or 0.0,
                'price_unit': price_unit,
                # 'tax_id': [(6, 0, [x.id for x in i.tax_id])],
                'picking_type_id': picking_type.id,
                'location_id': picking_type.default_location_src_id.id,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'date': line.contract_id.date_order,
                # 'exchange_rate':this.purchase_contract_id.exchange_rate or 1,
                'currency_id':line.contract_id.currency_id.id or False,
                # 'type': picking_type.code,
                'state':'draft',
                # 'scrapped': False,
                'price_currency':line.price_unit or 0.0,
                }
        
        move_id = moves.create(vals)
        return move_id
        
    
    
######################### NED CONTRACT  #####################################################################################################################
    premium = fields.Float(string='Subsidy')
    diff_price = fields.Float(string='Differencial Price')
    date_fix = fields.Date(string='Reference Price Month')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    # SON create type_price_weight
    type_price_weight = fields.Selection([
        ('vndkg', 'VND/Kg'),
        ('vndmts', 'VND/Mts'),
        ('usdmts', 'USD/Mts'),
        ('centlb', 'Cent/Lb')
    ], string='Price/Weight',  copy=False, default='vndkg')
    
######################### END NED CONTRACT  #######################################################################################################

######################### NED CONTRACT  VN #####################################################################################################################

    
    deadline_date = fields.Date(string='Deadline Date', related='contract_id.deadline_date', store=True)
    type = fields.Selection(related='contract_id.type', store=True, string='Type')
    cert_type = fields.Selection(related='contract_id.cert_type', store=True, string='Cert Type')
    state = fields.Selection(related='contract_id.state', store=True, string='State')
    contract_p_id = fields.Many2one('s.contract', related='contract_id.contract_p_id', store=True, string='P Ref')
    date_order = fields.Date(related='contract_id.date_order', store=True, string='Ctr Date')
    delivery_place_id = fields.Many2one('delivery.place', related='contract_id.delivery_place_id', string='Delivery', store=True)
    certificate_id = fields.Many2one('ned.certificate', related='contract_id.certificate_id', string='Certificate', store=True)
    qty_mt = fields.Float(string='Qty (MT)')
    delivery_from = fields.Date(related='contract_id.delivery_from', string="Delivery From", store=True)
    delivery_to = fields.Date(related='contract_id.delivery_to', string='Delivery To', store=True)
    certification_type = fields.Char(string='Ctr Type')
    ex = fields.Float(string='FX')  # waiting
    trade_month = fields.Char(string='Trade Month')
    total_lot = fields.Float(string='Total Lot')
    fix_lot = fields.Float(string='Total Lot')
    unfix_lot = fields.Float(string='Unfixed Lot')
    fix_status = fields.Char(string='Fixation Status')
    fixation_date = fields.Date(string='Fixation Date')
    trader_id = fields.Many2one('res.users', related='contract_id.trader_id', string='Trader', store=True)
    crop_id = fields.Many2one('ned.crop', string='Crop', related='contract_id.crop_id', store=True)
    transport_to_factory = fields.Float(string='Transport To Factory')
    cost_to_fob_hcm = fields.Float(string='Cost To FOB HCM')
    pre_dis_vs_g2 = fields.Float(string='Pre/Dis Vs G2')
    cert_pre = fields.Float(string='Cert Pre')
    g2_fob_equiv = fields.Float(string='G2 FOB equiv (USD/MT)')
    product_fob = fields.Float(string='Product FOB')

    qty_received = fields.Float(string='Received Qty(MT)', digits=(12, 2))
    qty_unreceived = fields.Float(string='Undelivery Qty(MT)', digits=(12, 2))
    delivery_status = fields.Char(string='Delivery Status')
    count_down = fields.Char(string='Countdown')
    provisional_amount = fields.Float(string='Provisional Amount (USD)')
    stoploss_level = fields.Float(string='Stoploss Level')
    hedged_fixed_level = fields.Float(string='Hedged/Fixed Level') #waiting

    hedged_fixed_level_report = fields.Float(string='Hedged/Fixed Level')

    ctr_fob_price = fields.Float(string='Ctr FOB Price')
    mtm_fob_price = fields.Float(string='MTM FOB Price')
    price_diff_usd_mt = fields.Float(string='Price Diff (USD/MT)')
    flat_exposure = fields.Float(string='Flat Exposure (USD)')
    diff_exposure = fields.Float(string='Diff Exposure (USD)')
    ptbf_unpaid_amount = fields.Float(string='PTBF Unpaid Amount 30% (USD)')
    deposit = fields.Float(string='Deposit')
    sum_exposure = fields.Float(string='Sum Exposure (USD)')
    in_exposure = fields.Char(string='In Exposure')
    grade_2 = fields.Char(string='Grade 2')
    group_location = fields.Char(string='Group Location')
    difams = fields.Float(string='DIFF AMS') # waiting


    def call_compute_all(self):
        for record in self.env['purchase.contract.line'].sudo().search([
            ('type', 'in', ['purchase', 'ptbf']),
            ('cert_type', '=', 'normal')
        ]):
            record._compute_hedged_fixed_level_report()
            record._compute_grade_2_and_group_location()
            record._compute_trade_month()
            record._compute_cert_type()
            record._compute_qty_mt()
            record._compute_total_fix_lot()
            record._compute_unfixed_lot()
            record._compute_fixation_status()
            record._compute_transport_to_factory()
            record._compute_cost_to_fob_hcm()
            record._compute_pre_dis_g2()
            record._compute_cert_pre()
            record._compute_g2_fob_equiv()
            record._compute_product_fob()
            record._compute_qty()
            record._compute_stoploss_level()
            record._compute_sum_exposure()
            record._compute_in_exposure()

    def _compute_hedged_fixed_level_report(self):
        for record in self:
            if record.contract_id.type in ['purchase', 'consign']:
                record.hedged_fixed_level_report = record.hedged_fixed_level
            if record.contract_id.type == 'ptbf':
                if len(record.contract_id.ptbf_ids) == 1:
                    record.hedged_fixed_level_report = sum(i.price_fix for i in record.contract_id.ptbf_ids)
                if len(record.contract_id.ptbf_ids) > 1:
                    record.hedged_fixed_level_report = sum(i.price_fix * i.quantity for i in record.contract_id.ptbf_ids) / sum(
                        i.quantity for i in record.contract_id.ptbf_ids)

    def _compute_grade_2_and_group_location(self):
        for record in self:
            record.grade_2 = record.product_id.name if record.product_id.default_code != 'FAQ' else 'FAQ'
            if record.product_id and record.certificate_id:
                if record.product_id.default_code == 'FAQ':
                    record.grade_2 = record.product_id.default_code + '-' + record.certificate_id.name
                else:
                    record.grade_2 = record.product_id.name + '-' + record.certificate_id.name
            if record.delivery_place_id.name == 'Katoen - AP' or record.delivery_place_id.name == 'Katoen - LT':
                record.group_location = 'KTN NBW'
            else:
                record.group_location = 'FACTORY'

    def _compute_trade_month(self):
        for record in self:
            month_code = record.contract_id.month_code
            record.trade_month = month_code
            # if record.contract_id.date_fix:
            #     date = datetime.strptime(record.contract_id.date_fix, DATE_FORMAT)
            #     if record.contract_id.rolling_ids:
            #         date = record.contract_id.rolling_ids.sorted(key=lambda l: l.date_fixed, reverse=True)[0].date_fixed
            #         date = datetime.strptime(date, DATE_FORMAT)
            #     date = str(date.strftime('%Y'))
            #     date_to_str = str([int(x) for x in date][2]) + str([int(x) for x in date][3])
            #     record.trade_month = str(date_to_str) + record.trade_month

    def _compute_cert_type(self):
        for record in self:
            record.certification_type = ''
            rate = self.env['market.price'].search([('commercialrate', '>', 0)], order='mdate desc', limit=1)
            total_advance_payment = sum(i.request_amount for i in record.contract_id.request_payment_ids.filtered(
                lambda x: x.type_payment == 'advance_payment'))
            if 'NVP' in record.contract_id.name:
                record.certification_type = 'Outright'
                record.provisional_amount = 0
            if 'PTBF' in record.contract_id.name:
                record.certification_type = 'PTBF'
                product_qty = sum(i.product_qty for i in record.contract_id.contract_line)
                product_qty_sum = product_qty + 2000
                product_qty_minus = product_qty - 2000
                if record.contract_id.qty_received == 0:
                    record.provisional_amount = 0
                elif record.contract_id.total_qty_fixed > 0 and record.contract_id.qty_received > 0:
                    if product_qty_minus <= record.contract_id.total_qty_fixed <= product_qty_sum:
                        record.provisional_amount = 0
                    elif record.contract_id.total_qty_fixed >= record.contract_id.qty_received:
                        record.provisional_amount = 0
                    elif record.contract_id.total_qty_fixed < record.contract_id.qty_received:
                        record.provisional_amount = (((record.contract_id.qty_received - record.contract_id.total_qty_fixed) * total_advance_payment) / record.contract_id.qty_received) / (rate.commercialrate)

                elif record.contract_id.total_qty_fixed == 0 and record.contract_id.qty_received > 0:
                    record.provisional_amount = (total_advance_payment) / (rate.commercialrate) # note lại cho PTBF 00399

    def _compute_qty_mt(self):
        for record in self:
            record.qty_mt = record.product_qty / 1000

    def _compute_total_fix_lot(self):
        for record in self:
            record.total_lot = record.product_qty / 10000
            if record.certification_type == 'PTBF':
                if record.contract_id.ptbf_ids:
                    record.fix_lot = sum(i.quantity for i in record.contract_id.ptbf_ids) / 10000
                else:
                    record.fix_lot = 0
            else:
                record.fix_lot = record.product_qty / 10000

    def _compute_unfixed_lot(self):
        for record in self:
            record.unfix_lot = 0
            if record.certification_type == 'Outright':
                record.unfix_lot = 0
            if record.certification_type == 'PTBF':
                record.unfix_lot = record.total_lot - record.fix_lot

    def _compute_fixation_status(self):
        for record in self:
            if record.certification_type == 'Outright':
                record.fix_status = 'Fully Fixed'
            elif record.unfix_lot == 0:
                record.fix_status = 'Fully Fixed'
            elif record.total_lot > record.unfix_lot > 0:
                record.fix_status = 'Partial Fixed'
            else:
                record.fix_status = 'Unfixed'

    def _compute_transport_to_factory(self):
        for record in self:
            fx_trade = self.env['fx.trade'].search([
                ('location_id', '=', record.delivery_place_id.id),
                ('fx_trade_root_id.effective_date', '<=', record.date_order),
                ('fx_trade_root_id.state', '=', 'run')
            ])
            if fx_trade:
                record.transport_to_factory = fx_trade.t_cost_factory
            else:
                record.transport_to_factory = 0

    def _compute_cost_to_fob_hcm(self):
        for record in self:
            record.cost_to_fob_hcm = 0
            if record.product_id.default_code == 'FAQ':
                partner_code = record.partner_id.partner_code
                condition_fob = self.env['cost.fob'].search([
                    ('product_id', '=', record.product_id.id),
                    ('fob_value_id.effective_date', '<=', record.date_order),
                    ('fob_value_id.state', '=', 'run')
                ])
                if condition_fob:
                    condition_fob = condition_fob.filtered(lambda x: x.partner_code in str(partner_code))
                    if not condition_fob:
                        fob = self.env['cost.fob'].search([
                            ('partner_code', '=', 'Khác'),
                            ('fob_value_id.effective_date', '<=', record.date_order),
                            ('fob_value_id.state', '=', 'run')
                        ])
                        if fob:
                            record.cost_to_fob_hcm = fob.cost_fob_hcm
                    else:
                        record.cost_to_fob_hcm = condition_fob.cost_fob_hcm
            else:
                delivery = record.delivery_place_id.id
                condition_fob_delivery = self.env['cost.fob'].search([
                    ('delivery_to_location', '=', delivery),
                    ('fob_value_id.effective_date', '<=', record.date_order),
                    ('fob_value_id.state', '=', 'run')
                ])
                if condition_fob_delivery:
                    record.cost_to_fob_hcm = condition_fob_delivery.cost_fob_hcm
                else:
                    condition_fob_diff_delivery = self.env['cost.fob'].search([
                        ('diff_delivery_to_location', '=', 'Different'),
                        ('fob_value_id.effective_date', '<=', record.date_order),
                        ('fob_value_id.state', '=', 'run')
                    ])
                    if condition_fob_diff_delivery:
                        record.cost_to_fob_hcm = condition_fob_diff_delivery.cost_fob_hcm

    def _compute_pre_dis_g2(self):
        for record in self:
            grade_premium = self.env['grade.premium'].search([
                ('grade_id', '=', record.product_id.id),
                ('grade_premium_root_id.effective_date', '<=', record.date_order),
                ('grade_premium_root_id.state', '=', 'run')
            ])
            if grade_premium:
                record.pre_dis_vs_g2 = grade_premium.premium_discount_g2
            else:
                record.pre_dis_vs_g2 = 0

    def _compute_cert_pre(self):
        for record in self:
            cert_pre_line = self.env['cert.pre.line'].search([
                ('certificate_id', '=', record.certificate_id.id),
                ('cert_pre_id.effective_date', '<=', record.date_order),
                ('cert_pre_id.state', '=', 'run'),
            ])
            if cert_pre_line:
                record.cert_pre = sum(i.price_in_usd for i in cert_pre_line)
            else:
                record.cert_pre = 0

    def _compute_g2_fob_equiv(self):
        for record in self:
            record.g2_fob_equiv = record.diff_price + (record.transport_to_factory + record.cost_to_fob_hcm) - \
                                  (record.cert_pre + record.pre_dis_vs_g2)

    def _compute_product_fob(self):
        for record in self:
            record.product_fob = record.g2_fob_equiv * (record.product_qty / 1000)

    def _compute_qty(self):
        for record in self:
            date_deadline = record.contract_id.deadline_date
            qty_mt = record.product_qty / 1000
            market_price = self.env['market.price'].search([
                ('liffe_month', '=', record.contract_id.month_code)
            ], order='mdate desc', limit=1)
            if record.contract_id.nvp_ids:
                received = 0
                for line in record.contract_id.nvp_ids:
                    received += line.product_qty

                if record.contract_id.state == 'done':
                    record.qty_unreceived = 0
                else:
                    record.qty_unreceived = (record.contract_id.total_qty - received) / 1000
                record.qty_received = received / 1000

                if qty_mt - record.qty_received < 2:
                    record.delivery_status = 'Delivered'
                    record.count_down = 'Delivered'
                    if market_price and record.fix_status == 'Unfixed':
                        record.ptbf_unpaid_amount = (record.diff_price + record.hedged_fixed_level_report) * record.fix_lot * 10 + record.unfix_lot * 10 * (
                                                                 record.diff_price + float(market_price.liffe)) - record.provisional_amount
                    elif not market_price and record.fix_status == 'Unfixed':
                        record.ptbf_unpaid_amount = (record.diff_price + record.hedged_fixed_level_report) * record.fix_lot * 10 + record.unfix_lot * 10 * record.diff_price - record.provisional_amount
                else:
                    record.delivery_status = 'Undelivered'
                    if date_deadline:
                        record.count_down = (
                                datetime.strptime(str(date_deadline), '%Y-%m-%d').date() - datetime.today().date()).days
                    else:
                        record.count_down = False
            else:
                received = 0
                for line in record.contract_id.stock_allocation_ids:
                    if line.contract_id.state == 'approved':
                        received += line.qty_allocation or 0.0
                if record.contract_id.state == 'done':
                    record.qty_unreceived = 0
                else:
                    record.qty_unreceived = (record.contract_id.total_qty - received) / 1000
                record.qty_received = received / 1000
                if qty_mt - record.qty_received < 2:
                    record.delivery_status = 'Delivered'
                    record.count_down = 'Delivered'
                    if market_price and record.fix_status == 'Unfixed':
                        record.ptbf_unpaid_amount = (record.diff_price + record.hedged_fixed_level_report) * record.fix_lot * 10 + record.unfix_lot * 10 * (record.diff_price + float(market_price.liffe)) - record.provisional_amount
                    elif not market_price and record.fix_status == 'Unfixed':
                        record.ptbf_unpaid_amount = (record.diff_price + record.hedged_fixed_level_report) * record.fix_lot * 10 + record.unfix_lot * 10 * record.diff_price - record.provisional_amount
                else:
                    record.delivery_status = 'Undelivered'
                    if date_deadline:
                        record.count_down = (
                                datetime.strptime(str(date_deadline), '%Y-%m-%d').date() - datetime.today().date()).days
                    else:
                        record.count_down = False
            if record.qty_unreceived < 2:
                record.ctr_fob_price = 0
                record.mtm_fob_price = 0
            elif record.certification_type == 'PTBF' and record.fix_status == 'Unfixed':
                if market_price:
                    record.ctr_fob_price = record.g2_fob_equiv + float(market_price.liffe)
                else:
                    record.ctr_fob_price = record.g2_fob_equiv
            else:
                record.ctr_fob_price = record.hedged_fixed_level_report + record.g2_fob_equiv
            if market_price:
                record.mtm_fob_price = market_price.faq_price
            else:
                market_price_spot = self.env['market.price'].search([
                    ('liffe_month', '=', 'Spot')
                ], order='mdate desc', limit=1)
                if market_price_spot:
                    if record.product_id.default_code == 'FAQ':
                        record.mtm_fob_price = market_price_spot.faq_price
                    else:
                        record.mtm_fob_price = market_price_spot.faq_price - 10
            record.price_diff_usd_mt = record.mtm_fob_price - record.ctr_fob_price

            if record.fix_status == 'Unfixed':
                record.flat_exposure = record.qty_unreceived * record.price_diff_usd_mt
            if record.fix_status == 'Fully Fixed':
                record.diff_exposure = 0

    def _compute_stoploss_level(self):
        for record in self:
            if record.certification_type == 'Outright' or record.delivery_status == 'Undelivered' \
                    or record.fix_status == 'Fully Fixed' or record.provisional_amount == 0:
                record.stoploss_level = 0
            else:
                config = self.env['stoploss.line'].search([
                    ('stop_loss_config_id.effective_date', '<=', record.date_order),
                    ('stop_loss_config_id.state', '=', 'run')
                ])
                if config:
                    if record.qty_received > record.contract_id.total_qty_fixed / 1000:
                        record.stoploss_level = config.price + (record.provisional_amount / (record.qty_received - (record.contract_id.total_qty_fixed / 1000))) - record.diff_price
                    else:
                        record.stoploss_level = 0

    def _compute_sum_exposure(self):
        for record in self:
            record.sum_exposure = record.flat_exposure + record.diff_exposure - record.ptbf_unpaid_amount - record.deposit

    def _compute_in_exposure(self):
        for record in self:
            purchase_contract_line = self.env['purchase.contract.line'].search([
                ('partner_id', '=', record.partner_id.id),
                ('id', '!=', record.id),
                ('type', 'in', ['purchase', 'ptbf']),
                ('cert_type', '=', 'normal'),
                ('delivery_status', '=', 'Undelivered')
            ])
            if purchase_contract_line:
                calculated = sum(i.qty_unreceived for i in purchase_contract_line) + record.qty_unreceived
                if calculated > 3:
                    record.in_exposure = 'Yes'
                else:
                    record.in_exposure = 'No'
            else:
                calculated = record.qty_unreceived
                if calculated > 3:
                    record.in_exposure = 'Yes'
                else:
                    record.in_exposure = 'No'

######################### END NED CONTRACT VN #######################################################################################################

    