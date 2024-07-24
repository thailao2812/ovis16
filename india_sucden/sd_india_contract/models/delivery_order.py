# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class DeliveryOrder(models.Model):
    _inherit = "delivery.order"

    transrate = fields.Float(string='Trans. Rate (INR)', digits=(12, 2), states={},readonly=False)
    gtr_picking_id = fields.Many2one('stock.picking', 'GTR No')

    packing_place = fields.Selection(selection='_get_new_packing_type', string='Stuffing place')
    from_warehouse_id = fields.Many2one('stock.warehouse', string="From Warehouse", default=False, required=True)

    @api.model
    def _get_new_packing_type(self):
        return [('kushalnagar', 'Kushalnagar'), ('mangalore', 'Managalore')]

    @api.depends('picking_id', 'picking_id.state', 'packing_place', 'post_shippemnt_ids.post_line',
                 'post_shippemnt_ids', 'post_shippemnt_ids.post_line.bags',
                 'post_shippemnt_ids.post_line.shipped_weight', 'contract_id', 'contract_id.type', 'gtr_picking_id',
                 'gtr_picking_id.state')
    def _factory_qty(self):
        for order in self:
            if order.type == 'Transfer':
                weight_out = weight_in = bags_out = bags_in = 0
                pick_id = self.env['stock.picking'].sudo().search([('delivery_id', '=', order.id)])
                for pick in pick_id:
                    if pick.state == 'done':
                        # print pick.state, pick.picking_type_code
                        # Duyệt stock_picking rows lấy các dòng transfer local
                        if pick.picking_type_id.code == 'transfer_out' or pick.picking_type_code == 'outgoing':  # 152:
                            for line in pick.move_line_ids_without_package:
                                if line.weighbridge == 0:
                                    weight_out += line.init_qty
                                else:
                                    weight_out += line.weighbridge
                                bags_out += line.bag_no or 0.0
                        if pick.picking_type_id.code == 'transfer_in' or pick.picking_type_code == 'incoming':  # 104:
                            for line in pick.move_line_ids_without_package:
                                if line.weighbridge == 0:
                                    weight_in += line.init_qty
                                else:
                                    weight_in += line.weighbridge
                                bags_in += line.bag_no or 0.0
                #         print weight_out, weight_in
                #     print pick.id
                # print weight_out, weight_in, 'STOP', order.id
                order.weightfactory = weight_out
                order.bagsfactory = bags_out
                order.shipped_weight = weight_in
                order.bags = bags_in
                order.storing_loss = order.total_qty - order.weightfactory
                order.transportation_loss = order.weightfactory - order.shipped_weight

                # # Duyệt stock_picking rows lấy các dòng transfer MBN
                # if pick.picking_type_id['code'] == 183:
                #     for line in pick.move_lines:
                #         weight_out += line.weighbridge or 0.0
                #         bags_out += line.bag_no or 0.0
                # if pick.picking_type_id['code'] == 174:
                #     for line in pick.move_lines:
                #         weight_in += line.init_qty or 0.0
                #         bags_in += line.bag_no or 0.0

            if order.type == 'Sale':
                weight = bagsfactory = 0
                for pick in order.picking_id:
                    if pick.state == 'done':
                        for line in pick.move_line_ids_without_package:
                            bagsfactory += line.bag_no or 0.0
                            weight += line.init_qty or 0.0

                shipped_weight = bags = 0
                for post in order.post_shippemnt_ids:
                    for line in post.post_line:
                        bags += line.bags
                        shipped_weight += line.shipped_weight

                if order.packing_place == 'factory':
                    order.bagsfactory = bagsfactory
                    order.weightfactory = weight
                    order.bags = bagsfactory
                    order.shipped_weight = weight
                    order.storing_loss = order.total_qty - weight
                    order.transportation_loss = 0
                else:
                    order.bags = bags
                    order.shipped_weight = shipped_weight

                    order.bagsfactory = bagsfactory
                    order.weightfactory = weight
                    order.storing_loss = order.total_qty - weight
                    order.transportation_loss = weight - shipped_weight

                if order.contract_id and order.contract_id.type == 'export':
                    if order.picking_id and ('KTN' in order.picking_id.name or 'CWT' in order.picking_id.name):
                        order.shipped_weight = weight
                        order.transportation_loss = 0

    def button_load_do(self):
        res = super(DeliveryOrder, self).button_load_do()
        for rec in self:
            if rec.shipping_id:
                rec.packing_place = rec.shipping_id.packing_place
        return res

    def button_cancel(self):
        for record in self:
            record.state = 'cancel'

    def printout_deilvery_order(self):
        return self.env.ref('sd_india_contract.report_delivery_order_india').report_action(self)

    def printout_transfer_order(self):
        return self.env.ref('sd_india_contract.stock_transfer_invoice').report_action(self)

    def _get_printed_report_name(self):
        return self.name

    def button_approve(self):
        for rec in self:
            if not rec.delivery_order_ids:
                raise UserError(_("You cannot approve when DO don't have any line product"))
            if sum(rec.delivery_order_ids.mapped('product_qty')) <= 0:
                raise UserError(_("You cannot approve when DO don't have any KGs"))
        return super(DeliveryOrder, self).button_approve()