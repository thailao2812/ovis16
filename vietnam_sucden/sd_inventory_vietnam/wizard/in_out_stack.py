
# -*- coding: utf-8 -*-

import time
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

class wizradInOutStack(models.TransientModel):
    _inherit = "wizard.in.out.stack"

    bom_id = fields.Many2one('mrp.bom', string='Bill of Material',store=True, readonly=True, compute=False,
                        domain="""[(1, '=', 1)]""", required=True,
                        help="Bill of Materials allow you to define the list of required components to make a finished product.")

    def default_get(self, fields):
        res = {}
        active_ids = self._context.get('active_ids')
        res.update({'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT) or False,
                    'stack_ids' :[[6, False, active_ids]],
                    'warehouse_id': self.env['stock.lot'].browse(active_ids)[0].warehouse_id.id or False,
                    'bom_id': self.env['mrp.bom'].search([('master_code_id.type_code', '=', 'Merge')]).id or False})
        return res

    def merg_stack(self):
        stack_id = False
        company = self.env.user.company_id.id or False
        warehouse_id = False
        # picking_type_id = self.env['stock.picking.type'].search([('name', '=', 'DF')], limit=1)
        init_qty = product_qty = bag = 0
        stick_count = stone_count = mc = immature = eaten = burn = screen13 = screen16 = screen18 = screen19 = screen20 = excelsa = 0
        greatersc12 = 0
        belowsc12 = 0
        screen17 =0
        screen15 = 0
        screen14 = 0
        cherry = mold = fm = black = brown = broken = 0.0
        packing_id = False
        count = 0
        product_id = False

        # Khởi tạo mẻ sản xuất mới
        vals = {
                "is_locked": True,
                "priority":"0",
                "warehouse_id": self.warehouse_id.id,
                "company_id": company,
                "bom_id": self.bom_id.id,
                "qty_producing": 0,
                "notes": '',
                "product_qty": self.bom_id.product_qty,
                "product_uom_id": self.bom_id.product_uom_id.id,
                "date_planned_start": datetime.now().strftime(DATETIME_FORMAT),
                "picking_type_id": self.warehouse_id.production_in_type_id.id,
                "location_src_id": self.warehouse_id.production_out_type_id.id,
                "location_dest_id": self.warehouse_id.wh_finished_good_loc_id.id,
                }
        mrp_production_id = self.env['mrp.production'].create(vals)
        mrp_production_id.action_confirm()

        # Kiểm tra và khởi tạo phiếu PMR - Request Coffee Materials
        for this in self:
            if not this.stack_ids:
                raise UserError(_("Stacks is not Null"))
            for line in this.stack_ids:
                if not product_id:
                    product_id = line.product_id.id
                if product_id != line.product_id.id:
                    raise ValidationError(_('Merge Stack need to be the same product %s', line.product_id.code))
                
                if not warehouse_id:
                    warehouse_id = line.warehouse_id.id
                if warehouse_id != line.warehouse_id.id:
                    raise ValidationError(_('Merge Stack need to be the same Warehouse %s', line.warehouse_id.code))

                if line.init_qty <= 0:
                    raise UserError(_("Request Qty need to be greater than 0"))
                if line.bag_qty < 0:
                    raise UserError(_("Request Bag Qty need to be greater than or equal to 0"))

                # Khởi tạo data cho phiếu GRP - Goods Receipt Process
                init_qty += line.init_qty
                product_qty += line.remaining_qty

                mc += line.mc * line.init_qty or 0.0
                fm += line.fm * line.init_qty or 0.0
                black += line.black * line.init_qty or 0.0
                broken += line.broken * line.init_qty or 0.0
                brown += line.brown * line.init_qty or 0.0
                mold += line.mold * line.init_qty or 0.0
                cherry += line.cherry * line.init_qty or 0.0
                excelsa += line.excelsa * line.init_qty or 0.0

                screen20 += line.screen20 * line.init_qty or 0.0
                screen19 += line.screen19 * line.init_qty or 0.0
                screen18 += line.screen18 * line.init_qty or 0.0
                screen17 += line.screen17 * line.init_qty or 0.0
                screen16 += line.screen16 * line.init_qty or 0.0
                screen15 += line.screen15 * line.init_qty or 0.0
                screen14 += line.screen14 * line.init_qty or 0.0
                screen13 += line.screen13 * line.init_qty or 0.0
                greatersc12 += line.greatersc12 * line.init_qty or 0.0
                belowsc12 += line.screen12 * line.init_qty or 0.0

                burn += line.burn * line.init_qty or 0.0
                eaten += line.eaten * line.init_qty or 0.0
                immature += line.immature * line.init_qty or 0.0
                stick_count = line.stick_count
                stone_count = line.stone_count
                count += line.init_qty

                bag += line.bag_qty or 0.0
                if not packing_id:
                    packing_id = line.packing_id and line.packing_id.id or False
                
            # Khởi tạo phiếu yêu cầu nguyên liệu
            val ={
                    'warehouse_id':this.warehouse_id.id,
                    'production_id':mrp_production_id.id,
                    'origin':mrp_production_id.name,
                    'request_user_id':self.env.uid,
                    'state':'draft'
                }
            request_id = self.env['request.materials'].create(val)
            request_id.state = 'approved'
            
            for line in this.stack_ids:
                vals ={
                    'product_id':line.product_id.id,
                    'product_uom':line.product_uom_id.id,
                    'product_qty':line.init_qty or 0.0,
                    'request_id':request_id.id,
                    'stack_id':line.id
                    }
                rml = self.env['request.materials.line'].create(vals)

                # Khởi tạo phiếu GIP - Goods In Process
                location_id = False
                if rml and rml.stack_id:
                    location_id = self.warehouse_id.wh_raw_material_loc_id
                crop_id = self.env['ned.crop'].sudo().search([('state', '=', 'current')], limit=1)
                
                vals = {
                    'name': '/', 
                    'picking_type_id': self.warehouse_id.production_out_type_id.id, 
                    'date_done': datetime.now().strftime(DATETIME_FORMAT), 
                    'partner_id': False, 
                    'crop_id':crop_id.id,
                    'location_id': location_id and location_id.id or False, 
                    'production_id': rml.request_id.production_id.id or False,  
                    'location_dest_id': self.warehouse_id.production_out_type_id.default_location_dest_id.id or False,
                    'request_materials_id':rml.request_id.id,
                    'warehouse_id':self.warehouse_id.id,
                    'state':'draft',
                    'state_kcs': 'draft',
                    }  
                create_picking = self.env['stock.picking'].create(vals)
                rml.sudo().write({'picking_ids': [(4, create_picking.id)]})
                product_uom_qty = line.init_qty - (line.init_qty * abs(rml.stack_id.avg_deduction/100)) or 0.0
                spl_val ={
                    'picking_id': create_picking.id or False, 
                    'product_uom_id': rml.product_id.uom_id.id or False,
                    'init_qty':line.init_qty or 0.0,
                    'qty_done': product_uom_qty or 0.0, 
                    'reserved_uom_qty':product_uom_qty or 0.0,
                    'price_unit': 0.0,
                    'picking_type_id': create_picking.picking_type_id.id or False,
                    'location_id': create_picking.location_id.id or False,
                    'location_dest_id': create_picking.location_dest_id.id or False,
                    'company_id': self.env.user.company_id.id, 
                    'zone_id': rml.stack_id.zone_id.id or False, 
                    'product_id': rml.product_id.id or False,
                    'date': create_picking.date_done or False, 
                    'currency_id': False,
                    'state':'draft', 
                    'warehouse_id': create_picking.warehouse_id.id or False,
                    'lot_id':rml.stack_id.id,
                    'production_id': create_picking.production_id.id or False,
                    'packing_id':rml.stack_id and rml.stack_id.packing_id and rml.stack_id.packing_id.id or False,
                    'bag_no':line.bag_qty or 0.0,
                    'tare_weight': 0.0,
                    'material_id': rml.request_id.production_id.id or False,
                    }
                move_id = self.env['stock.move.line'].create(spl_val)

                create_picking.btt_loads()
                create_picking.load_qc_gip_merge()
                create_picking.button_qc_assigned()
                create_picking.btt_approved()
                create_picking.button_sd_validate()

                # Lây chất lượng bỏ qua
                rml.write({'picking_ids': [(4, create_picking.id)]})
                rml.stack_empty = False
                if rml.product_qty == rml.basis_qty:
                    rml.request_id.state = 'done'

        # Khởi tạo phiếu GRP - Goods Receipt Process
        vals = {'end_date': datetime.now().strftime(DATETIME_FORMAT),
                'start_date': datetime.now().strftime(DATETIME_FORMAT),
                'production_shift': '1',
                'create_uid': self.env.uid,
                'user_import_id': self.env.uid,
                'date_result': datetime.now().strftime(DATETIME_FORMAT),
                'production_id': mrp_production_id.id,
                'warehouse_id': self.warehouse_id.id,}
        result_id = self.env['mrp.operation.result'].create(vals)

        mc_avf = mc / count
        if result_id:
            tmp = { 'product_id': line[0].product_id.id,
                    'zone_id': self.zone_id.id,
                    'packing_id': packing_id,
                    'qty_bags': bag,
                    'tare_weight': 0.0,
                    'product_uom': line[0].product_id.uom_id.id,
                    'product_qty': init_qty,
                    'production_weight': init_qty,
                    'production_id':mrp_production_id.id,
                    'pending_grn': result_id.production_id.name.split('/')[1] + '-001-' + self.zone_id.name,
                    'operation_result_id': result_id.id,
                    'create_uid': self.env.uid,
                    }
            result_produced_product_id = self.env['mrp.operation.result.produced.product'].create(tmp)

            result_produced_product_id.create_update_stack_wip()

            result_produced_product_id.create_kcs()
            if result_produced_product_id.picking_id:
                result_produced_product_id.picking_id.btt_loads()
                result_produced_product_id.picking_id.kcs_line.update({
                                        'sample_weight': 100,
                                        'bb_sample_weight': 100,
                                        'mc_degree': mc_avf / (1 - (0.01 * mc_avf)),
                                        'fm_gram': fm / count,
                                        'black_gram': black / count,
                                        'broken_gram': broken / count,
                                        'brown_gram': brown / count,
                                        'mold_gram': mold / count,
                                        'cherry_gram': cherry / count,
                                        'excelsa_gram': excelsa / count,
                                        'screen20_gram': screen20 / count,
                                        'screen19_gram': screen19 / count,
                                        'screen18_gram': screen18 / count,
                                        'screen17_gram': screen17 / count,
                                        'screen16_gram': screen16 / count,
                                        'screen15_gram': screen15 / count,
                                        'screen14_gram': screen14 / count,
                                        'screen13_gram': screen13 / count,
                                        'greatersc12_gram':greatersc12 / count,
                                        'belowsc12_gram': belowsc12 / count,
                                        'burned_gram': burn / count,
                                        'eaten_gram': eaten / count,
                                        'immature_gram': immature / count,
                                        'stone_count': stone_count,
                                        'stick_count': stick_count,
                                        'check_deduction': True,
                                        })
                result_produced_product_id.picking_id.kcs_line._percent_mc()
                result_produced_product_id.picking_id.kcs_line._percent_fm()
                result_produced_product_id.picking_id.kcs_line._percent_black()
                result_produced_product_id.picking_id.kcs_line._percent_broken()
                result_produced_product_id.picking_id.kcs_line._percent_brown()
                result_produced_product_id.picking_id.kcs_line._percent_mold()
                result_produced_product_id.picking_id.kcs_line._percent_cherry()
                result_produced_product_id.picking_id.kcs_line._percent_excelsa()
                result_produced_product_id.picking_id.kcs_line._percent_screen20()
                result_produced_product_id.picking_id.kcs_line._percent_screen19()
                result_produced_product_id.picking_id.kcs_line._percent_screen18()
                result_produced_product_id.picking_id.kcs_line._percent_screen17()
                result_produced_product_id.picking_id.kcs_line._percent_screen16()
                result_produced_product_id.picking_id.kcs_line._percent_screen15()
                result_produced_product_id.picking_id.kcs_line._percent_screen14()
                result_produced_product_id.picking_id.kcs_line._percent_screen13()
                result_produced_product_id.picking_id.kcs_line._greatersc12_gram()
                result_produced_product_id.picking_id.kcs_line._percent_greatersc12()
                result_produced_product_id.picking_id.kcs_line._percent_belowsc12()
                result_produced_product_id.picking_id.kcs_line._screen12_deduct()
                result_produced_product_id.picking_id.kcs_line._percent_burned()
                result_produced_product_id.picking_id.kcs_line._percent_eaten()
                result_produced_product_id.picking_id.kcs_line._percent_immature()
                result_produced_product_id.picking_id.kcs_line._compute_deduction()
                                
                #Done Phiếu chất lượng
                result_produced_product_id.picking_id.btt_approved()
                
                #Tạo Stack phiếu kho
                for move_line in result_produced_product_id.picking_id.move_line_ids_without_package:
                    if not move_line.lot_id:
                        var = {
                            'product_id':move_line.product_id.id,
                            'company_id':self.warehouse_id.company_id.id or False,
                            'zone_id': self.zone_id.id,
                            'date': datetime.now().strftime(DATETIME_FORMAT),
                            'name':'/',
                            }
                    lot_id = self.env['stock.lot'].create(var)
                    
                    move_line.lot_id = lot_id and lot_id.id or False
                result_produced_product_id.picking_id.date_done = datetime.now().strftime(DATETIME_FORMAT)
                result_produced_product_id.picking_id.button_sd_validate()
        
        mrp_production_id.button_mark_done()
        
        return True

