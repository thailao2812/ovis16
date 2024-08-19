# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class SaleContractIndia(models.Model):
    _name = 'sale.contract.india'
    _inherit = ['mail.thread']
    _description = 'Pro Forma Sales Contract - Create'

    name = fields.Char(string='SN No.', tracking=True)
    crop_id = fields.Many2one('ned.crop', string='Season', tracking=True, required=True)
    partner_id = fields.Many2one('res.partner', string='Customer Name', tracking=True, required=True)
    partner_address = fields.Char(string='Customer Address', required=True)
    sn_date = fields.Date(string='SN Date', tracking=True)
    contact_id = fields.Many2one('res.partner', string='Contact Person', tracking=True)
    contact_person = fields.Char(string='Contact Person', tracking=True)
    inco_term_id = fields.Many2one('account.incoterms', string='Inco Terms')
    payment_term_id = fields.Many2one('account.payment.term', string='Payment Terms', required=True)
    payment_term_description = fields.Char(string='Payment Terms Description')
    shipment = fields.Char(string='Shipment')
    arbitration = fields.Selection([
        ('london', 'If any in London'),
        ('newyork', 'If any in New York')
    ], string='Arbitration', default=None)
    general_condition = fields.Char(string='General Condition', tracking=True)
    special_condition = fields.Char(string='Special Condition', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approve', 'Approve'),
        ('approve_allocation', 'Approve Allocation'),
        ('approve_sc_link', 'Approve Allocation SC')
    ], string='State', default='draft', tracking=True)
    p_number = fields.Char(string='P Number')
    p_date = fields.Date(string='P Date')
    product_id = fields.Many2one('product.product', related='line_ids.product_id', store=True)
    item_group_id = fields.Many2one('product.group', related='line_ids.item_group_id', store=True)
    total_quantity = fields.Float(string='PSC Qty(Kg)', compute='_compute_quantity', store=True)
    allocated_quantity = fields.Float(string='Allocated Qty(Kg)', compute="_compute_transaction_qty", store=True)
    balance_quantity = fields.Float(string='Balance Qty(Kg)', compute="_compute_transaction_qty", store=True)
    allocated_quantity_sc = fields.Float(string='Allocated Qty(Kg)', compute="_compute_transaction_sc_qty", store=True)
    balance_quantity_sc = fields.Float(string='Balance Qty(Kg)', compute="_compute_transaction_sc_qty", store=True)
    line_purchase_ids = fields.One2many('psc.to.pc.linked', 'sale_contract_id', string='Line Purchase')
    line_ids = fields.One2many('sale.contract.line.india', 'sale_contract_id', string='Line')
    sale_contract_factory_ids = fields.One2many('psc.to.sc.linked', 'sale_contract_id', string='Line Sale Contract')
    state_p = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approve')
    ], string='State P Number', default='draft')
    check_state_p = fields.Boolean(string='Check State P', compute='compute_check_state_p', store=True)
    price_unit = fields.Float(string='Price unit', related='line_ids.price_unit', store=True)
    unit = fields.Float(string='Unit', related='line_ids.price_unit', store=True)
    packing_id = fields.Many2one('ned.packing', string='Packing Nature', related='line_ids.packing_id', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='line_ids.currency_id', store=True)
    price_uom = fields.Many2one('uom.uom', string='UOM', related='line_ids.price_uom', store=True)

    @api.depends('p_number', 'p_date')
    def compute_check_state_p(self):
        for record in self:
            if not record.p_number:
                record.check_state_p = False
            else:
                record.check_state_p = True

    def button_approve_p_data(self):
        for record in self:
            if not record.p_number or not record.p_date:
                raise UserError(_("You have to input P number and P date before approve Sale Contract!!!"))
            record.state_p = 'approve'

    def button_approve(self):
        for record in self:
            record.state = 'approve'
            record.button_approve_p_data()

    def button_approve_allocation(self):
        for record in self:
            record.state = 'approve_allocation'
            for line in record.line_purchase_ids:
                line.purchase_contract_id._compute_allocated_qty()
                line.purchase_contract_id._compute_open_qty()
                line.onchange_purchase_contract_id()

    def button_approve_allocation_sc(self):
        for record in self:
            record.state = 'approve_sc_link'
            for line in record.sale_contract_factory_ids:
                line.s_contract._compute_total_allocated()
                line.onchange_s_contract()

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        if self.partner_id:
            street = ', '.join([x for x in (self.partner_id.street, self.partner_id.street2) if x])
            if self.partner_id.district_id:
                street += ' ' + self.partner_id.district_id.name + ' '
            if self.partner_id.city:
                street += self.partner_id.city + ' '
            if self.partner_id.state_id:
                street += self.partner_id.state_id.name
            self.partner_address = street

    @api.depends('line_purchase_ids', 'line_purchase_ids.current_allocated', 'total_quantity', 'state', 'line_purchase_ids.state')
    def _compute_transaction_qty(self):
        for record in self:
            record.allocated_quantity = sum(i.current_allocated for i in record.line_purchase_ids.filtered(
                lambda x: x.state == 'approve_allocation'))
            record.balance_quantity = record.total_quantity - record.allocated_quantity
            if record.balance_quantity < 0:
                raise UserError(_("You cannot allocate more than PSC Qty, check again!"))

    @api.depends('sale_contract_factory_ids', 'sale_contract_factory_ids.state_allocate',
                 'sale_contract_factory_ids.current_allocated')
    def _compute_transaction_sc_qty(self):
        for record in self:
            record.allocated_quantity_sc = sum(i.current_allocated for i in record.sale_contract_factory_ids.filtered(
                lambda x: x.state_allocate == 'submit'))
            record.balance_quantity_sc = record.total_quantity - record.allocated_quantity_sc

    @api.depends('line_ids', 'line_ids.quantity')
    def _compute_quantity(self):
        for record in self:
            record.total_quantity = sum(i.quantity for i in record.line_ids)

    def button_submit(self):
        for record in self:
            record.state = 'submit'

    def button_set_to_draft(self):
        for record in self:
            record.state = 'draft'
            record.state_p = 'draft'

    def write(self, vals):
        res = super(SaleContractIndia, self).write(vals)
        if self.p_number and not self.p_date:
            raise UserError(_("You have to input P Number and P Date!! Not leave it empty!!"))
        if not self.p_number and self.p_date:
            raise UserError(_("You have to input P Number and P Date!! Not leave it empty!!"))
        return res

    # @api.model
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].next_by_code('sale.contract.india')
    #     result = super(SaleContractIndia, self).create(vals)
    #     return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += ['|', ('name', operator, name), ('p_number', operator, name)]
        if self._context.get('fob_report') or self._context.get('psc_to_sc_report'):
            if self._context.get('item_group_ids')[0][2]:
                args += [('item_group_id', 'in', self._context.get('item_group_ids')[0][2])]
            else:
                args += [('item_group_id', '!=', False)]
            if self._context.get('date_from') and self._context.get('date_to'):
                args += [('p_date', '<=', self._context.get('date_to')),
                         ('p_date', '>=', self._context.get('date_from'))]
            if self._context.get('crop_id'):
                args += [('crop_id', '=', self._context.get('crop_id'))]
        sale_contract = self.with_context(from_name_search=True).search(args, limit=limit)
        return sale_contract.name_get()

    def name_get(self):
        res = []
        for record in self:
            if self.env.context.get('search_sale_contract'):
                res.append((record.id, record.name))
            else:
                res.append((record.id, record.p_number))
        return res


class SaleContractLineIndia(models.Model):
    _name = 'sale.contract.line.india'

    def get_default_uom(self):
        uom = self.env.ref('uom.product_uom_kgm')
        if uom:
            return uom.id
        else:
            return False

    def get_default_uom_price(self):
        uom = self.env.ref('uom.product_uom_ton')
        if uom:
            return uom.id
        else:
            return False

    sale_contract_id = fields.Many2one('sale.contract.india', string='Sale Contract India')
    product_id = fields.Many2one('product.product', string='Item group')
    item_group_id = fields.Many2one('product.group', string='Item Group')
    units = fields.Float(string='Unit', compute='_compute_unit', store=True)
    packing_id = fields.Many2one('ned.packing', string='Packing Nature')
    quantity = fields.Float(string='Quantity')
    uom_id = fields.Many2one('uom.uom', string='UOM', default=get_default_uom)
    price_unit = fields.Float(string='Price')
    currency_id = fields.Many2one('res.currency', string='Currency')
    price_uom = fields.Many2one('uom.uom', string='UOM', default=get_default_uom_price)

    @api.depends('packing_id', 'quantity', 'packing_id.capacity')
    def _compute_unit(self):
        for record in self:
            if record.packing_id:
                record.units = record.quantity / record.packing_id.capacity
            else:
                record.units = 0
