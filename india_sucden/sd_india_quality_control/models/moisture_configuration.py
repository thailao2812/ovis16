# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError


class MoistureConfiguration(models.Model):
    _name = 'moisture.configuration'
    _description = 'Quality Configuration'
    _inherit = ['mail.thread']

    name = fields.Char(string='Name', compute='compute_name', store=True)
    product_category_id = fields.Many2one('product.category', string='Grade')
    crop_id = fields.Many2one('ned.crop', string='Season')
    reject_percent = fields.Float(string='Reject Percent (Above)')
    standard = fields.Float(string='Standard Percent')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approve')
    ], string='State', default='draft')
    # moisture configuration
    line_ids = fields.One2many('moisture.configuration.line', 'moisture_id')

    # A/AB configuration
    standard_ab_percent = fields.Float(string='Minium A/AB Grade')
    deduction_percent_ab = fields.Float(string='Deduction for every % ')

    # Outturn Configuration
    using_deduction = fields.Boolean(string='Using for Outturn deduction')
    standard_outturn_percent = fields.Float(string='Standard Outturn')

    # FM configuration
    using_deduction_fm = fields.Boolean(string='Using for FM Deduction')
    use_category_id = fields.Many2one('product.category', string='Grade Use')
    standard_for_fm = fields.Float(string='Tolerance Limit')

    @api.constrains('state', 'crop_id', 'product_category_id')
    def constrains_rule(self):
        for obj in self:
            check_constraint = self.env['moisture.configuration'].search([
                ('state', '=', 'approve'),
                ('crop_id', '=', obj.crop_id.id),
                ('product_category_id', '=', obj.product_category_id.id),
                ('id', '!=', obj.id)
            ])
            if check_constraint:
                raise UserError(_('You cannot approve the same Category in the same Season, please check again!!!'))

    @api.depends('product_category_id', 'crop_id')
    def compute_name(self):
        for rec in self:
            if rec.product_category_id and rec.crop_id:
                rec.name = 'Quality Rule Configuration for %s in %s' % (rec.product_category_id.name, rec.crop_id.name)

    def set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def button_approve(self):
        for rec in self:
            checking = self.env['moisture.configuration'].search([
                ('product_category_id', '=', rec.product_category_id.id),
                ('crop_id', '=', rec.crop_id.id),
                ('state', '=', 'approve'),
                ('id', '!=', rec.id)
            ])
            if checking:
                raise UserError(_("You cannot approve the same Category in 1 season!! Please check again"))
            rec.state = 'approve'


class MoistureConfigurationLine(models.Model):
    _name = 'moisture.configuration.line'

    moisture_id = fields.Many2one('moisture.configuration')
    from_percent = fields.Float(string='From')
    to_percent = fields.Float(string='To')
    deduction_percent = fields.Float(string='Deduction %')
    reject_percent = fields.Float(string='Reject % (Above)')
