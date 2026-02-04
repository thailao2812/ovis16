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
    is_return = fields.Boolean(string='Is Return', store=True, compute='_compute_is_return')
    state_return = fields.Selection([
        ('draft', 'Draft'),
        ('approve_inventory', 'Approved Inventory'),
        ('approve_director', 'Approved Director'),
        ('reject', 'Rejected'),
    ], string='State Return', default='draft', tracking=True, copy=False)

    @api.depends('picking_type_id', 'state')
    def _compute_is_return(self):
        for rec in self:
            rec.is_return = False
            picking_type_id = rec.picking_type_id
            if picking_type_id and picking_type_id.code == 'return_supplier':
                rec.is_return = True


    def approve_by_inventory(self):
        self.write({'state_return': 'approve_inventory'})


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
            if record.is_return:
                record.state_return = 'approve_director'
        return super(StockPicking, self).button_sd_validate()

    def print_receipt_report(self):
        return self.env.ref('sd_india_inventory.grn_receipt_report').report_action(self)

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        if name:
            args += [('name', operator, name)]
        picking = self.with_context(from_name_search=True).search(args, limit=limit)
        return picking.name_get()


    def action_cancel(self):
        res = super().action_cancel()
        for rec in self:
            if rec.is_return:
                rec.state_return = 'reject'
        return res