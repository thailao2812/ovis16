# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from datetime import datetime
    
    
class FOBManagement(models.Model):
    _name ="fob.management"
    _order = "id desc"

    lot_date = fields.Date(string="Date")
    name = fields.Char(string="Lot no")
    lot_sucden = fields.Char('Lot Sucden', size=256)
    scontract_id = fields.Many2one('s.contract', 'S Contract')
    pcontract_id = fields.Many2one('s.contract', 'P Contract')
    shipper_id = fields.Many2one('res.partner', 'Shipper')
    stuff_place = fields.Char(string='Stuffing Place')
    dest_id = fields.Many2one('stock.location', string='Destination')
    net_qty =  fields.Float(string='Net Weight')
    mc = fields.Float(string="MC")
    fm = fields.Float(string="FM")
    black = fields.Float(string="Black")
    broken = fields.Float(string="Broken")
    brown = fields.Float(string="Brown")
    mold = fields.Float(string="Mold")
    screen20 = fields.Float(string="Screen20",  digits=(12, 2))
    screen19 = fields.Float(string="Screen19",  digits=(12, 2))
    screen17 = fields.Float(string="Screen17",  digits=(12, 2))
    screen18 = fields.Float(string="Screen18",  digits=(12, 2))
    screen16 = fields.Float(string="Screen16",  digits=(12, 2))
    screen15 = fields.Float(string="Screen15",  digits=(12, 2))
    screen14 = fields.Float(string="Screen14",  digits=(12, 2))
    screen13 = fields.Float(string="Screen13",  digits=(12, 2))
    screen12 = fields.Float(string="Screen12",  digits=(12, 2))
    bscreen12 = fields.Float(string="Below Screen12",  digits=(12, 2))
    burn = fields.Float(string="Burn",  digits=(12, 2)) 
    excelsa = fields.Float(string="Excelsa",  digits=(12, 2)) 
    insect = fields.Float(string="Insect",  digits=(12, 2)) 
    defects = fields.Float(string="Defects",  digits=(12, 2))
    bulk_density = fields.Char(string='Bulk Density', size=256)
    cup_taste = fields.Char(string="Cuptaste")
    inspect_sampler = fields.Char('Inspected by/Sampler', size=256)
    sup_suc = fields.Char(string="Supervisor of Sucden", size = 256)
    remark = fields.Char('Remark', size=256)
    x_quality_claim = fields.Char('Quality Claim', size=128)
    x_reoclaim = fields.Char('Reason of Claim', size=256)
    x_claim_date = fields.Date('Date of Claim')
    #err
    x_traffic_contract_id = fields.Many2one('traffic.contract', 'S Contract')
    shiping_line = fields.Char('Shiping Line', size=256)
    x_p_contract_name = fields.Char('P Contract', size=256)
    x_p_contract_ids = fields.Many2many('s.contract', 'x_fob_management_s_contract_rel', 'fob_management_id', 's_contract_id', 'P Contract')
    customer_id = fields.Many2one('res.partner', 'Customer')
    product_id = fields.Many2one('product.product', string='Product')
    packing_id = fields.Many2one('ned.packing', string='Packing')
    qty_scontract = fields.Float(string='Qty Scontract')
    contract_no = fields.Char(string="Container No.", size=256)
    x_fumi = fields.Char('Fumigation', size=256)
    state = fields.Selection([('draft','Draft'), ('approve', 'Approved')], string='Status', default='draft')

    p_on_hand = fields.Float(string='P On Hand')
    stack_on_hand = fields.Char(string='Real Stack Export')
    real_qty_scontract = fields.Float(string='Real Qty Scontract', compute='compute_real_qty_scontract')
    real_container = fields.Float(string='Real Container')
    weight_claim = fields.Float(string='Weight Claim')
    x_stuff_place_id = fields.Many2one('x_external.warehouse', string='Stuffing Place')

    file = fields.Binary(string='File')
    file_name = fields.Char(string='File Name')
    port_of_destination = fields.Many2one('delivery.place', string='POD', related='x_traffic_contract_id.port_of_discharge',
                                          store=True)


    def compute_real_qty_scontract(self):
        for record in self:
            record.real_qty_scontract = 0
            s_contract = self.env['s.contract'].search([
                ('name', 'ilike', record.x_traffic_contract_id.name)
            ])
            if s_contract:
                sp_allocaton = self.env['sale.contract'].search([
                    ('scontract_id', '=', s_contract[0].id),
                    ('shipping_id', '!=', False),
                    ('type', '=', 'export'),
                    ('x_is_bonded', '=', True)
                ])
                if sp_allocaton:
                    total = sum(i.allocated_qty for i in sp_allocaton.detail_ids)
                    record.real_qty_scontract = total

    @api.onchange('x_traffic_contract_id')
    def onchange_scontract_id(self):
        for rc in self:
            if rc.x_traffic_contract_id:
                ctr_id = rc.x_traffic_contract_id
                rc.shiping_line = ctr_id.shipping_line_id and ctr_id.shipping_line_id.name or 0
                rc.x_p_contract_name = ctr_id.x_p_contract_link or ''
                rc.customer_id = ctr_id.partner_id  and ctr_id.partner_id.id or 0
                rc.product_id = ctr_id.standard_id and ctr_id.standard_id.id or 0
                rc.packing_id = ctr_id.packing_id and ctr_id.packing_id.id or 0
                rc.qty_scontract = ctr_id.p_qty and ctr_id.p_qty or 0
                del ctr_id
                
                
    def btt_confirm(self):
        return self.write({'state': 'approve'})

    def btt_draft(self):
        return self.write({'state': 'draft'})
    
