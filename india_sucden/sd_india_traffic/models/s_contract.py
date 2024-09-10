# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError


class SContract(models.Model):
    _inherit = 's.contract'

    total_allocated_sc = fields.Float(string='Total Allocated SC', compute='_compute_total_allocated', store=True)
    open_qty = fields.Float(string='Open Qty', compute='_compute_total_allocated', store=True)
    psc_to_sc_ids = fields.One2many('psc.to.sc.linked', 's_contract')
    arbitration = fields.Selection([
        ('london', 'If any in London'),
        ('newyork', 'If any in New York')
    ], string='Arbitration', default=None)
    truck_no = fields.Float(string='No of Trucks (Lots)')

    incoterm_id = fields.Many2one('account.incoterms', string='Inco Terms')
    differential = fields.Float(string="Additional Cost", related='contract_line.differential', store=True)
    exchange_product = fields.Many2one('exchange.india', string='Exchange')

    special_condition = fields.Text(string='Special Condition',
                                    default='THE UNIFORM LAW ON THE INTERNATIONAL SALE OF GOODS '
                                            'SHALL NOT APPLY TO THIS CONTRACT.')
    general_condition = fields.Text(string='General Condition', default='ACCORDING TO CONDITIONS OF ECC.')
    fixation_by = fields.Selection([
        ('buyer', "Buyer's Call"),
        ('seller', "Seller's Call")
    ], string='Fixation By', default=None)

    premium_cert = fields.Float(string='Certificate Premium', related='contract_line.premium_cert', store=True)
    packing_cost = fields.Float(string='Packing Cost', related='contract_line.packing_cost', store=True)
    total_qty = fields.Float(compute='_total_qty', digits=(16, 2), string='Total Qty', store=True)
    no_of_pack = fields.Float(string='No. of bag', related='contract_line.number_of_bags', store=True)
    packing_id_s_contract = fields.Many2one('ned.packing', string='Packing', related='contract_line.packing_id', store=True)

    qty_allocated_si = fields.Float(string='Allocated SI Qty (Kgs)', compute='_compute_allocated_qty_india', store=True)
    bag_allocated_si = fields.Float(string='Allocated SI Bag (Nos)',digits=(16, 0), compute='_compute_allocated_qty_india', store=True)
    qty_tobe_allocated_si = fields.Float(string='To Be Allocated SI Qty (Kgs)', compute='_compute_allocated_qty_india', store=True)
    bag_tobe_allocated_si = fields.Float(string='To Be Allocated SI Bag (Nos)', digits=(16, 0), compute='_compute_allocated_qty_india', store=True)

    qty_allocated_so = fields.Float(string='Allocated SO Qty (Kgs)', compute='_compute_allocated_qty_india', store=True)
    bag_allocated_so = fields.Float(string='Allocated SO Bag (Nos)', digits=(16, 0), compute='_compute_allocated_qty_india', store=True)
    qty_tobe_allocated_so = fields.Float(string='To Be Allocated SO Qty (Kgs)', compute='_compute_allocated_qty_india', store=True)
    bag_tobe_allocated_so = fields.Float(string='To Be Allocated SO Bag (Nos)', digits=(16, 0), compute='_compute_allocated_qty_india', store=True)

    weights = fields.Selection([('DW', 'Delivered Weights'), ('NLW', 'Net Landed Weights'),
                                ('NSW', 'Net Shipped Weights'), ('RW', 'Re Weights'), ('net_shipping', 'Net Shipping Weight with 0.50% franchise')],
                               string='Weigh Condition', readonly=True, states={'draft': [('readonly', False)]},
                               index=True)

    pss_type = fields.Selection(
        [('SAS', 'SAS'), ('SAN', 'SAN'), ('SAP', 'SAP'), ('PSS', 'PSS'), ('PSS+OTS', 'PSS+OTS'), ('No', 'Non PSS')],
        string=" Pss type", copy=True)

    @api.depends('contract_line', 'contract_line.product_qty')
    def _total_qty(self):
        for order in self:
            total_qty = 0
            for line in order.contract_line:
                total_qty += line.product_qty
            order.total_qty = total_qty

    @api.depends('shipping_ids', 'shipping_ids.total_line_qty', 'shipping_ids.no_of_bag',
                 'contract_ids.total_qty', 'contract_ids', 'contract_ids.no_of_bags', 'total_qty', 'no_of_pack')
    def _compute_allocated_qty_india(self):
        for record in self:
            qty_allocated_si = record.qty_allocated_si = sum(record.shipping_ids.mapped('total_line_qty'))
            bag_allocated_si = record.bag_allocated_si = sum(record.shipping_ids.mapped('no_of_bag'))
            record.qty_tobe_allocated_si = record.total_qty - qty_allocated_si
            record.bag_tobe_allocated_si = record.no_of_pack - bag_allocated_si

            qty_allocated_so = record.qty_allocated_so = sum(record.contract_ids.mapped('total_qty'))
            bag_allocated_so = record.bag_allocated_so = sum(record.contract_ids.mapped('no_of_bags'))
            record.qty_tobe_allocated_so = record.total_qty - qty_allocated_so
            record.bag_tobe_allocated_so = record.no_of_pack - bag_allocated_so


    @api.depends('psc_to_sc_ids', 'psc_to_sc_ids.state_allocate', 'psc_to_sc_ids.current_allocated', 'total_qty')
    def _compute_total_allocated(self):
        for record in self:
            record.total_allocated_sc = sum(i.current_allocated for i in record.psc_to_sc_ids.filtered(
                lambda x: x.state_allocate == 'submit'))
            # print(record.total_qty, record.total_allocated_sc)
            record.open_qty = record.total_qty - record.total_allocated_sc


class ScontractLine(models.Model):
    _inherit = 's.contract.line'

    no_of_teus = fields.Float(string='No. of Container')
    premium_cert = fields.Float(string='Certificate Premium')
    packing_cost = fields.Float(string='Packing Cost')
    differential = fields.Float(string="Additional Cost")

    @api.onchange('packing_id', 'product_qty', 'type')
    def onchange_packing_id(self):
        if self.packing_id:
            if self.packing_id.capacity > 0:
                self.number_of_bags = round(self.product_qty / self.packing_id.capacity, 0)
            else:
                self.number_of_bags = 0
            if self.type == 'export':
                self.packing_cost = self.packing_id.Premium
            else:
                self.packing_cost = 0

    @api.onchange('product_id')
    def onchange_for_tax(self):
        if self.product_id:
            if self.product_id.taxes_id:
                self.tax_id = [(6,0,self.product_id.taxes_id.ids)]

    @api.onchange('certificate_id', 'product_id')
    def onchange_certificate_id(self):
        if self.certificate_id:
            line_premium = self.certificate_id.sale_premium_line.filtered(lambda x: x.item_group_id.id == self.product_id.item_group_id.id)
            if line_premium:
                self.premium_cert = line_premium.sale_premium
            else:
                self.premium_cert = 0
        else:
            self.premium_cert = 0
