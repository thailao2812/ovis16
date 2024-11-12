# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ShippingInstruction(models.Model):
    _inherit = 'shipping.instruction'

    process_state = fields.Selection([
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('completed', 'Completed')
    ], string="Progress State", default=None)

    invoice_qty = fields.Float(string="Invoice Qty", compute='_compute_invoice_qty', store=True)
    delivery_order_ids = fields.One2many('delivery.order', 'shipping_id', string="Delivery Orders", readonly=True)
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse', required=True, readonly=True,
                                   states={'draft': [('readonly', False)]}, default=False, compute='_compute_warehouse_id', store=True)

    @api.depends('delivery_order_ids', 'delivery_order_ids.from_warehouse_id', 'delivery_order_ids.state')
    def _compute_warehouse_id(self):
        for rec in self:
            if rec.delivery_order_ids:
                rec.warehouse_id = rec.delivery_order_ids[0].from_warehouse_id.id if rec.delivery_order_ids[0].from_warehouse_id else False


    @api.depends('contract_ids', 'contract_ids.invoiced_qty', 'contract_ids.state')
    def _compute_invoice_qty(self):
        for rec in self:
            rec.invoice_qty = sum(rec.contract_ids.mapped('invoiced_qty'))

    @api.model
    def create(self, vals):
        if not self.user_has_groups('sd_contract_vietnam.group_full_right_shipping_instruction'):
            raise UserError(_("You don't have permission to do that"))
        return super(ShippingInstruction, self).create(vals)

    def write(self, vals):
        if not self.user_has_groups('sd_contract_vietnam.group_full_right_shipping_instruction'):
            raise UserError(_("You don't have permission to do that"))
        return super(ShippingInstruction, self).write(vals)
