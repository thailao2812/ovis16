# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta


class SContract(models.Model):
    _inherit = "s.contract"

    # sale_contract_detail_ids = fields.One2many
    init_qty = fields.Float(related='wr_line.net_qty', string='In Weight', digits=(12, 0), store=True)
    out_qty = fields.Float(related='wr_line.gdn_net', string='Out Weight', digits=(12, 0), store=True)
    remaining_qty = fields.Float(related=False, string='Balance Weight', digits=(12, 0),
                                 compute='compute_balance_weight', store=True)
    balance_bags = fields.Float(string='Balance Bags', compute='compute_balance_weight', store=True)
    loss_weight = fields.Float(string='Loss Weight', compute='compute_balance_weight', store=True)
    loss_weight_percent = fields.Float(string='Loss Weight (%)', compute='compute_balance_weight', store=True)
    certificate = fields.Char(string='Cert No.')
    cert_validity = fields.Date(string="Cert Validity")
    stock_validity = fields.Date(string='Stock Validity', compute='_compute_stock_validity', store=True)
    status_p = fields.Selection([
        ('new', 'New'),
        ('available', 'Available'),
        ('done', 'Done')
    ], string='Status', copy=False, compute='_compute_status_p_contract', store=True)
    bag_in_stock = fields.Float(string='Bag In', compute='_compute_bag_in_stock', store=True)
    bag_out_stock = fields.Float(string='Bag Out', compute='_compute_bag_in_stock', store=True)
    allocated_not_out = fields.Float(string='Allocated Weight ( Not Out )', compute='_compute_allocated_not_out',
                                     store=True)
    allocated_bag_not_out = fields.Float(string='Allocated Bags ( Not Out )', compute='_compute_allocated_not_out',
                                         store=True)
    sale_contract_detail_ids = fields.One2many('sale.contract.deatail', 'p_contract_id')

    @api.depends('sale_contract_detail_ids', 'sale_contract_detail_ids.p_contract_id')
    def compute_balance_weight(self):
        for record in self:
            init_qty = record.init_qty
            sale_contract_detail = record.sale_contract_detail_ids.filtered(
                lambda x: x.allocated_qty > 0 and x.stack_id.id == record.wr_line.id and x.sp_id != False)
            record.remaining_qty = init_qty - sum(sale_contract_detail.mapped('tobe_qty'))
            if record.wr_line:
                if record.wr_line.stack_empty:
                    record.remaining_qty = 0
            bag_in = sum(record.wr_line.mapped('move_line_ids').filtered(
                lambda x: x.picking_id.picking_type_id.code in ['incoming', 'transfer_in', 'production_in'] and x.state == 'done').mapped('bag_no'))
            bag_out = sum(record.wr_line.mapped('move_line_ids').filtered(
                lambda x: x.picking_id.picking_type_id.code in ['outgoing', 'transfer_out', 'phys_adj'] and x.state == 'done').mapped('bag_no'))
            if record.wr_line.stack_empty:
                record.balance_bags = 0
            else:
                record.balance_bags = bag_in - bag_out
            record.loss_weight = record.remaining_qty - init_qty + record.out_qty
            record.loss_weight_percent = (record.loss_weight / init_qty) * 100 if init_qty > 0 else 0

    @api.depends('wr_line', 'no_of_pack', 'bag_allocated', 'bag_in_stock')
    def _compute_status_p_contract(self):
        for record in self:
            record.status_p = 'new'
            if not record.wr_line:
                record.status_p = 'new'
            if record.wr_line:
                if record.no_of_pack > record.bag_in_stock:
                    record.status_p = 'available'
                if record.no_of_pack == record.bag_in_stock:
                    record.status_p = 'done'

    @api.depends('wr_line', 'wr_line.move_line_ids', 'wr_line.move_line_ids.state')
    def _compute_bag_in_stock(self):
        for record in self:
            record.bag_in_stock = 0
            record.bag_out_stock = 0
            if record.wr_line:
                if record.wr_line.move_line_ids.filtered(
                        lambda x: x.picking_id.picking_type_id.code in ['incoming', 'transfer_in', 'production_in']
                                  and x.state == 'done'):
                    record.bag_in_stock = sum(record.wr_line.mapped('move_line_ids').filtered(
                        lambda x: x.picking_id.picking_type_id.code in ['incoming', 'transfer_in', 'production_in']
                                  and x.state == 'done').mapped('bag_no'))
                if record.wr_line.move_line_ids.filtered(
                        lambda x: x.picking_id.picking_type_id.code in ['outgoing', 'transfer_out', 'phys_adj']
                                  and x.state == 'done'):
                    record.bag_out_stock = sum(record.wr_line.mapped('move_line_ids').filtered(
                        lambda x: x.picking_id.picking_type_id.code in ['outgoing', 'transfer_out', 'phys_adj']
                                  and x.state == 'done').mapped('bag_no'))

    @api.depends('qty_allocated', 'out_qty', 'bag_allocated', 'bag_out_stock')
    def _compute_allocated_not_out(self):
        for record in self:
            record.allocated_not_out = record.qty_allocated - record.out_qty
            record.allocated_bag_not_out = record.bag_allocated - record.bag_out_stock

    @api.depends('wr_date')
    def _compute_stock_validity(self):
        for record in self:
            if record.wr_date:
                record.stock_validity = datetime.strptime(str(record.wr_date), '%Y-%m-%d').date() + relativedelta(
                    years=2)
            else:
                record.stock_validity = False

    qty_allocated = fields.Float(string='Allocated (Kg)', compute='_compute_allocated', store=True)
    bag_allocated = fields.Float(string='Allocated Bag No.', compute='_compute_allocated', store=True)
    tb_qty_alloca = fields.Float(string='To be Allocated (Kg)', compute='_compute_allocated', store=True)
    tb_bag_alloca = fields.Float(string='To be Allocated (bag)', compute='_compute_allocated', store=True)

    @api.depends('sale_contract_detail_ids', 'wr_line', 'no_of_pack')
    def _compute_allocated(self):
        for record in self:
            sale_contract_detail = record.sale_contract_detail_ids
            stock_stack = self.env['stock.lot'].search([
                ('p_contract_id', '=', record.id)
            ])
            if sale_contract_detail:
                record.qty_allocated = sum(detail.tobe_qty for detail in sale_contract_detail)
                record.bag_allocated = sum(detail.tobe_bag for detail in sale_contract_detail)
            else:
                record.bag_allocated = 0
                record.qty_allocated = 0
            if stock_stack:
                record.tb_qty_alloca = (sum(detail.net_qty for detail in stock_stack)) - \
                                       sum(detail.tobe_qty for detail in sale_contract_detail)
                record.tb_bag_alloca = record.no_of_pack - record.bag_allocated
            else:
                record.tb_qty_alloca = 0
                record.tb_bag_alloca = 0

    @api.constrains('name')
    def _check_constraint_name(self):
        for record in self:
            if record.traffic_link_id:
                s_contract_traffic = self.search([('name', '=', record.name),
                                                  ('traffic_link_id', '=', record.traffic_link_id.id),
                                                  ('id', '!=', record.id)], limit=1)
                if s_contract_traffic:
                    raise UserError(_("S Contract (%s) of Traffic was exist.") % (record.name))
            else:
                s_contract = self.search([('name', '=', record.name),
                                            ('id', '!=', record.id),
                                          ('traffic_link_id', '=', False)], limit=1)
                if s_contract:
                    raise UserError(_("S Contract (%s) of Factory was exist.") % (record.name))

    @api.model
    def create(self, vals):
        # if vals.get('name', False):
            # name = vals.get('name', False)
            # contract_ids = self.search([('name', '=', name), ('traffic_link_id', '!=', False)])
            # if len(contract_ids) >= 1:
            #     raise UserError(_("S Contract (%s) was exist.") % (name))

        if any(f not in vals for f in ['partner_invoice_id', 'partner_shipping_id']):
            partner = self.env['res.partner'].browse(vals.get('partner_id'))
            addr = partner.address_get(['delivery', 'invoice'])
            vals['partner_invoice_id'] = vals.setdefault('partner_invoice_id', addr['invoice'])
            vals['partner_shipping_id'] = vals.setdefault('partner_shipping_id', addr['delivery'])

        new_id = super(SContract, self).create(vals)

        ############# NED Contract ###################################################
        shipment_inf = {
            'status': new_id.status and new_id.status or '',
            'name': 'SI-%s' % (new_id.name and new_id.name or ''),
            'client_ref': new_id.client_ref or '',
            'partner_id': new_id.partner_id and new_id.partner_id.id or 0,
            'standard_id': new_id.product_id and new_id.product_id.id or (
                        new_id.standard_id and new_id.standard_id.id or 0),
            'scertificate_id': new_id.certificate_id and new_id.certificate_id.id or 0,
            'incoterms_id': new_id.incoterms_id and new_id.incoterms_id.id or 0,
            'contract_id': new_id.id,
            'port_of_loading': new_id.port_of_loading and new_id.port_of_loading.id or '',
            'port_of_discharge': new_id.port_of_discharge and new_id.port_of_discharge.id or '',
            'spacking_id': new_id.packing_id and new_id.packing_id.id or 0,
            'no_of_bag': new_id.no_of_pack or 0,
            'specs': new_id.p_quality or new_id.standard_id.name,
            'request_qty': new_id.p_qty and new_id.p_qty or 0
        }
        if 'type' in vals or 'default_type' in self.env.context:
            if (vals.get('type', False) == 'p_contract' or self.env.context.get('default_type',
                                                                                False) == 'p_contract') and 'traffic' in self.env.context.keys():
                wh_code = new_id.warehouse_id and '%s-' % new_id.warehouse_id.code or ''
                shipt_month = new_id.shipt_month and '-%s' % new_id.shipt_month.name or ''
                cname = new_id.name and '-%s' % new_id.name or ''
                zone_id = self.env['stock.zone'].search([('warehouse_id', '=', vals.get('warehouse_id', 0))], limit=1)
                stack_info = {
                    'name': '%sWR%s' % (wh_code, cname),
                    'stack_type': 'stacked',
                    'date': fields.Datetime.now(),
                    'p_contract_id': new_id.id,
                    'shipper_id': new_id.partner_id and new_id.partner_id.id or 0,
                    'product_id': new_id.product_id and new_id.product_id.id or (
                                new_id.standard_id and new_id.standard_id.id or 0),
                    'zone_id': zone_id and zone_id.id or 0,
                    'company_id': self.env.user.company_id.id
                }
                self.env['stock.lot'].create(stack_info)
            elif vals.get('type', False) in ['export', 'local'] or self.env.context.get('default_type', False) in [
                'export', 'local']:
                shipment = self.env['shipping.instruction'].create(shipment_inf)

        return new_id
