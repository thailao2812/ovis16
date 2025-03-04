# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class InvoicePurchaseContract(models.Model):
    _name = "invoice.purchase.contract"
    _description = "Invoice Purchase Contract"

    contract_id = fields.Many2one('purchase.contract', string='Pur. Contract No', required=True)
    invoice_number = fields.Char(string='Invoice Number', required=True)
    invoice_date = fields.Date(string='Invoice Date', required=True)
    picking_id = fields.Many2one('stock.picking', string='GRN No', required=True)
    grn_date = fields.Datetime(string='GRN Date', related='picking_id.date_done', store=True)

    @api.constrains('picking_id', 'invoice_number')
    def _constrains_picking_id(self):
        for obj in self:
            check = self.env['invoice.purchase.contract'].search([
                ('picking_id', '=', obj.picking_id.id),
                ('id', '!=', obj.id),
            ], limit=1)
            if check:
                raise models.ValidationError(
                    _('Invoice Purchase Contract already exists for GRN No: %s with Invoice number %s') %
                    (obj.picking_id.name, obj.invoice_number)
                )




