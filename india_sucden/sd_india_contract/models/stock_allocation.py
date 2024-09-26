# -*- coding: utf-8 -*-
from string import digits

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class StockAllocation(models.Model):
    _inherit = "stock.allocation"

    qty_allocation_net = fields.Float(string='Qty Allocation (Gross Qty)', digits=(12, 0))
    qty_received_net = fields.Float(compute='_compute_qty_net', string='Allocated (Gross Qty)', store=True, digits=(12, 0))
    qty_unreceived_net = fields.Float(compute='_compute_qty_net', string='UnAllocated (Gross Qty)', digits=(12, 0), store=True)

    # New Field
    purchase_date = fields.Date(string='Purchase Date', compute='compute_data', store=True)
    consignment_id = fields.Many2one('purchase.contract', string='CS No', compute='compute_data', store=True)
    consignment_date = fields.Date(string='CS Date', compute='compute_data', store=True)
    partner_code = fields.Char(string='Vendor Code', related='partner_id.partner_code', store=True)
    estate_name = fields.Char(string='Estate Name', related='partner_id.estate_name', store=True)
    product_code = fields.Char(string='Item Code', related='product_id.default_code', store=True)
    certificate_id = fields.Many2one('ned.certificate', string='Certificate', related='contract_id.certificate_id', store=True)
    crop_id = fields.Many2one('ned.crop', related='contract_id.crop_id', string='Crop Season', store=True)
    bag_no = fields.Float(string='No of Bags', digits=(12, 0), compute='compute_data', store=True)
    gross_qty = fields.Float(string='Gross Qty', digits=(12,0), compute='compute_data', store=True)
    quality_deduction = fields.Float(string='Quality Deduction', compute='compute_data', store=True)
    net_qty = fields.Float(string='Net Qty', compute='compute_data', store=True)
    net_price = fields.Float(string='Net Price/kg', compute='compute_data', store=True)
    premium = fields.Float(string='Premium', related='contract_id.premium', store=True)
    gross_price = fields.Float(string='Gross Price/kg', compute='compute_data', store=True)
    gross_value = fields.Float(string='Gross Value', compute='compute_data', store=True)
    deduction_value = fields.Float(string='Deduction Value', compute='compute_data', store=True)
    net_value = fields.Float(string='Net Value', compute='compute_data', store=True)
    inv_no_date = fields.Char(string='Invoice no/Date')

    @api.depends('product_id', 'contract_id', 'picking_id', 'state', 'contract_id.pending_allocation_qty',
                 'picking_id.total_bag', 'picking_id.total_init_qty', 'picking_id.date_done', 'picking_id.deduction_qty',
                 'contract_id.relation_price_unit', 'contract_id.premium', 'contract_id.type', 'contract_id.npe_ids',
                 'contract_id.nvp_ids')
    def compute_data(self):
        for rec in self:
            if rec.picking_id:
                rec.quality_deduction = rec.picking_id.deduction_qty
            else:
                rec.quality_deduction = 0
            rec.net_price = rec.contract_id.relation_price_unit if rec.contract_id.type == 'purchase' else 0
            rec.premium = rec.contract_id.premium
            if rec.contract_id and rec.contract_id.type == 'purchase' and rec.picking_id:
                rec.purchase_date = rec.picking_id.date_done
                rec.bag_no = rec.picking_id.total_bag
                rec.gross_qty = rec.picking_id.total_init_qty
            elif rec.contract_id and rec.contract_id.type == 'consign':
                rec.purchase_date = rec.contract_id.npe_ids and rec.contract_id.npe_ids[0].date_fixed or False
                rec.bag_no = rec.contract_id.npe_ids and rec.contract_id.npe_ids[0].contract_id.number_of_bags or False
                rec.gross_qty = rec.contract_id.npe_ids and rec.contract_id.npe_ids[0].product_qty + rec.contract_id.pending_allocation_qty or False
            else:
                rec.purchase_date = False
                rec.bag_no = 0
                rec.gross_qty = 0

            if rec.contract_id and rec.contract_id.type == 'purchase' and rec.contract_id.origin:
                rec.consignment_id = rec.contract_id.nvp_ids[0].npe_contract_id and rec.contract_id.nvp_ids[0].npe_contract_id.id or False
                rec.consignment_date = rec.contract_id.nvp_ids[0].npe_contract_id and rec.contract_id.nvp_ids[0].npe_contract_id.date_contract or False
            else:
                rec.consignment_id = False
                rec.consignment_date = False

            rec.net_qty = rec.gross_qty - rec.quality_deduction
            rec.gross_price = rec.net_price + rec.premium
            rec.gross_value = rec.gross_qty * rec.gross_price
            rec.deduction_value = rec.quality_deduction * rec.gross_price
            rec.net_value = rec.net_qty * rec.gross_price

    @api.depends('contract_id', 'picking_id', 'qty_allocation_net', 'state')
    def _compute_qty_net(self):
        for order in self:
            allocation_qty = 0.0
            if order.picking_id and order.contract_id:

                allocation_obj = self.env['stock.allocation'].search([('picking_id', '=', order.picking_id.id)])
                allocation_qty = sum(allocation_obj.mapped('qty_allocation_net'))
                order.qty_received_net = allocation_qty or 0.0

                move_line = order.picking_id.move_line_ids_without_package.filtered(
                    lambda r: r.picking_id.state == 'done')
                qty_grn = sum(move_line.mapped('init_qty'))
                order.qty_unreceived_net = qty_grn - allocation_qty


            else:
                order.qty_received_net = 0
                order.qty_unreceived_net = 0

            if order.qty_unreceived_net < 0:
                raise UserError(_('unReceived Net must larger than 0'))

    def approve_allocation(self):
        for allocation in self:
            if allocation.contract_id.type == 'purchase' and allocation.contract_id.origin:
                raise UserError(_("You don't need to allocate into this contract, because it converted from CS already!!!"))
            if allocation.qty_allocation_net == 0:
                raise UserError(_("Please input Qty Allocation (Net Qty) before approve this Allocation!!!"))
            allocation.state = 'approved'
            allocation.contract_id.qty_received = allocation.contract_id.qty_received + allocation.qty_allocation
            allocation._compute_qty_net()
            allocation._compute_qty()
        return True
