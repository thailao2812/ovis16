# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    template_qc = fields.Selection(related='move_line_ids_without_package.product_id.template_qc', store=True)

    first_weight = fields.Float(string='1st Weight', related='move_line_ids_without_package.first_weight', store=True)
    second_weight = fields.Float(string='2nd Weight', related='move_line_ids_without_package.second_weight', store=True)
    tare_weight = fields.Float(string='Tare Weight', related='move_line_ids_without_package.tare_weight', store=True)
    partner_code = fields.Char(string='Partner Code', related='partner_id.partner_code', store=True)
    estate_name = fields.Char(string='Estate Name', related='partner_id.estate_name', store=True)
    sup_product_id = fields.Many2one('product.product', string='Sub Product', related='move_line_ids_without_package.sup_product_id', store=True)

    def print_grn_india(self):
        stock_allocation = self.env['stock.allocation'].search([
            ('picking_id', '=', self.id),
            ('state', '=', 'approved'),
            ('contract_id.type', '=', 'purchase')
        ])
        if stock_allocation:
            return self.env.ref('sd_india_inventory.grn_india_report').report_action(self)
        else:
            return True

    def print_grn_india_without_price(self):
        return self.env.ref('sd_india_inventory.grn_india_without_price_report').report_action(self)

    def print_grn_bag_in(self):
        if self.template_qc == 'bag':
            return self.env.ref('sd_india_inventory.grn_india_bag_in_report').report_action(self)
        else:
            return True

    def print_grn_bag_out(self):
        if self.template_qc == 'bag':
            return self.env.ref('sd_india_inventory.grn_india_bag_out_report').report_action(self)
        else:
            return True

    @api.onchange('warehouse_id')
    def onchange_domain_warehouse_id(self):
        res = super(StockPicking, self).onchange_domain_warehouse_id()
        if self.env.context.get('picking_grn_Goods'):
            self.picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', 'incoming')
            ], limit=1).id
        if self.env.context.get('gdn_out'):
            self.picking_type_id = self.env['stock.picking.type'].search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('code', '=', 'outgoing')
            ], limit=1).id
        return res

    def button_sd_validate(self):
        for record in self:
            if record.picking_type_id.code == 'incoming' and record.picking_type_id.operation == 'factory':
                net_qty = record.total_init_qty
                basis_qty = 0
                if record.state_kcs == 'approved':
                    for line in record.kcs_line:
                        line.product_qty = net_qty
                        line._compute_deduction()
                        basis_qty = line.basis_weight
                    for ml in record.move_line_ids_without_package:
                        ml.qty_done = basis_qty
        return super(StockPicking, self).button_sd_validate()
