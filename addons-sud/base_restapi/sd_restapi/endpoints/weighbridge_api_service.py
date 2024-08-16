# -*- coding: utf-8 -*-

from marshmallow import fields
from werkzeug.exceptions import BadRequest

from odoo.addons.base_rest import restapi
from odoo.addons.component.core import Component
from odoo.addons.datamodel.core import Datamodel

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

from odoo.http import request, json
from odoo import SUPERUSER_ID
from datetime import datetime as dtime, timedelta

###========= Datamodel INPUT =========###
class SecurityGateSearchParam(Datamodel):
    _name = "security.gate.search.param"
    _inherit = "masterdata.search.param"
    
    warehouse_id = fields.String(load_default="1,22")
    
###========= Datamodel OUTPUT =========###
class SecurityGateShortInfo(Datamodel):
    _name = "security.gate.short.info"
    # _inherit = "masterdata.short.info"

    id = fields.Integer()
    name = fields.String()
    warehouse_id = fields.Integer()
    supplier_id = fields.Integer()
    customer_id = fields.Integer()
    vehicle = fields.String()
    first_cont = fields.String(allow_none=True)
    last_cont = fields.String(allow_none=True)
    estimated_bags = fields.Integer()
    parking_order = fields.Integer()
    code = fields.String()
    picking_name = fields.String()
    state = fields.String()
    default_code = fields.String()
    product_id = fields.Integer()
    type_transfer = fields.String()
    districts_id = fields.Integer(allow_none=True)
    packing_id = fields.Integer()
    time_out = fields.DateTime(allow_none=True)
    estate_name = fields.String()

class SecurityGateShortInfoExt(Datamodel):
    _name = "security.gate.short.infoext"
    id = fields.Integer()
    name = fields.String()

### ========================================================= ###
class WeighbridgeApiService(Component):
    _inherit = "base.rest.service"
    _name = "weighbridge.api.service"
    _usage = "weighbridge"
    _collection = "sucden.restapi.services"
    _description = """
        Weighbridge New API Services
        Services developed with the new api provided by IT Team - SUCDEN VN
    """
### Get Security Gate ###
    @restapi.method(
        [(["/security_gate/list"], "GET")],
        input_param=restapi.Datamodel("security.gate.search.param"),
        output_param=restapi.Datamodel("security.gate.short.info", is_list=True),
        # output_param=restapi.CerberusListValidator("_output_sec_gate_schema"),
        auth="api_key",
    )
    def security_list(self, security_gate_search_param):
        """
        Search for Security Gate
        @param: Input ID or Name or Warehouse ID
        @return: Return a list of Security Gate follow parameters
        """
        domain = [('arrivial_time','>=',((dtime.today()-timedelta(days=4)).strftime('%Y-%m-%d')))]
        if security_gate_search_param.name:
            domain.append(("name", "like", security_gate_search_param.name))
        if security_gate_search_param.id:
            domain.append(("id", "=", security_gate_search_param.id))
        array = []
        if security_gate_search_param.warehouse_id and isinstance(security_gate_search_param.warehouse_id, str):
            array = [int(x) for x in security_gate_search_param.warehouse_id.split(",")]
            domain.append(("warehouse_id", "in", array))
        res = []
        SecurityGateShortInfo = self.env.datamodels["security.gate.short.info"]
        if len(array) == 1:
            for p in self.env["ned.security.gate.queue"].search(domain):
                get_timeout = None if p.time_out == False else dtime.strptime(str(p.time_out), "%Y-%m-%d %H:%M:%S.%f").strftime(DATETIME_FORMAT)
                res.append(SecurityGateShortInfo(id=p.id, name=p.name, warehouse_id=p.warehouse_id, supplier_id=p.supplier_id, customer_id=p.customer_id, 
                                                vehicle=p.license_plate, first_cont='' if p.first_cont == False else p.first_cont, last_cont='' if p.last_cont == False 
                                                else p.last_cont, estimated_bags=p.estimated_bags,
                                                parking_order=p.parking_order, code=p.picking_type_id.code, picking_name=p.picking_type_id.name, 
                                                state=p.state, default_code=p.product_ids.default_code, product_id=p.product_ids.id, type_transfer=p.type_transfer,
                                                districts_id=p.districts_id, packing_id=p.packing_id, 
                                                time_out=get_timeout))
        else: # Thêm estate_name cho riêng India
            for p in self.env["ned.security.gate.queue"].search(domain):
                get_timeout = None if p.time_out == False else dtime.strptime(str(p.time_out), "%Y-%m-%d %H:%M:%S.%f").strftime(DATETIME_FORMAT)
                res.append(SecurityGateShortInfo(id=p.id, name=p.name, warehouse_id=p.warehouse_id, supplier_id=p.supplier_id, customer_id=p.customer_id, 
                                                vehicle=p.license_plate, first_cont='' if p.first_cont == False else p.first_cont, last_cont='' if p.last_cont == False 
                                                else p.last_cont, estimated_bags=p.estimated_bags,
                                                parking_order=p.parking_order, code=p.picking_type_id.code, picking_name=p.picking_type_id.name, 
                                                state=p.state, default_code=p.product_ids.default_code, product_id=p.product_ids.id, type_transfer=p.type_transfer,
                                                districts_id=p.districts_id, packing_id=p.packing_id, 
                                                time_out=get_timeout,estate_name=p.estate_name))
        return res
    
### CREATE STACK, BUILDING ###
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

### UPDATE GRN ###
    @restapi.method(
        [(["/stock_picking/<int:id>"], "GET")],
        output_param=restapi.CerberusValidator("_get_picking_schema"),
        auth="api_key",
    )

    def get_picking(self, _id):
        return {"id": self.env["stock.picking"].browse(_id).id,
                "name": self.env["stock.picking"].browse(_id).name}

    def _get_picking_schema(self):
        return {"id": {"type": "integer"},
                "name": {"type": "string"}}
        
    def _input_picking_schema(self):
        return {"gate_id": {"type": "integer"},
                "districts_id": {"type": "integer"},
                "packing_id": {"type": "integer"},
                "partner_id": {"type": "integer"},
                "product_id": {"type": "integer"},
                "warehouse_id": {"type": "integer"},
                "soxe": {"type": "string"},
                "weight_in": {"type": "float"},
                "weight_out": {"type": "float", "required": False},
                "tare_weight": {"type": "float", "required": False},
                "init_qty": {"type": "float", "required": False},
                "num_of_bag": {"type": "integer", "required": False},
                "weight_scale_id": {"type": "string"},
                "weight_user_id": {"type": "integer"},
                "wb_flag": {"type": "string"},
                "stack_type": {"type": "string", "required": False},
                "reweighing_reason": {"type": "string"},
                "zone_id": {"type": "integer"},
                "stack_id": {"type": "integer"},
                "building_id": {"type": "integer"},
                "total_weight_of_bag": {"type": "float", "required": False},
                "real_weight": {"type": "float", "required": False}
                }
        
    def _output_picking_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
                'picking_name': {"type": "string"},
                'picking_id': {"type": "integer"},
                'stack_id': {"type": "integer"},
                'stack_name': {"type": "string"}
                }

    @restapi.method(
        [(["/stock_picking/create_update_grn"], "POST")],
        # input_param=restapi.Datamodel("stock.picking.grn.intput"),
        input_param=restapi.CerberusValidator("_input_picking_schema"),
        output_param=restapi.CerberusValidator("_output_picking_schema"),
        auth="api_key",
    )
    def create_update_grn(self, **params):
        vehicle_no = params.get('soxe')
        first_weight = params.get('weight_in')
        second_weight = params.get('weight_out')
        bag_no = params.get('num_of_bag')
        tare_weight = params.get('total_weight_of_bag')
        init_qty = params.get('real_weight')
        weight_scale_id = params.get('weight_scale_id')
        weight_scale_id = self.env['res.users'].sudo().search([('login','=',weight_scale_id)])
        
        weight_user_id = params.get('weight_user_id')
        if weight_user_id and isinstance(weight_user_id, str):
            weight_user_id = int(params.get('weight_user_id'))

        product_id = params.get('product_id')
        if product_id and isinstance(product_id, str):
            product_id = int(params.get('product_id'))
        if not product_id:
            return {
                    'status_code': 'SUD23-404',
                    'message': 'Product does not exist.',
                    }

        warehouse_id = params.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(params.get('warehouse_id'))
        if not warehouse_id:
            return {
                    'status_code': 'SUD23-404',
                    'message': 'Warehouse does not exist.',
                    }

        flag = params.get('wb_flag')
        stack_type = params.get('stack_type')
        reweighing_reason = params.get('reweighing_reason')
    
        warehouse_id = request.env['stock.warehouse'].sudo().browse(warehouse_id)
        product_id = request.env['product.product'].sudo().browse(product_id)

        partner_id = params.get('partner_id')
        if partner_id and isinstance(partner_id, str):
            partner_id = int(params.get('partner_id'))

        packing_id = params.get('packing_id')
        if packing_id and isinstance(packing_id, str):
            packing_id = int(params.get('packing_id'))
        if packing_id:
            packing_id = request.env['ned.packing'].sudo().browse(packing_id)
                    
        districts_id = params.get('districts_id')
        if districts_id and isinstance(districts_id, str):
            districts_id = int(params.get('districts_id'))
            
        gate_id = params.get('gate_id')
        if gate_id and isinstance(gate_id, str):
            gate_id = int(params.get('gate_id'))
        if not gate_id:
            return {
                    'status_code': 'SUD23-404',
                    'message': 'Gate does not exist.',
                    }
        
        gate_id = self.env['ned.security.gate.queue'].sudo().browse(gate_id)
        gate_id.sudo().write({
                'license_plate': vehicle_no,
                'supplier_id': partner_id,
            })

        if not gate_id.time_in:
            gate_id.sudo().write({
                    'time_in': dtime.now()
                })

        if gate_id.picking_ids and len(gate_id.picking_ids)== 1:
            picking_id = gate_id.picking_ids and gate_id.picking_ids[0]
            if not picking_id:
                return {
                        'status_code': 'SUD23-404',
                        'message': 'Picking does not exist.',
                        }
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
                        'date_done': dtime.now(),
                    })
                if not picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id) and len(picking_id.move_line_ids_without_package) == 0:
                    data = {
                        'picking_id':picking_id.id,
                        'partner_id':partner_id,
                        'price_unit':0,
                        'location_id':picking_id.picking_type_id.default_location_src_id.id,
                        'date': dtime.now(),
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

                # print(len(picking_id.kcs_line))
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
                        zone_id = params.get('zone_id')
                        stack_id = params.get('stack_id')
                        building_id = params.get('building_id')
                        if zone_id and isinstance(zone_id, str):
                            zone_id = int(params.get('zone_id'))
                        if stack_id and isinstance(stack_id, str):
                            stack_id = int(params.get('stack_id'))
                        if building_id and isinstance(building_id, str):
                            building_id = int(params.get('building_id'))

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
                                return {
                                        'status_code': 'SUD23-404',
                                        'message': 'Zone does not exist.',
                                        }

                        for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                            move.with_user(weight_user_id).update({
                                'lot_id':stack_id,
                                'zone_id':zone_id
                            })
                        picking_id.button_qc_assigned()
                        gate_id.state ='closed'
                        gate_id.time_out = dtime.now()

                    if packing_id:
                        for move in picking_id.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id):
                            move.with_user(weight_user_id).update({
                                'packing_id': packing_id.id
                            })
                    
                    if flag == u'True':
                        # print(stack_id,picking_id.move_line_ids_without_package.lot_id.name)
                        return {
                                'status_code': 'SUD23-200',
                                'message': 'Weighment completed!',
                                'picking_name': picking_id.name,
                                'picking_id':picking_id.id,
                                'stack_id':stack_id,
                                'stack_name':picking_id.move_line_ids_without_package.lot_id.name,
                                }
                    else:
                        return {
                                'status_code': 'SUD23-200',
                                'message': 'Update GRN completed!',
                                'picking_name': picking_id.name,
                                'picking_id':picking_id.id,
                                }
                else:
                    return {
                            'status_code': 'SUD23-113',
                            'message': 'This GRN has been done at QC step. Can not update!',
                            }

    def _output_gdn_picking_schema(self):
        return {
                'status_code': {"type": "string"},
                'message': {"type": "string"},
               }
### CREATE UPDATE GDN ###
    @restapi.method(
        [(["/stock_picking/create_update_gdn"], "POST")],
        input_param=restapi.CerberusValidator("_input_picking_schema"),
        output_param=restapi.CerberusValidator("_output_gdn_picking_schema"),
        auth="api_key",
    )
    def update_gdn(self, **params):
        vehicle_no = params.get('soxe')
        first_weight = float(params.get('weight_in'))
        
        second_weight = params.get('weight_out') or 0
        if second_weight and isinstance(second_weight, str):
            second_weight = float(params.get('weight_out'))

        bag_no = params.get('num_of_bag')
        tare_weight = params.get('total_weight_of_bag')
        if tare_weight and isinstance(tare_weight, str):
            tare_weight = float(params.get('total_weight_of_bag'))

        net_weight = params.get('real_weight') or 0
        if net_weight and isinstance(net_weight, str):
            net_weight = float(params.get('real_weight'))
        
        weight_scale_id = params.get('weight_scale_id')
        
        weight_user_id = params.get('weight_user_id')
        if weight_user_id and isinstance(weight_user_id, str):
            weight_user_id = int(params.get('weight_user_id'))

        reweighing_reason = params.get('reweighing_reason')

        weight_scale_id = request.env['res.users'].sudo().search([('login','=',weight_scale_id)])

        flag = params.get('wb_flag')
                                
        warehouse_id = params.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(params.get('warehouse_id'))
        if not warehouse_id:
            mess = {
                'status_code': 'SUD23-404',
                'message': 'Warehouse does not exist.',
                }
            return mess
        warehouse_id = request.env['stock.warehouse'].sudo().browse(warehouse_id)

        gate_id = params.get('gate_id')
        if gate_id and isinstance(gate_id, str):
            gate_id = int(params.get('gate_id'))
        if not gate_id:
            mess = {
                'status_code': 'SUD23-404',
                'message': 'Gate does not exist.',
                }
            return mess
        
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
                                mess = {
                                    'status_code': 'SUD23-204',
                                    'message': 'Need to define Picking Type for this transaction',
                                    }
                                return mess                                

                            if not _do.picking_id:
                                var = {'name': '/',
                                        'picking_type_id': picking_type_id.id or False,
                                        'scheduled_date': dtime.now().strftime(DATETIME_FORMAT),
                                        'origin': _do.name,
                                        'partner_id': _do.partner_id.id or False,
                                        'picking_type_code': picking_type_id.code or False,
                                        'location_id': picking_type_id.default_location_src_id.id or False,
                                        'vehicle_no': _do.trucking_no or '',
                                        'trucking_id': gate_id.trucking_id.id or False,
                                        'location_dest_id': picking_type_id.default_location_dest_id.id or False,
                                        'delivery_id': _do.id,
                                        'security_gate_id': gate_id.id,
                                       # 'min_date': dtime.now().strftime(DATETIME_FORMAT)
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
            gate_id.time_in = dtime.now()
            
        mess = {
            'status_code': 'SUD23-200',
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
            gate_id.time_out = dtime.now()

        lot_allocations = []
        for p in gate_id.delivery_id:
            lot_allocations.append(p.id)
        lot_allocate = request.env['lot.stack.allocation'].sudo().search([('delivery_id','in',lot_allocations)])
        sum_lot_allocation = sum(lot_allocate.mapped('quantity')) or 0
        print(sum_lot_allocation)
        
        allocation_dict = {}
        if gate_id.picking_ids and second_weight > 0 and net_weight > 0: 
            for do_id in gate_id.delivery_id:
                do_id.with_user(weight_user_id).update({
                                'trucking_no': vehicle_no,
                            })
                for pick in do_id.picking_id:
                    pick.with_user(weight_user_id).update({
                                    'vehicle_no': vehicle_no,
                                })
                    allocation_obj = request.env['lot.stack.allocation'].sudo().search([('delivery_id','=',do_id.id)], order="id asc")
                    # print(allocation_obj)
                    if not allocation_obj:
                        mess = {
                                'status_code': 'SUD23-204',
                                'message': 'Please check Product line of ' + pick.name + ' and Lot Allocation maybe not allocated yet',
                                }
                        return mess
                    elif len(pick.move_line_ids_without_package) != len(allocation_obj):
                        mess = {
                                'status_code': 'SUD23-204',
                                'message': 'Please check Product line of ' + pick.name + ' and Lot Allocation line of ' + allocation_obj[i].delivery_id.name,
                                }
                        return mess
                    else:
                        for line in pick.move_line_ids_without_package:
                            for item in allocation_obj.filtered(lambda x: x.stack_id.id == line.lot_id.id):
                                # print(item)
                                line.with_user(weight_user_id).update({
                                    'init_qty': net_weight * (item.quantity/sum_lot_allocation),
                                    'tare_weight': tare_weight * (item.quantity/sum_lot_allocation) or 0,
                                    'description_picking': reweighing_reason,
                                })
                    pick.with_user(weight_user_id).update({
                                                            'date_done': dtime.now().strftime(DATETIME_FORMAT)
                                                            })

            gate_id.state ='closed'

            mess = {
                'status_code': 'SUD23-200',
                'message': 'Second weight update successfully',
                # 'picking_id':gate_id.delivery_id.picking_id.id,
                }

        return mess
