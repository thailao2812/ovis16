# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class PscToScLinked(models.Model):
    _name = 'psc.to.sc.linked'

    sale_contract_id = fields.Many2one('sale.contract.india')
    s_contract = fields.Many2one('s.contract', string='SC No')
    sc_date = fields.Date(string='SC Date')
    partner_id = fields.Many2one('res.partner', string='Customer')
    product_id = fields.Many2one('product.product', string='Item name - Item code')
    sc_qty = fields.Float(string='SC Qty')
    balance_qty = fields.Float(string='Balance Qty')
    value = fields.Float(string='Value (USD/MT)', related='sale_contract_id.price_unit', store=True)
    current_allocated = fields.Float(string='Current Allocation')
    state = fields.Selection(related='sale_contract_id.state', string='State')
    state_allocate = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit')
    ], string='State', default='draft')

    @api.onchange('s_contract')
    def onchange_s_contract(self):
        if self.s_contract:
            self.sc_date = self.s_contract.date
            self.partner_id = self.s_contract.partner_id.id
            self.product_id = self.s_contract.product_id.id
            self.sc_qty = self.s_contract.total_qty
            self.balance_qty = self.s_contract.open_qty

    @api.constrains('current_allocated')
    def _constrains_current_allocated(self):
        for obj in self:
            if obj.current_allocated > obj.balance_qty:
                raise UserError(
                    _("Allocation cannot higher than balance quantity for %s") % obj.s_contract.name)

    def button_submit(self):
        for rec in self:
            rec.s_contract._compute_total_allocated()
            rec.state_allocate = 'submit'

    def button_draft(self):
        for rec in self:
            rec.s_contract._compute_total_allocated()
            rec.state_allocate = 'draft'

