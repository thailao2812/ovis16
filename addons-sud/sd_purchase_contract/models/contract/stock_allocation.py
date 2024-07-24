# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

from datetime import datetime
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%d-%m-%Y"
DAT= "%Y-%m-%d"

    
class StockAllocation(models.Model):
    _name ="stock.allocation"
    _order = 'date_picking desc' 
        
    @api.model
    def create(self, vals):
        result = super(StockAllocation, self).create(vals)
        return result
    
    @api.depends('contract_id','picking_id','qty_allocation','state')
    def _compute_qty(self):
        for order in self:
            allocation_qty = 0.0
            if order.picking_id and order.contract_id:
                
                allocation_obj = self.env['stock.allocation'].search([('picking_id','=',order.picking_id.id)])
                allocation_qty = sum(allocation_obj.mapped('qty_allocation'))
                order.qty_received = allocation_qty or 0.0
                
                move_line = order.picking_id.move_line_ids_without_package.filtered(lambda r: r.picking_id.state == 'done')
                qty_grn = sum(move_line.mapped('qty_done'))
                order.qty_unreceived = qty_grn -  allocation_qty

                if not order.qty_unreceived != 0:
                    order.compare_qty = True

            else:
                order.qty_received = 0
                order.qty_unreceived = 0
            
            if order.qty_unreceived < 0:
                raise UserError(_('unReceived > 0'))
    

    contract_id = fields.Many2one('purchase.contract', string='Contract')
    type_contract = fields.Selection([('consign', 'Consignment Agreement'), ('purchase', 'Purchase Contract')],
                            string="Type", related='contract_id.type',store=True)
    product_id = fields.Many2one('product.product',related='picking_id.product_id', string='Product',store=True)
    picking_id = fields.Many2one('stock.picking', string='GRN',
       readonly=False, states={'draft': [('readonly', False)]}, required=False,)
    date_allocation = fields.Date(string="Date Allocation",default= time.strftime(DAT))
    
    grade_id = fields.Many2one('product.category', string='Grade', related='product_id.categ_id', store=True)

    #err kiet dim
    # qty_grn = fields.Float('picking_id.total_qty',string='GRN Qty')
    # qty_grn = fields.Float(related='picking_id.total_qty',string='GRN Qty', store = True)
    
    
    date_picking = fields.Datetime(related='picking_id.date_done',string='Date Picking',store=True)
    partner_id = fields.Many2one(related ='picking_id.partner_id',string='Partner',store=True)
    qty_contract = fields.Float(related ='contract_id.total_qty',string='Contract Qty',store=True)
    price_contract = fields.Float(related = 'contract_id.price_unit',string='Fix Price',store=True)

    date_contract = fields.Date(related='contract_id.date_order',string='Date Contract')
    qty_allocation = fields.Float(string='Qty Allocation',digits=(12, 0))
    qty_received = fields.Float(compute='_compute_qty',string = 'Allocated',store=True,digits=(12, 0))
    qty_unreceived = fields.Float(compute='_compute_qty',string = 'UnAllocated',digits=(12, 0), store=True)
    compare_qty = fields.Boolean(compute='_compute_qty',string = "Compare",default =True, store=True)
    
    state = fields.Selection([('draft', 'New'), ('approved', 'Approved')], string='Status',
                             readonly=True, copy=False, index=True, default='draft')

    allocation_picking_id = fields.Many2one('stock.picking',string='GRN Allocate')
    # warehouse_id = fields.Many2one('stock.warehouse', related=False, string='Warehouse', store=True)

    license_id = fields.Many2one('ned.certificate.license', string='License', store=True,
                                 related='contract_id.license_id')

    # @api.depends('contract_id.license_id')
    # def _compute_license_id(self):
    #     for allocation in self:
    #         allocation.license_id = allocation.contract_id.license_id


    def unlink(self):
        if any([x.state in ('approved') for x in self]):
            raise UserError(_('You can not delete a, You set to cancel picking'))
        return super(StockAllocation, self).unlink()

    #reamin_qty = fields.Float(compute='_reamin_qty', string='Remain Qty', readonly=True,store = True)
    
    def _create_stock_moves(self, line, picking,  allocation):
        qty = allocation.qty_allocation
        moves = self.env['stock.move.line']
        price_unit = line.price_unit
#         price_unit = line.price_unit * allocation.picking_id.total_qty / allocation.picking_id.total_init_qty
        price_currency = price_unit = line.price_unit
        # if line.tax_id:
        #     price_unit = line.tax_id.compute_all(price_unit, currency=line.contract_id.currency_id, quantity=1.0)['total_excluded']
        # if line.product_uom.id != line.product_id.uom_id.id:
        #     price_unit = line.product_uom.factor / line.product_id.uom_id.factor
        
        #kiet: Quyy doi
        date_contract = picking.date_done
        price_unit = self.env.user.company_id.second_currency_id.with_context(date=date_contract).compute(price_unit, 
                                                                                                 self.env.user.company_id.currency_id,
                                                                                                 round=False)
        
        vals = {
                'picking_id': picking.id,
                #'name': line.name or '',
                'product_id': line.product_id.id,
                'product_uom_id': line.product_uom.id,
                'qty_done': qty or 0.0,
                'init_qty':qty,
                'price_unit': price_unit,
                # 'tax_id': [(6, 0, [x.id for x in i.tax_id])],
                'picking_type_id': picking.picking_type_id.id,
                'location_id': picking.location_id.id,
                'location_dest_id': picking.location_dest_id.id,
                'date': line.contract_id.date_order,
                'price_currency':price_currency or 0.0,
                # 'exchange_rate':this.purchase_contract_id.exchange_rate or 1,
                'currency_id':line.contract_id.currency_id.id or False,
                #'type': picking_type.code,
                'state':'draft',
                #'scrapped': False,
                'warehouse_id':line.contract_id.warehouse_id.id,
                }
        
        move_id = moves.create(vals)
        return move_id
    
    def cancel_allocation(self):
        for allocation in self:
            sql ='''
                DELETE FROM stock_move_line where picking_id in 
                    (SELECT id FROM stock_picking where allocation_id = %s);
                    
                    
                DELETE FROM stock_move where picking_id in 
                    (SELECT id FROM stock_picking where allocation_id = %s);
                    
                DELETE FROM stock_picking where allocation_id = %s;
                
            '''%(allocation.id, allocation.id, allocation.id)
            self.env.cr.execute(sql)
            allocation.state = 'draft'
            allocation.contract_id.qty_received = allocation.contract_id.qty_received - allocation.qty_allocation
            
            allocation._compute_qty()
    
        
    
    
    def approve_allocation(self):
        for allocation in self:
            
            #kiet: Im NVP
            if allocation.contract_id.type =='purchase':
                #kiet: Trường hợp transfer trạm
                if allocation.picking_id.to_picking_type_id:
                    if not allocation.picking_id.to_picking_type_id.picking_type_nvp_id:
                        raise UserError(_('You cannot approve, You must define Picking type for NVP'))
                    picking_type = allocation.picking_id.to_picking_type_id.picking_type_nvp_id
                #kiet: Trương hợp trại kho chính
                else:
                    if not allocation.picking_id.picking_type_id.picking_type_nvp_id:
                        raise UserError(_('You cannot approve, You must define Picking type for NVP'))
                    picking_type = allocation.picking_id.picking_type_id.picking_type_nvp_id
            
            #kiet: Im NPE
            else:
                if allocation.picking_id.to_picking_type_id:
                    if not allocation.picking_id.to_picking_type_id.picking_type_npe_id:
                        raise UserError(_('You cannot approve, You must define Picking type for NPE'))
                    picking_type = allocation.picking_id.to_picking_type_id.picking_type_npe_id
                else:
                    if not allocation.picking_id.picking_type_id.picking_type_npe_id:
                        raise UserError(_('You cannot approve, You must define Picking type for NPE'))
                    picking_type = allocation.picking_id.picking_type_id.picking_type_npe_id
                #kiet: Trương hợp trại kho chính
            
            var = {
                'warehouse_id':allocation.contract_id.warehouse_id.id,
                'picking_type_id': picking_type.id,
                'partner_id': allocation.contract_id.partner_id.id,
                'date': allocation.contract_id.date_order,
                'date_done':allocation.picking_id.date_done,
                'origin': allocation.contract_id.name + ';'+ allocation.picking_id.name,
                'location_dest_id': picking_type.default_location_dest_id.id,
                'location_id': picking_type.default_location_src_id.id,
                'allocation_id':allocation.id,
                'purchase_contract_id':allocation.contract_id.id
            }
            picking = self.env['stock.picking'].create(var)
            for line in allocation.contract_id.contract_line:
                moves = self._create_stock_moves(line, picking, allocation)
            picking.button_sd_validate()
            #Kiet: cho sinh bút toán luôn
            # allocation.contract_id.get_entries_picking_nvp(picking)
            
            
            allocation.allocation_picking_id = picking.id
            #allocation.date_allocation = time.strftime(DATE_FORMAT)
            allocation.state ='approved'
            allocation.contract_id.qty_received = allocation.contract_id.qty_received + allocation.qty_allocation
            
            allocation._compute_qty()
        return True