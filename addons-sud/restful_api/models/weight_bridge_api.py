# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, fields, http, models, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import append_content_to_html, float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round
# from odoo.http import http
from odoo import SUPERUSER_ID
# from odoo.addons.website import slug, unslug
from odoo.http import route, request, json
# from models import JWTAuth
from odoo.tools.misc import formatLang
import time
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"



class APIWeightBridge(http.Controller):


    @http.route('/api/weight/supplier', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_partner(self):
        sql = '''SELECT id, shortname from res_partner Where (is_supplier_coffee=true or is_customer_coffee=true)
                and shortname is not null'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/weight/product', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_product(self):
        sql = '''SELECT id, default_code as company_code, display_wb from product_product where default_code is not null'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/weight/packing', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_packing(self):
        sql = '''SELECT * from ned_packing Where active = 'true'; '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            tmp = 0
            for x in result:
                result[tmp]['create_date'] = str(result[tmp]['create_date'])
                result[tmp]['write_date'] = str(result[tmp]['write_date'])
                tmp += 1
            del(tmp)
            return json.dumps(result)

    @http.route('/api/weight/picking', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_picking(self):
        sql = '''SELECT sp.name
                FROM stock_picking sp
                WHERE sp.state = 'draft'
                    AND picking_type_code in ('incoming','transfer_out','outgoing')
                    AND (sp.weightbridge_update != True OR sp.weightbridge_update is null)
                    ; 
                '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)



    @http.route('/api/weight/create_stack', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def api_create_stack(self, **post):
        zone_id = int(post.get('zone_id'))
        product_id = int(post.get('product_id'))
        stack_id = False
        var = {
            'name': '/',
            'zone_id':zone_id,
            'product_id':product_id and product_id or 1,
            'stack_type': 'stacked',
            'company_id': 1
          }

        if stack_id:
            stack_id = request.env['stock.lot'].sudo().browse(stack_id)
            zone_id = stack_id.zone_id.id
            mess = {
                'message': 'Successful!',
            }
            return json.dumps(mess)

        stack_id = request.env['stock.lot'].sudo().create(var)
        mess = {
            'message': 'Successful!',
            }
        return json.dumps(mess)


    @http.route('/api/weight/delivery', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_delivery_order(self):
        sql = '''SELECT d.name as name
                FROM delivery_order d
                JOIN stock_warehouse sw ON sw.id = d.from_warehouse_id
                WHERE d.state = 'approved' AND sw.code = 'BCCE'
                AND type = 'Transfer'; 
                '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)


    def create_stack(self, zone_id, stack_id, product_id, stack_type, warehouse_id): #=False
        if stack_id:
            stack_id = request.env['stock.lot'].sudo().browse(stack_id)
            zone_id = stack_id.zone_id.id
            # print('1. Founded tack ', stack_id.id)
            return zone_id,stack_id.id

        var = {
            'name': '/',
            'zone_id': int(zone_id),
            'product_id': int(product_id) and product_id or 1,
            'stack_type': stack_type,
            'company_id': 1,
            'warehouse_id': warehouse_id,
          }

        stack_id = request.env['stock.lot'].sudo().create(var)
        # print('2. Created tack ', stack_id.id)
        return zone_id,stack_id.id

    def create_stack_building(self, zone_id, stack_id, product_id, stack_type, building_id, warehouse_id): #=False
        if stack_id:
            stack_id = request.env['stock.lot'].sudo().browse(stack_id)
            zone_id = stack_id.zone_id.id
            # print('1. Founded tack ', stack_id)
            return zone_id,stack_id.id

        var = {
            'name': '/',
            'zone_id':zone_id,
            'building_id':building_id,
            'product_id':product_id and product_id or 1,
            'stack_type': stack_type,
            'company_id': 1,
            'warehouse_id': warehouse_id
          }

        stack_id = request.env['stock.lot'].sudo().create(var)
        # print('2. Created tack ', stack_id)
        return zone_id,stack_id.id

    @http.route('/api/weight/check_country', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def check_country(self, **post):
        sql = '''SELECT name FROM res_company WHERE name ilike '%VN%' or name ilike '%VIỆT NAM%';'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)
    
    @http.route('/api/weight/update_grn', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def update_grn(self, **post):
        station_ids =[]
        vehicle_no = post.get('soxe')
        first_weight = post.get('weight_in')
        second_weight = post.get('weight_out')
        bag_no = post.get('num_of_bag')
        tare_weight = post.get('total_weight_of_bag')
        init_qty = post.get('real_weight')
        weight_scale_id = post.get('weight_scale_id')
        weight_scale_id = request.env['res.users'].sudo().search([('login','=',weight_scale_id)])
        
        weight_user_id = post.get('weight_user_id')
        if weight_user_id and isinstance(weight_user_id, str):
            weight_user_id = int(post.get('weight_user_id'))

        product_id = post.get('product_id')
        if product_id and isinstance(product_id, str):
            product_id = int(post.get('product_id'))
        if not product_id:
            mess = {
                'err_code': 'SUD23-00000',
                'message': 'Product does not exist.',
                }
            return json.dumps(mess)

        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))
        if not warehouse_id:
            mess = {
                'err_code': 'SUD23-00000',
                'message': 'Warehouse does not exist.',
                }
            return json.dumps(mess)
        
        # weighing_app_id = post.get('weighing_app_id')
        # if weighing_app_id and isinstance(weighing_app_id, str):
        #     weighing_app_id = int(post.get('weighing_app_id'))

        flag = post.get('flag')
        stack_type = post.get('stack_type')
        reweighing_reason = post.get('reweighing_reason')
    
        warehouse_id = request.env['stock.warehouse'].sudo().browse(warehouse_id)
        product_id = request.env['product.product'].sudo().browse(product_id)

        partner_id = post.get('partner_id')
        if partner_id and isinstance(partner_id, str):
            partner_id = int(post.get('partner_id'))

        packing_id = post.get('packing_id')
        if packing_id and isinstance(packing_id, str):
            packing_id = int(post.get('packing_id'))
        if packing_id:
            packing_id = request.env['ned.packing'].sudo().browse(packing_id)
                    
        districts_id = post.get('districts_id')
        if districts_id and isinstance(districts_id, str):
            districts_id = int(post.get('districts_id'))
            
        gate_id = post.get('gate_id')
        if gate_id and isinstance(gate_id, str):
            gate_id = int(post.get('gate_id'))
        if not gate_id:
            mess = {
                'err_code': 'SUD23-00000',
                'message': 'Gate does not exist.',
                }
            return json.dumps(mess)
        
        gate_id = request.env['ned.security.gate.queue'].sudo().browse(gate_id)
        gate_id.license_plate = vehicle_no
        gate_id.supplier_id = partner_id
        if not gate_id.time_in:
            gate_id.time_in = datetime.now()
        # if weighing_app_id:
        #     gate_id.weighing_app_id = weighing_app_id
        
        if gate_id.picking_ids and len(gate_id.picking_ids)== 1:
            picking_id = gate_id.picking_ids and gate_id.picking_ids[0]
            if not picking_id:
                mess = {
                    'err_code': 'SUD23-00003',
                    'message': 'Picking does not exist.',
                    }
                return json.dumps(mess)
            else:
                if warehouse_id != picking_id.warehouse_id:
                    picking_id.with_user(weight_user_id).update({
                                        'warehouse_id': warehouse_id.id
                                    })
                    for move in picking_id.move_line_ids_without_package:
                        move.with_user(weight_user_id).update({
                                            'location_dest_id': warehouse_id.wh_input_stock_loc_id.id,
                                            })
                    if picking_id.backorder_id:
                        picking_id.backorder_id.with_user(weight_user_id).update({
                                        'warehouse_id': warehouse_id.id
                                    })
                    for move in picking_id.backorder_id.move_line_ids_without_package:
                        move.with_user(weight_user_id).update({
                                            'location_dest_id': warehouse_id.wh_input_stock_loc_id.id,
                                            })
                
                picking_id.with_user(weight_user_id).update({
                        'vehicle_no': vehicle_no,
                        'weightbridge_update': True,
                        'partner_id': partner_id,
                        'weight_scale_id': weight_scale_id.id,
                        'districts_id': districts_id,
                        'date_done': datetime.now(),
                    })
                if not picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id) and len(picking_id.move_line_ids_without_package) == 0:
                    data = {
                        'picking_id':picking_id.id,
                        'partner_id':partner_id,
                        'price_unit':0,
                        'location_id':picking_id.picking_type_id.default_location_src_id.id,
                        'date': datetime.now(),
                        'product_id': product_id.id,
                        'product_uom_id': product_id.uom_id.id,
                        'location_dest_id': picking_id.picking_type_id.default_location_dest_id.id,
                        'company_id': picking_id.company_id.id,
                    }
                    request.env['stock.move.line'].with_user(weight_user_id).create(data)

                for move in picking_id.move_ids:
                    move.with_user(weight_user_id).update({
                        'product_id': product_id.id,
                    })

                for move in picking_id.move_line_ids_without_package:
                    if not move.filtered(lambda x: x.product_id == product_id) and len(move) == 1 and picking_id.state == 'draft':
                        picking_id.product_id = product_id
                        move.with_user(weight_user_id).update({
                            'product_id': product_id.id,
                        })

                print(len(picking_id.kcs_line))
                if len(picking_id.kcs_line) == 0:    
                    for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                        move.with_user(weight_user_id).update({
                            'first_weight': first_weight,
                            'second_weight': second_weight,
                            'bag_no': bag_no,
                            'tare_weight': tare_weight,
                            'init_qty': init_qty,
                            'description_picking': reweighing_reason,
                        })

                    if flag == u'True':
                        zone_id = post.get('zone_id')
                        stack_id = post.get('stack_id')
                        building_id = post.get('building_id')
                        if zone_id and isinstance(zone_id, str):
                            zone_id = int(post.get('zone_id'))
                        if stack_id and isinstance(stack_id, str):
                            stack_id = int(post.get('stack_id'))
                        if building_id and isinstance(building_id, str):
                            building_id = int(post.get('building_id'))

                        sql = '''SELECT name FROM res_company WHERE name ilike '%VN%' or name ilike '%VIỆT NAM%';'''
                        records = request.cr.execute(sql)
                        result = request.env.cr.dictfetchall()
                        # print(zone_id,stack_id)
                        if result == []:
                            zone_id,stack_id = self.create_stack_building(zone_id, stack_id, int(product_id), stack_type, building_id, warehouse_id.id)
                        else:
                            zone_id,stack_id = self.create_stack(zone_id, stack_id, int(product_id), stack_type, warehouse_id.id)
                        
                        if not stack_id:
                            if not zone_id:
                                mess = {
                                    'err_code': 'SUD23-00003',
                                    'message': 'Zone does not exist.',
                                    }
                                return json.dumps(mess)

                        for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                            move.with_user(weight_user_id).update({
                                'lot_id':stack_id,
                                'zone_id':zone_id
                            })
                        picking_id.button_qc_assigned()
                        gate_id.state ='closed'
                        gate_id.time_out = datetime.now()

                    if packing_id:
                        for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                            move.with_user(weight_user_id).update({
                                'packing_id': packing_id.id
                            })
                    
                    if flag == u'True':
                        # print(stack_id,picking_id.move_line_ids_without_package.lot_id.name)
                        mess = {
                                'err_code': 'SUD23-00000',
                                'message': 'Weighment completed!',
                                'picking_name': picking_id.name,
                                'picking_id':picking_id.id,
                                'stack_id':stack_id,
                                'stack_name':picking_id.move_line_ids_without_package.lot_id.name,
                                }
                        return json.dumps(mess)
                    else:
                        mess = {
                                'err_code': 'SUD23-00000',
                                'message': 'Update GRN completed!',
                                'picking_name': picking_id.name,
                                'picking_id':picking_id.id,
                                }
                        return json.dumps(mess)
                else:
                    mess = {
                            'err_code': 'SUD23-00003',
                            'message': 'This GRN has been done at QC step. Can not update!',
                            }
                    return json.dumps(mess)


    @http.route('/api/weight/update_receipt_warehouse', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def update_receipt_warehouse(self, **post):
        station_ids =[]
        grn_ids =[]
        gate_id = post.get('gate_id')
        vehicle_no = post.get('soxe')
        product_id = post.get('product_id')
        first_weight = post.get('weight_in')
        second_weight = post.get('weight_out')
        packing_id = post.get('packing_id')
        bag_no = post.get('num_of_bag')
        tare_weight = post.get('total_weight_of_bag')
        init_qty = post.get('real_weight')
        weight_scale_id = post.get('weight_scale_id')
        districts_id = post.get('districts_id')
        stack_type = post.get('stack_type')
        flag = post.get('flag')
        
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))

        if flag != u'False':
            zone_id = post.get('zone_id')
            stack_id = post.get('stack_id')
            if zone_id and isinstance(zone_id, str):
                zone_id = int(post.get('zone_id'))
            if stack_id and isinstance(stack_id, str):
                stack_id = int(post.get('stack_id'))
            zone_id,stack_id = self.create_stack(zone_id, stack_id, int(product_id), stack_type, warehouse_id)
            
            if not stack_id:
                if not zone_id:
                    mess = {
                    'message': 'Zone does not exist.',
                    }
                    return json.dumps(mess)
    
        if not gate_id:
            mess = {
                'message': 'Gate does not exist.',
                }
            return json.dumps(mess)
        
        if gate_id and isinstance(gate_id, str):
            gate_id = int(post.get('gate_id'))
            
        if product_id and isinstance(product_id, str):
            product_id = int(post.get('product_id'))
        # print product_id
        if packing_id and isinstance(packing_id, str):
            packing_id = int(post.get('packing_id'))
            
        if districts_id and isinstance(districts_id, str):
            districts_id = int(post.get('districts_id'))

        if not product_id:
            mess = {
                'message': 'Product does not exist.',
                }
            return json.dumps(mess)
            
        gate_id = request.env['ned.security.gate.queue'].sudo().browse(gate_id)
        product_id = request.env['product.product'].sudo().browse(product_id)
        if packing_id:
            packing_id = request.env['ned.packing'].sudo().browse(packing_id)
        
        partner_id = post.get('partner_id')
        if partner_id and isinstance(partner_id, str):
            partner_id = int(post.get('partner_id'))
        gate_id.license_plate = vehicle_no
        gate_id.supplier_id = partner_id
        
        if not gate_id.time_in:
            gate_id.time_in = datetime.now()
        

        if not warehouse_id:
            mess = {
                'message': 'Warehouse does not exist.',
                }
            return json.dumps(mess)
        warehouse_id = request.env['stock.warehouse'].sudo().browse(warehouse_id)

        
        if gate_id.picking_ids and len(gate_id.picking_ids)== 1:
            picking_id = gate_id.picking_ids and gate_id.picking_ids[0]
            if not picking_id:
                mess = {
                    'message': 'Picking does not exist.',
                    }
                return json.dumps(mess)
            else:
                if warehouse_id != picking_id.warehouse_id:
                    picking_id.sudo().update({
                                        'warehouse_id': warehouse_id.id
                                    })
                    for move in picking_id.move_line_ids_without_package:
                        move.sudo().update({
                                            'location_dest_id': warehouse_id.wh_input_stock_loc_id.id,
                                            })
                    if picking_id.backorder_id:
                        picking_id.backorder_id.sudo().update({
                                        'warehouse_id': warehouse_id.id
                                    })
                    for move in picking_id.backorder_id.move_line_ids_without_package:
                        move.sudo().update({
                                            'location_dest_id': warehouse_id.wh_input_stock_loc_id.id,
                                            })
                
                picking_id.update({
                    'vehicle_no': vehicle_no,
                    'weightbridge_update': True,
                    'partner_id': partner_id,
                    'weight_scale_id': weight_scale_id,
                    'districts_id': districts_id,
                    'date_done': datetime.now(),
                })
                if not picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    data = {
                    'picking_id':picking_id.id,
                    'partner_id':partner_id,
                    #'product_uom_qty':0,
                    'price_unit':0,
                    'location_id':picking_id.picking_type_id.default_location_src_id.id,
                    #'name': product_id.default_code,
                    'date': datetime.now(),
                    'product_id': product_id.id,
                    'product_uom_id': product_id.uom_id.id,
                    'location_dest_id': warehouse_id.wh_input_stock_loc_id.id,
                    'company_id': picking_id.company_id.id,
                    #'note':'',
                    #'state': 'draft'
                    }
                    # print data
                    request.env['stock.move.line'].sudo().create(data)
                
                for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    move.sudo().update({
                    'first_weight': first_weight,
                    'second_weight': second_weight,
                    'bag_no': bag_no,
                    'tare_weight': tare_weight,
                    'init_qty': init_qty,
                    'product_id': product_id.id,
                })
                for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    move.sudo().update({
                    #'qty_done': init_qty,
                    'product_id': product_id.id,
                })
                if flag != u'False':
                    for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                        move.sudo().update({
                        'lot_id':stack_id,
                        'zone_id':zone_id
                    })
                    #picking_id.action_confirm()
                    picking_id.button_qc_assigned() #force_assign()
                    # picking_id.button_sd_validate()
                    #Finish is Done
                    gate_id.state ='closed'
                
                if second_weight > 0:
                    gate_id.time_out = datetime.now()

                if packing_id:
                    for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                        move.sudo().update({
                        'packing_id': packing_id.id
                    })
                
                mess = {
                    'message': picking_id.name,
                    'picking_id':picking_id.id,
                    }
                return json.dumps(mess)
        
        elif gate_id.picking_ids and len(gate_id.picking_ids)!= 1:
            for p in gate_id.picking_ids:
                station_ids.append(p.backorder_id.id)
            
            station_ids = request.env['stock.picking'].sudo().search([('backorder_id','in',station_ids)])
            sum_grn = isinstance(init_qty, str) and int(init_qty) or init_qty
            
            sum_station = sum(station_ids.mapped('total_init_qty'))
#             rate = sum_station and sum_grn/sum_station or 0.0
            for picking_id in gate_id.picking_ids:
                if warehouse_id != picking_id.warehouse_id:
                    picking_id.sudo().update({
                                        'warehouse_id': warehouse_id.id
                                    })
                    for move in picking_id.move_line_ids_without_package:
                        move.sudo().update({
                                            'location_dest_id': warehouse_id.wh_input_stock_loc_id.id,
                                            })
                    if picking_id.backorder_id:
                        picking_id.backorder_id.sudo().update({
                                        'warehouse_id': warehouse_id.id
                                    })
                    for move in picking_id.backorder_id.move_line_ids_without_package:
                        move.sudo().update({
                                            'location_dest_id': warehouse_id.wh_input_stock_loc_id.id,
                                            })
                picking_id.update({
                    'vehicle_no': vehicle_no,
                    'weightbridge_update': True,
                    'partner_id': partner_id,
                    'weight_scale_id': weight_scale_id,
                    'districts_id': districts_id,
                    'date_done': datetime.now(),
                })
                # print picking_id
                rate = picking_id.backorder_id.total_init_qty /sum_station
                if not picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    data = {
                    'picking_id':picking_id.id,
                    'partner_id':partner_id,
                    #'product_uom_qty':0,
                    'price_unit':0,
                    'location_id':picking_id.picking_type_id.default_location_src_id.id,
                    #'name': product_id.default_code,
                    'date': datetime.now(),
                    'product_id': product_id.id,
                    'product_uom_id': product_id.uom_id.id,
                    'location_dest_id': picking_id.picking_type_id.default_location_dest_id.id,
                    'company_id': picking_id.company_id.id,
                    #'note':'',
                    #'state': 'draft'
                    }
                    request.env['stock.move.line'].sudo().create(data)
                    
                for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    move.sudo().update({
                    'first_weight': isinstance(first_weight, str) and float(first_weight) * rate or first_weight  * rate ,
                    'second_weight': isinstance(second_weight, str) and float(second_weight) * rate or second_weight  * rate ,
                    'bag_no': isinstance(bag_no, str) and float(bag_no) * rate or bag_no  * rate , 
                    'tare_weight':isinstance(tare_weight, str) and float(tare_weight) * rate or tare_weight  * rate ,
                    'init_qty': isinstance(init_qty, str) and float(init_qty) * rate or init_qty  * rate ,
                    'weighbridge':isinstance(init_qty, str) and float(init_qty) * rate or init_qty  * rate ,
                    'product_id': product_id.id,
                })
                for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    move.sudo().update({
                    #'qty_done': isinstance(init_qty, str) and float(init_qty) * rate or init_qty  * rate ,
                    'product_id': product_id.id,
                })
                if flag != u'False':
                    for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                        move.sudo().update({
                        'lot_id':stack_id,
                        'zone_id':zone_id
                    })
                   # picking_id.action_confirm()
                    picking_id.button_qc_assigned() #force_assign()
                    # picking_id.button_sd_validate()
                    #Finish is  Done
                    gate_id.state ='closed'
                    gate_id.time_out = datetime.now()
                if packing_id:
                    for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                        move.sudo().update({
                        'packing_id': packing_id.id
                    })
                
            mess = {
                'message': picking_id.name,
                'picking_id':picking_id.id,
                }
            # print mess
            return json.dumps(mess)
            
    @http.route('/api/weight/update_gdn', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def update_gdn(self, **post):
        vehicle_no = post.get('soxe')
        first_weight = float(post.get('weight_in'))
        
        second_weight = post.get('weight_out') or 0
        if second_weight and isinstance(second_weight, str):
            second_weight = float(post.get('weight_out'))

        bag_no = post.get('num_of_bag')
        tare_weight = post.get('total_weight_of_bag')
        if tare_weight and isinstance(tare_weight, str):
            tare_weight = float(post.get('total_weight_of_bag'))

        net_weight = post.get('real_weight') or 0
        if net_weight and isinstance(net_weight, str):
            net_weight = float(post.get('real_weight'))
        
        weight_scale_id = post.get('weight_scale_id')
        
        weight_user_id = post.get('weight_user_id')
        if weight_user_id and isinstance(weight_user_id, str):
            weight_user_id = int(post.get('weight_user_id'))

        reweighing_reason = post.get('reweighing_reason')

        # product_id = post.get('product_id')
        # if product_id and isinstance(product_id, str):
        #     product_id = int(post.get('product_id'))
        # if not product_id:
        #     mess = {
        #         'err_code': 'SUD23-00000',
        #         'message': 'Product does not exist.',
        #         }
        #     return json.dumps(mess)
        # product_id = request.env['product.product'].sudo().browse(product_id)

        weight_scale_id = request.env['res.users'].sudo().search([('login','=',weight_scale_id)])

        flag = post.get('flag')
                                
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))
        if not warehouse_id:
            mess = {
                'err_code': 'SUD23-00000',
                'message': 'Warehouse does not exist.',
                }
            return json.dumps(mess)
        warehouse_id = request.env['stock.warehouse'].sudo().browse(warehouse_id)

        gate_id = post.get('gate_id')
        if gate_id and isinstance(gate_id, str):
            gate_id = int(post.get('gate_id'))
        if not gate_id:
            mess = {
                'err_code': 'SUD23-00000',
                'message': 'Gate does not exist.',
                }
            return json.dumps(mess)
        
        gate_id = request.env['ned.security.gate.queue'].sudo().browse(gate_id)

        if not gate_id.picking_ids:
                for _do in gate_id.delivery_id:
                    if _do:
                        if _do.type == 'Sale':
                            picking_type_id = 0
                            if _do.contract_id.type != 'local':
                                picking_type_id = warehouse_id.out_type_id
                            else:
                                picking_type_id = warehouse_id.out_type_local_id

                            if not picking_type_id:
                                raise UserError(_('Need to define Picking Type for this transaction'))

                            if not _do.picking_id:
                                var = {'name': '/',
                                        'picking_type_id': picking_type_id.id or False,
                                        'scheduled_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                                        'origin': _do.name,
                                        'partner_id': _do.partner_id.id or False,
                                        'picking_type_code': picking_type_id.code or False,
                                        'location_id': picking_type_id.default_location_src_id.id or False,
                                        'vehicle_no': _do.trucking_no or '',
                                        'trucking_id': gate_id.trucking_id.id or False,
                                        'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                        'delivery_id': _do.id,
                                        'security_gate_id': gate_id.id,
                                       # 'min_date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                                       }
                                picking_id = request.env['stock.picking'].with_user(weight_user_id).create(var)
                                _do.picking_id = picking_id.id
                            else:
                                picking_id = _do.picking_id.with_user(weight_user_id).update({
                                        'security_gate_id': gate_id.id,
                                        'vehicle_no': _do.trucking_no or '',
                                        'trucking_id': gate_id.trucking_id.id or False,
                                    })

        gate_id.license_plate = vehicle_no
        gate_id.first_weight = first_weight
        gate_id.estimated_bags = bag_no
        gate_id.tare_weight = tare_weight

        if gate_id.picking_ids:
            gate_id.picking_ids.weight_scale_id = weight_scale_id

        if second_weight == 0 and first_weight > 0 and not gate_id.time_in: 
            gate_id.time_in = datetime.now()
            
        mess = {
            'err_code': 'SUD23-00000',
            'message': 'First weight update successfully',
            # 'picking_id':gate_id.picking_ids.id,
            }

        #Update vehicle_no if change
        if not gate_id.license_plate == vehicle_no:
            for item in gate_id.nvs_nls_id:
                do_item = request.env['delivery.order'].sudo().search([('security_gate_id','=',gate_id.id),('contract_id','=',item.id)],limit =1)
                if do_item:
                    do_item.trucking_no = vehicle_no
                    for pick in do_item.picking_id:
                        pick.vehicle_no = vehicle_no
                        # print(pick.vehicle_no,do_item.trucking_no)
            
        if second_weight > 0:
            gate_id.estimated_bags = bag_no
            gate_id.tare_weight = tare_weight
            gate_id.second_weight = second_weight
            gate_id.net_weight = net_weight
            gate_id.time_out = datetime.now()

        lot_allocations = []
        for p in gate_id.delivery_id:
            lot_allocations.append(p.id)
        lot_allocate = request.env['lot.stack.allocation'].sudo().search([('delivery_id','in',lot_allocations)])
        sum_lot_allocation = sum(lot_allocate.mapped('quantity')) or 0
        # print(sum_lot_allocation)
        
        if gate_id.picking_ids and second_weight > 0 and net_weight > 0: 
            for do_id in gate_id.delivery_id:
                do_id.with_user(weight_user_id).update({
                                'trucking_no': vehicle_no,
                            })
                for pick in do_id.picking_id:
                    pick.with_user(weight_user_id).update({
                                    'vehicle_no': vehicle_no,
                                })
                    i = 0
                    allocation_obj = request.env['lot.stack.allocation'].sudo().search([('delivery_id','=',do_id.id)], order="id asc")
                    # print(allocation_obj)
                    if not allocation_obj:
                        mess = {
                                'err_code': 'SUD23-00002',
                                'message': 'Please check Product line of ' + pick.name + ' and Lot Allocation maybe not allocated yet',
                                }
                        return json.dumps(mess)
                    elif len(pick.move_line_ids_without_package) != len(allocation_obj):
                        mess = {
                                'err_code': 'SUD23-00002',
                                'message': 'Please check Product line of ' + pick.name + ' and Lot Allocation line of ' + allocation_obj[i].delivery_id.name,
                                }
                        return json.dumps(mess)
                    else:
                        for line in pick.move_line_ids_without_package:
                            percen = allocation_obj[i].quantity/sum_lot_allocation
                            # print(percen)
                            i += 1
                            line.with_user(weight_user_id).update({
                                'init_qty': net_weight * percen,
                                'tare_weight': tare_weight * percen or 0,
                                'description_picking': reweighing_reason,
                            })
                    pick.with_user(weight_user_id).update({
                                                            'date_done': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                                                            })

            gate_id.state ='closed'

            mess = {
                'err_code': 'SUD23-00000',
                'message': 'Second weight update successfully',
                # 'picking_id':gate_id.delivery_id.picking_id.id,
                }

        return json.dumps(mess)


    # Nhap Delivery Order BCCE de tao BCCE-GDN - hien tai chi ap dung cho kho BCCE
    @http.route('/api/weight/create_bcce_gdn', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def create_bcce_gdn(self, **post):
        vehicle_no = post.get('soxe')
        first_weight = post.get('weight_in')
        second_weight = post.get('weight_out')
        bag_no = post.get('num_of_bag')
        tare_weight = post.get('total_weight_of_bag')
        init_qty = post.get('real_weight')
        do_id = post.get('do_id')
        flag = post.get('flag')
        type_transfer = post.get('type_transfer')
        product_id = post.get('product_id')
        packing_id = post.get('packing_id')
        gate_id = post.get('gate_id')
        if not gate_id:
            mess = {
                'message': 'Gate does not exist.',
                }
            return json.dumps(mess)
        
        if gate_id and isinstance(gate_id, str):
            gate_id = int(post.get('gate_id'))
        if not do_id:
            mess = {
                'message': 'Delivery does not exist.',
                }
            return json.dumps(mess)
        gate_id = request.env['ned.security.gate.queue'].sudo().browse(gate_id)
        if gate_id.type_transfer == u'out':
            if do_id and isinstance(do_id, str):
                do_id = int(do_id)
            if flag != u'False':
                zone_id = post.get('zone_id')
                stack_id = post.get('stack_id')
                if zone_id and isinstance(zone_id, str):
                    zone_id = int(post.get('zone_id'))
                if stack_id and isinstance(stack_id, str):
                    stack_id = int(post.get('stack_id'))
                zone_id,stack_id = self.create_stack(zone_id, stack_id)
            
                if not stack_id:
                    if not zone_id:
                        mess = {
                        'message': 'Zone does not exist.',
                        }
                        return json.dumps(mess)
            if product_id and isinstance(product_id, str):
                product_id = int(post.get('product_id'))
            if packing_id and isinstance(packing_id, str):
                packing_id = int(post.get('packing_id'))
                
            if not product_id:
                mess = {
                    'message': 'Product does not exist.',
                    }
                return json.dumps(mess)
    
            delivery_id = request.env['delivery.order'].sudo().browse(do_id)
            product_id = request.env['product.product'].sudo().browse(product_id)
            if packing_id:
                packing_id = request.env['ned.packing'].sudo().browse(packing_id)
            pick_id = False
            if not delivery_id:
                mess = {
                    'message': 'Delivery Order does not exist.',
                    }
                return json.dumps(mess)
            elif delivery_id:
                pick_id = delivery_id.sudo().create_picking()
            if pick_id:
                pick_id.security_gate_id = gate_id.id
                delivery_id.picking_id = pick_id.id
                pick_id.sudo().update({
                    'zone_id': False,
                    'vehicle_no':vehicle_no,
                    'date_done':datetime.now()
                    })
                for move in pick_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    move.sudo().update({
                        'first_weight': first_weight,
                        'second_weight': second_weight,
                        'bag_no': bag_no,
                        'tare_weight': tare_weight,
                        'init_qty': init_qty,
                        'packing_id': packing_id.id
                    })
                #for move in pick_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                #    move.sudo().update({
                #        'qty_done': init_qty,
                #    })
                if flag != u'False':
                    for move in pick_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                        move.sudo().update({
                        'lot_id':stack_id,
                        'zone_id':zone_id
                    })
                    pick_id.do_new_transfer()
                    pick_id.action_done()
                    gate_id.state ='closed'
        else:
            if do_id and isinstance(do_id, str):
                do_id = int(do_id)
            if flag != u'False':
                zone_id = post.get('zone_id')
                stack_id = post.get('stack_id')
                if zone_id and isinstance(zone_id, str):
                    zone_id = int(post.get('zone_id'))
                if stack_id and isinstance(stack_id, str):
                    stack_id = int(post.get('stack_id'))
                zone_id,stack_id = self.create_stack(zone_id, stack_id)
            
                if not stack_id:
                    if not zone_id:
                        mess = {
                        'message': 'Zone does not exist.',
                        }
                        return json.dumps(mess)
    
            delivery_id = request.env['delivery.order'].sudo().browse(do_id)
            pick_id = False
            if not delivery_id:
                mess = {
                    'message': 'Delivery Order does not exist.',
                    }
                return json.dumps(mess)
            elif delivery_id:
                picking_out_id = request.env['stock.picking'].sudo().search([('delivery_order_id','=',delivery_id.id)],limit =1)
                if picking_out_id:
                    pick_id = request.env['stock.picking'].sudo().search([('backorder_id','=',picking_out_id.id)],limit =1)
                else:
                    mess = {
                        'message': 'Picking OUT does not exist.',
                        }
                    return json.dumps(mess)
            if not pick_id:
                mess = {
                        'message': 'Picking IN does not exist.',
                        }
                return json.dumps(mess)
            product_id = request.env['product.product'].sudo().browse(product_id)
            if packing_id:
                packing_id = request.env['ned.packing'].sudo().browse(packing_id)
                
            if pick_id:
                pick_id.security_gate_id = gate_id.id
                pick_id.sudo().update({
                    'zone_id': False,
                    'vehicle_no':vehicle_no,
                    'date_done':datetime.now()
                    })
                for move in pick_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                    move.sudo().update({
                        'first_weight': first_weight,
                        'second_weight': second_weight,
                        'bag_no': bag_no,
                        'tare_weight': tare_weight,
                        'init_qty': init_qty,
                        'packing_id': packing_id.id
                    })
                #for move in pick_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                #    move.sudo().update({
                #        'qty_done': init_qty,
                #    })
                if flag != u'False':
                    for move in pick_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                        move.sudo().update({
                        'lot_id':stack_id,
                        'zone_id':zone_id
                    })
                    #pick_id.action_confirm()
                    pick_id.button_qc_assigned() #force_assign()
                    # picking_id.button_sd_validate()
                    #Hoan thành Là Done
                    gate_id.state ='closed'
        mess = {
            'message': 'Successful!',
            }
        return json.dumps(mess)

