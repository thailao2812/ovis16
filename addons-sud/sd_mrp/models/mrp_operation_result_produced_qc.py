# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import time
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import datetime, timedelta
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
from odoo.exceptions import UserError, ValidationError, AccessError


class MrpOperationResultProducedProduct(models.Model):
    _inherit = 'mrp.operation.result.produced.product'
    
    zone_id = fields.Many2one("stock.zone",string="Zone")
    zone = fields.Char('Zone')
    stack_id = fields.Many2one("stock.lot",string="Stack")
    stack = fields.Char('stack')
    product_id = fields.Many2one("product.product",string="Product")
    product = fields.Char(string="Product")
    packing = fields.Char(string="packing")
    source = fields.Char(string="Source")
    bag = fields.Char(string="Bag")
    mc = fields.Float(string="Mc")
    fm = fields.Float(string="Fm")
    black = fields.Float(string="Black")
    broken = fields.Float(string="Broken")
    brown = fields.Float(string="Brown")
    mold = fields.Float(string="Mold")
    cherry = fields.Float(string="Cherry")
    excelsa = fields.Float(string="Excelsa")
    screen20 = fields.Float(string="Screen20")
    screen19 = fields.Float(string="Screen19")
    screen18 = fields.Float(string="Screen18")
    screen17 = fields.Float(string="Screen17")
    screen16 = fields.Float(string="Screen16")
    screen15 = fields.Float(string="Screen15")
    screen14 = fields.Float(string="Screen14")
    screen13 = fields.Float(string="Screen13")
    screen12 = fields.Float(string="Screen12")
    below_screen12 = fields.Float(string="Below Screen12")
    immature = fields.Float(string="Immature")
    burn = fields.Float(string="Burn")
    insect = fields.Float(string="Insect")
    stone = fields.Char(string="Stone")
    stick = fields.Char(string="Stick")
    remarks = fields.Char(string="Remarks")
    remark_note = fields.Char(string="Remark Note")
    sampler = fields.Char(string="Sampler")
    x_bulk_density = fields.Char(string="Bulk Density")
    x_inspector = fields.Many2one('x_inspectors.kcs')

    
    def create_kcs11(self):
        # name = self.operation_result_id.name.split('Separate')[0].rstrip('/')
        # manufacturing_order = self.env['mrp.production'].search([
        #     ('name', '=', name)
        # ])
        if self.operation_result_id.operation_id.production_id:
            if self.operation_result_id.operation_id.production_id.warehouse_id.code != 'FA':
                produced = self
                warehouse_obj = produced.operation_result_id.operation_id.production_id.warehouse_id
                result = produced.operation_result_id
                production_obj = produced.operation_result_id.operation_id.production_id
                product_qty = production_weight = 0
                company_id = production_obj.company_id.id or False
                move = self.env['stock.move.line']
                operation_produce = self.env['mrp.production.workcenter.product.produce']
                operation_consumed = self.env['mrp.production.workcenter.consumed.produce']
                if produced.picking_id:
                    return
                if produced.product_qty > 0 and produced.production_weight > 0:

                    picking_type_id = warehouse_obj.production_in_type_id.id or False
                    picking_type = self.env['stock.picking.type'].browse(picking_type_id)

                    if not produced.product_id.property_stock_production.id:
                        error = "Production Locations  does not exist."
                        raise UserError(_(error))
                    location_id = produced.product_id.property_stock_production.id
                    if not warehouse_obj.wh_production_loc_id.id:
                        error = "Location Destination does not exist."
                        raise UserError(_(error))
                    #location_dest_id = warehouse_obj.wh_production_loc_id.id
                    location_dest_id = warehouse_obj.wh_finished_good_loc_id.id
                    for bom_material in result.operation_id.production_id.bom_id.bom_stage_lines.bom_stage_material_line:
                        val ={
                            'product_id':bom_material.product_id.id,
                            'product_uom':bom_material.product_uom.id,
                            'date_consumed':time.strftime('%Y-%m-%d'),
                            'operation_result_id':result.id,
                            'check_kcs':False,
                            'product_qty':0.0,
                            'production_weight':0.0,
                            'finished_id':produced.id
                            }
                        self.env['mrp.operation.result.consumed.product'].create(val)


                    product_qty += produced.product_qty
                    production_weight += produced.production_weight
                    # Kiệt: Create nhập kho Thành phẩm Thêm Picking để KCS NED
                    var = {
                        'name':produced.pending_grn or False,
                        'picking_type_id': picking_type_id,
                        'partner_id': False,
                        'date': fields.Datetime.now,
                        'date_sent': fields.Datetime.now,
                        'origin': produced.pending_grn or False,
                        'location_dest_id': location_dest_id,
                        'location_id': 7,
                        'state':'draft',
                        'production_id':production_obj.id,
                        'operation_id':result.operation_id.id,
                        'result_id':result.id,
                        'note':produced.notes
                    }
                    picking_id = self.env['stock.picking'].create(var)
                    move.create({'picking_id': picking_id.id, 'name': produced.product_id.name or '', 'product_id': produced.product_id.id or False,
                        'product_uom': produced.product_uom.id or False,
                        'init_qty':produced.product_qty or 0.0, 'weighbridge':produced.production_weight or 0.0,
                        'product_uom_qty': produced.product_qty or 0.0, 'price_unit': 0.0,
                        'picking_type_id': picking_type_id or False, 'location_id': location_id or False, 'production_id': production_obj.id,
                        'location_dest_id': location_dest_id or False, 'date_expected': time.strftime('%Y-%m-%d %H:%M:%S') or False,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S') or False, 'type': picking_type.code or False, 'result_id': result.id,
                        'zone_id':produced.zone_id and produced.zone_id.id or False,
                        'packing_id':produced.packing_id.id,
                        'bag_no':produced.qty_bags or 0.0,
                        'company_id': company_id, 'state':'draft', 'scrapped': False, 'warehouse_id': warehouse_obj.id or False})


                    i = self
                    # Nghiệp vụ tạo phiếu QC
                    picking_id.btt_loads()
                    for j in picking_id.kcs_line:
                        j.sample_weight = 100
                        j.bb_sample_weight = 100
                        j.mc_degree  =produced.mc
                        j.fm_gram = i.fm
                        j.black_gram = i.black
                        j.broken_gram =i.broken
                        j.brown_gram = i.brown
                        j.mold_gram = i.mold
                        j.cherry_gram = i.cherry
                        j.excelsa_gram = i.excelsa
                        j.screen20_gram = i.screen20
                        j.screen19_gram = i.screen19
                        j.screen18_gram = i.screen18
                        j.screen17_gram = i.screen17
                        j.screen16_gram = i.screen16
                        j.screen15_gram = i.screen15
                        j.screen14_gram = i.screen14
                        j.screen13_gram = i.screen13
                        j.screen12_gram = i.screen12
                        j.belowsc12_gram = i.below_screen12
                        j.immature_gram = i.immature
                        j.burned_gram = i.burn
                        j.insect_gram = i.insect
                        j.stone_count = i.stone
                        j.stick_count = i.stick
                        j.remarks = i.remarks
                        j.remark_note = i.remark_note
                        j.sampler = i.sampler or False
                        j.x_bulk_density = i.x_bulk_density or False
                        j.x_inspectator = i.x_inspector.id or False

                    picking_id.date_done = picking_id.scheduled_date
                    picking_id.action_confirm()
                    picking_id.btt_approved()
                    # picking_id.action_confirm()

                    produced.picking_id = picking_id.id
                    #self.env['mrp.operation.result.produced.product'].write(produced.id,{'picking_id':picking_id.id})
                    operation_produce_id = operation_produce.search([('operation_id','=',result.operation_id.id),('product_id','=',produced.product_id.id)])
                    if operation_produce_id:
                        operation_produce_id.check_kcs =False
                    else:
                        operation_produce.create({'check_kcs':False,'product_id': produced.product_id.id or False, 'product_uom': produced.product_uom.id or False,
                            'operation_id': result.operation_id.id})

                #     Kiet: Tạo nguyên vật liệu tiêu hao
                for bom_material in result.operation_id.production_id.bom_id.bom_stage_lines.bom_stage_material_line:
                    operation_consumed_id = operation_consumed.search([('operation_id','=',result.operation_id.id),('product_id','=',bom_material.product_id.id)])
                    if operation_consumed_id:
                        operation_consumed_id.check_kcs =False
                    else:
                        val = {
                            'product_id':bom_material.product_id.id,
                            'product_uom':bom_material.product_uom.id,
                            'operation_id':result.operation_id.id,
                            'check_kcs':False,
                            'product_qty':0
                        }
                        operation_consumed.create(val)

            if self.operation_result_id.operation_id.production_id.warehouse_id.code == 'FA':
                produced = self
                warehouse_obj = produced.operation_result_id.operation_id.production_id.warehouse_id
                result = produced.operation_result_id
                production_obj = produced.operation_result_id.operation_id.production_id
                product_qty = production_weight = 0
                company_id = production_obj.company_id.id or False
                move = self.env['stock.move']
                operation_produce = self.env['mrp.production.workcenter.product.produce']
                operation_consumed = self.env['mrp.production.workcenter.consumed.produce']
                if produced.picking_id:
                    return
                if produced.product_qty > 0 and produced.production_weight > 0:

                    picking_type_id = warehouse_obj.production_in_type_id.id or False
                    picking_type = self.env['stock.picking.type'].browse(picking_type_id)

                    if not produced.product_id.property_stock_production.id:
                        error = "Production Locations  does not exist."
                        raise UserError(_(error))
                    location_id = produced.product_id.property_stock_production.id
                    if not warehouse_obj.wh_production_loc_id.id:
                        error = "Location Destination does not exist."
                        raise UserError(_(error))
                    # location_dest_id = warehouse_obj.wh_production_loc_id.id
                    location_dest_id = warehouse_obj.wh_finished_good_loc_id.id
                    for bom_material in result.operation_id.production_id.bom_id.bom_stage_lines.bom_stage_material_line:
                        val = {
                            'product_id': bom_material.product_id.id,
                            'product_uom': bom_material.product_uom.id,
                            'date_consumed': time.strftime('%Y-%m-%d'),
                            'operation_result_id': result.id,
                            'check_kcs': False,
                            'product_qty': 0.0,
                            'production_weight': 0.0,
                            'finished_id': produced.id
                        }
                        self.env['mrp.operation.result.consumed.product'].create(val)

                    product_qty += produced.product_qty
                    production_weight += produced.production_weight
                    # Kiệt: Create nhập kho Thành phẩm Thêm Picking để KCS NED
                    var = {
                        'name': produced.pending_grn or False,
                        'picking_type_id': picking_type_id,
                        'partner_id': False,
                        'date': datetime.now(),
                        'date_sent': datetime.now(),
                        'origin': produced.pending_grn or False,
                        'location_dest_id': location_dest_id,
                        'location_id': 7,
                        'state': 'draft',
                        'production_id': production_obj.id,
                        'operation_id': result.operation_id.id,
                        'result_id': result.id,
                        'note': produced.notes
                    }
                    picking_id = self.env['stock.picking'].create(var)
                    move.create({'picking_id': picking_id.id, 'name': produced.product_id.name or '',
                                 'product_id': produced.product_id.id or False,
                                 'product_uom': produced.product_uom.id or False,
                                 'init_qty': produced.product_qty or 0.0,
                                 'weighbridge': produced.production_weight or 0.0,
                                 'product_uom_qty': produced.product_qty or 0.0, 'price_unit': 0.0,
                                 'picking_type_id': picking_type_id or False, 'location_id': location_id or False,
                                 'production_id': production_obj.id,
                                 'location_dest_id': location_dest_id or False,
                                 'date_expected': time.strftime('%Y-%m-%d %H:%M:%S') or False,
                                 'date': time.strftime('%Y-%m-%d %H:%M:%S') or False,
                                 'type': picking_type.code or False, 'result_id': result.id,
                                 'zone_id': produced.zone_id and produced.zone_id.id or False,
                                 'packing_id': produced.packing_id.id,
                                 'bag_no': produced.qty_bags or 0.0,
                                 'company_id': company_id, 'state': 'draft', 'scrapped': False,
                                 'warehouse_id': warehouse_obj.id or False})

                    i = self
                    # Nghiệp vụ tạo phiếu QC
                    picking_id.btt_loads()
                    # for j in picking_id.kcs_line:
                    #     j.sample_weight = 100
                    #     j.bb_sample_weight = 100
                    #     j.mc_degree = produced.mc
                    #     j.fm_gram = i.fm
                    #     j.black_gram = i.black
                    #     j.broken_gram = i.broken
                    #     j.brown_gram = i.brown
                    #     j.mold_gram = i.mold
                    #     j.cherry_gram = i.cherry
                    #     j.excelsa_gram = i.excelsa
                    #     j.screen20_gram = i.screen20
                    #     j.screen19_gram = i.screen19
                    #     j.screen18_gram = i.screen18
                    #     j.screen17_gram = i.screen17
                    #     j.screen16_gram = i.screen16
                    #     j.screen15_gram = i.screen15
                    #     j.screen14_gram = i.screen14
                    #     j.screen13_gram = i.screen13
                    #     j.screen12_gram = i.screen12
                    #     j.belowsc12_gram = i.below_screen12
                    #     j.immature_gram = i.immature
                    #     j.burned_gram = i.burn
                    #     j.insect_gram = i.insect
                    #     j.stone_count = i.stone
                    #     j.stick_count = i.stick
                    #     j.remarks = i.remarks
                    #     j.remark_note = i.remark_note
                    #     j.sampler = i.sampler or False
                    #     j.x_bulk_density = i.x_bulk_density or False
                    #     j.x_inspectator = i.x_inspector.id or False

                    picking_id.date_done = picking_id.scheduled_date
                    picking_id.action_confirm()
                    # picking_id.btt_approved()
                    # picking_id.action_confirm()

                    produced.picking_id = picking_id.id
                    # self.env['mrp.operation.result.produced.product'].write(produced.id,{'picking_id':picking_id.id})
                    operation_produce_id = operation_produce.search(
                        [('operation_id', '=', result.operation_id.id), ('product_id', '=', produced.product_id.id)])
                    if operation_produce_id:
                        operation_produce_id.check_kcs = False
                    else:
                        operation_produce.create({'check_kcs': False, 'product_id': produced.product_id.id or False,
                                                  'product_uom': produced.product_uom.id or False,
                                                  'operation_id': result.operation_id.id})

                #     Kiet: Tạo nguyên vật liệu tiêu hao
                for bom_material in result.operation_id.production_id.bom_id.bom_stage_lines.bom_stage_material_line:
                    operation_consumed_id = operation_consumed.search([('operation_id', '=', result.operation_id.id),
                                                                       ('product_id', '=', bom_material.product_id.id)])
                    if operation_consumed_id:
                        operation_consumed_id.check_kcs = False
                    else:
                        val = {
                            'product_id': bom_material.product_id.id,
                            'product_uom': bom_material.product_uom.id,
                            'operation_id': result.operation_id.id,
                            'check_kcs': False,
                            'product_qty': 0
                        }
                        operation_consumed.create(val)

class MrpOperationResult(models.Model):
    _inherit = 'mrp.operation.result'
    
    produced_products_qc = fields.One2many('mrp.operation.result.produced.product', 'operation_result_id', 'Qc Line', readonly=True, states={'draft': [('readonly', False)]})
    
    
    
    
