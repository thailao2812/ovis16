# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
import math
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class SaleContract(models.Model):
    _inherit = "sale.contract"

    amount_total_india = fields.Monetary(string='Total Amount (rounding)', store=True, readonly=True, compute='_amount_all', )

    def button_approve(self):
        for rec in self:
            if rec.scontract_id.state != 'approved':
                raise UserError(_("You cannot approve Sale Order, Your S Contract is not approved yet!!"))
        return super(SaleContract, self).button_approve()

    @api.constrains('currency_id')
    def constrain_currency_id(self):
        for obj in self:
            if obj.type == 'local':
                if obj.currency_id:
                    if obj.currency_id.name != 'INR':
                        raise UserError(_("You need to check currency again!! Local should be INR"))
            if obj.type == 'export':
                if obj.currency_id:
                    if obj.currency_id.name != 'USD':
                        raise UserError(_("You need to check currency again!! Export should be USD"))

    def custom_round(self, number: float) -> int:
        if number - round(number) == 0.5:
            return math.ceil(number)
        else:
            return round(number)

    @api.depends('contract_line.price_total')
    def _amount_all(self):
        for contract in self:
            amount_untaxed = amount_tax = 0.0
            for line in contract.contract_line:
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            contract.update({
                'amount_untaxed': contract.currency_id and contract.currency_id.round(amount_untaxed) or amount_untaxed,
                'amount_tax': contract.currency_id and contract.currency_id.round(amount_tax) or amount_tax,
                'amount_total': amount_untaxed + amount_tax,
                'amount_total_india': self.custom_round(amount_untaxed + amount_tax),
            })