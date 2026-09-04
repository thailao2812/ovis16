# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    pan_number = fields.Char(string='Pan Number', compute='_compute_pan_number', store=True)
    ifsc_code = fields.Char(string='IFSC Code')
    agent = fields.Boolean(string='Agent')
    shipping_customer = fields.Boolean(string='Shipping Customer')
    forwarding_agent_check = fields.Boolean(string='Forwarding Agent')
    estate_name = fields.Char(string='Estate Name')
    # accounting_type = fields.Selection([
    #     ('coffee_export', 'Coffee Export'),
    #     ('coffee_local', 'Coffee Local'),
    #     ('expense', 'Expense')
    # ], string='Accounting Type', required=False)
    farm_id = fields.Text(string='Farm ID')
    with_declaration = fields.Boolean(string='With Declaration', compute='_compute_with_declaration', store=True)
    pan_number_line_ids = fields.One2many('pan.number.line', 'partner_id', string='Pan Number Line')
    declaration_line_ids = fields.One2many('declaration.line', 'partner_id', string='Declaration Line')

    @api.depends('pan_number_line_ids', 'pan_number_line_ids.pan_number')
    def _compute_pan_number(self):
        for rec in self:
            pan_number = False
            if rec.pan_number_line_ids.filtered(lambda x: x.pan_number):
                pan_number = rec.pan_number_line_ids.filtered(lambda x: x.pan_number)[0].pan_number
            rec.pan_number = pan_number

    @api.depends('declaration_line_ids', 'declaration_line_ids.with_declaration')
    def _compute_with_declaration(self):
        for rec in self:
            with_declaration = False
            if rec.declaration_line_ids.filtered(lambda x: x.with_declaration):
                with_declaration = rec.declaration_line_ids.filtered(lambda x: x.with_declaration)[0].with_declaration
            rec.with_declaration = with_declaration

    # @api.model
    # def create(self, vals):
    #     if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
    #         raise UserError(_("You don't have permission Create Contact to do that"))
    #     return super(ResPartner, self).create(vals)
    #
    # def write(self, vals):
    #     if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
    #         raise UserError(_("You don't have permission Write Contact to do that"))
    #     return super(ResPartner, self).write(vals)
    #
    # def unlink(self):
    #     if not self.env.user.user_has_groups('sd_india_master.group_admin_india'):
    #         raise UserError(_("You don't have permission Delete Contact to do that"))
    #     return super(ResPartner, self).unlink()


class PanNumberLine(models.Model):
    _name = 'pan.number.line'

    partner_id = fields.Many2one('res.partner', string='Partner')
    pan_number = fields.Char(string='Pan Number')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')

class DeclarationLine(models.Model):
    _name = 'declaration.line'

    partner_id = fields.Many2one('res.partner', string='Partner')
    with_declaration = fields.Boolean(string='With Declaration')
    date_from = fields.Date(string='From')
    date_to = fields.Date(string='To')
