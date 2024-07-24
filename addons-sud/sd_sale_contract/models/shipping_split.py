# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
    
class ShippingSplit(models.Model):
    _name = 'shipping.split'

    name = fields.Char('Entity Number', size=256)
    shipment_id = fields.Many2one('shipping.instruction', string='Shipping Instruction')
    scontract_id = fields.Many2one('s.contract', string='S Contract')
    qty_contract = fields.Float('Quantity')
    res_qty = fields.Float('Remaining Qty')
    new_qty = fields.Float('Qty New')
    uom = fields.Many2one('product.uom', 'UOM')
    
    def split_scontract(self):
        new_record = 0
        for record in self:
            return {
                'name': 'Split Shipment',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'shipping.split',
                'type': 'ir.actions.act_window',
                'target': 'new',
                'context': {'default_scontract_id': record.id},
            }

    @api.onchange('shipment_id', 'new_qty', 'scontract_id')
    def onchange_si(self):
        for record in self:
            if record.shipment_id:
                record.name = record.shipment_id.name
                record.qty_contract = sum([line.product_qty for line in record.shipment_id.shipping_ids])
            if record.scontract_id:
                record.name = record.scontract_id.name
                record.qty_contract = sum([line.product_qty for line in record.scontract_id.contract_line])
            if record.new_qty:
                record.res_qty = record.qty_contract - record.new_qty

    def split_shipment(self):
        new_record = 0
        for rc in self:
            if rc.shipment_id:
                record = rc.shipment_id
                rc_name = rc.shipment_id.name
                new_record = record.copy({
                    'contract_id': record.contract_id.id, 
                    'name': '%s - %s' % (record.name, str(len(self.search([('name', 'ilike', record.name)])) + 1)),
                    'port_of_loading': record.port_of_loading and record.port_of_loading.id,
                    'port_of_discharge': record.port_of_discharge and record.port_of_discharge.id or 0,
                    'date': record.date and record.date or '',
                    'request_qty': rc.new_qty,
                    'no_of_pack': round((rc.new_qty / 60),0),
                })
                record.write({
                    'name': '%s - %s' % (record.name, len(self.search([('name', 'ilike', record.name)]))),
                    'request_qty': rc.res_qty,
                    'no_of_pack': round((rc.res_qty / 60),0),
                })
                for prod in record.shipping_ids:
                    prod.copy({
                        'shipping_id': new_record.id,
                        'product_qty': rc.new_qty,
                    })
                    prod.write({
                        'product_qty': rc.res_qty,
                    })
                return {
                    'name': 'Shipment',
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'domain': [('name', 'ilike', rc_name)],
                    'res_model': 'shipping.instruction',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': new_record.id,
                }
            if rc.scontract_id:
                record = rc.scontract_id
                rc_name = rc.scontract_id.name
                new_record = record.copy({
                    'name': '%s - %s' % (record.name, str(len(self.search([('name', 'ilike', record.name)])) + 1)),
                    'port_of_loading': record.port_of_loading and record.port_of_loading.id,
                    'port_of_discharge': record.port_of_discharge and record.port_of_discharge.id or 0,
                    'p_qty': rc.new_qty,
                    'no_of_pack': round((rc.new_qty / 60),0),
                })
                for prod in record.contract_line:
                    prod.copy({
                        'shipping_id': new_record.id,
                        'product_qty': rc.new_qty,
                    })
                    prod.write({
                        'product_qty': rc.res_qty,
                    })
                return {
                    'name': 'S Contract',
                    'view_type': 'form',
                    'view_mode': 'tree',
                    'domain': [('name', 'ilike', rc_name)],
                    'res_model': 's.contract',
                    'type': 'ir.actions.act_window',
                    'target': 'current',
                    'res_id': new_record.id,
                }