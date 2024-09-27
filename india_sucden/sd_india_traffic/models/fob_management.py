# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class FOBManagement(models.Model):
    _name = 'fob.management.india'
    _inherit = ['mail.thread']
    _description = 'FOB Management'

    name = fields.Char(string='FOB Number')
    fob_date = fields.Date(string='FOB Date', tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency')
    exchange = fields.Many2one('exchange.india', string='Exchange', tracking=True)
    forex_rate_inr = fields.Float(string='Forex Rate INR')
    market_price = fields.Float(string='Market Price')
    total_cost = fields.Float(string='Total Cost')
    yield_loss = fields.Float(string='Yield Loss')
    farm_gate_price_1st = fields.Float(string='Farm Gate Price (INR/MT)', compute='compute_farm_gate_price', store=True)
    farm_gate_price_2nd = fields.Float(string='Farm Gate Price (INR/Kg)', compute='compute_farm_gate_price', store=True)
    price = fields.Float(string='Farm Gate Price (INR/50Kg)', compute='compute_farm_gate_price', store=True)
    fob = fields.Float(string='FOB')
    fob_usd = fields.Float(string='FOB (USD/MT)', compute='_compute_fob_usd', store=True)
    crop_id = fields.Many2one('ned.crop', string='Season', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submit', 'Submit'),
        ('approve', 'Approve'),
        ('close', 'Close')
    ], string='State', default='draft', tracking=True)
    market_id = fields.Many2one('market.india', string='Market', compute='_compute_market', store=True)
    market_month = fields.Many2one('s.period', string='Market Month')

    def close_fob(self):
        for record in self:
            record.state = 'close'

    @api.depends('exchange')
    def _compute_market(self):
        for record in self:
            if record.exchange and record.exchange.market_id:
                record.market_id = record.exchange.market_id.id
            else:
                record.market_id = False

    @api.depends('exchange', 'fob', 'exchange.market_id')
    def _compute_fob_usd(self):
        for record in self:
            if record.exchange:
                record.fob_usd = record.fob * record.exchange.market_id.rate

    @api.onchange('exchange')
    def onchange_exchange(self):
        if self.exchange:
            self.currency_id = self.exchange.currency_id.id
            self.yield_loss = self.exchange.yield_loss

    def button_submit(self):
        for record in self:
            if not record.name:
                if record.crop_id:
                    record.name = self.env['ir.sequence'].next_by_code('fob.management.india') + '/' + record.crop_id.short_name
            record.state = 'submit'
    def button_approve(self):
        for record in self:
            record.state = 'approve'

    def button_set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.onchange('crop_id')
    def onchange_crop_id(self):
        if self.crop_id:
            self.total_cost = self.crop_id.fixed_cost

    @api.depends('forex_rate_inr', 'fob', 'total_cost', 'yield_loss')
    def compute_farm_gate_price(self):
        for record in self:
            record.farm_gate_price_1st = ((record.forex_rate_inr * record.fob_usd) - record.total_cost) * ((100-record.yield_loss) / 100)
            record.farm_gate_price_2nd = record.farm_gate_price_1st / 1000
            record.price = (record.farm_gate_price_1st / 1000) * 50

