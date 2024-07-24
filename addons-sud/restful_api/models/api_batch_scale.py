# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, http, fields, models, _
import odoo.addons.decimal_precision as dp
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools import append_content_to_html, float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare, float_round
# # from odoo.http import http
from odoo import SUPERUSER_ID
# from odoo.addons.website import slug, unslug
from odoo.http import route, request, json
# from models import JWTAuth
from odoo.tools.misc import formatLang
import time
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
utr = [' ',',','.','/','<','>','?',':',';','"',"'",'[','{','}',']','=','+','-','_',')','(','*','&','^','%','$','#','@','!','`','~','|']


class APISearch(http.Controller):
    
    @http.route('/api/weightscale/mrp_production_list', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def mrp_production_list(self, **post):
        warehouse_id = int(post.get('warehouse_id'))
        sql_ext1 = ''
        if warehouse_id:
            sql_ext1 = 'AND mrp.warehouse_id = %s'%(warehouse_id)
        sql = '''SELECT mrp.id, mrp.name, mbom.code bom_name, pcat.name grade_name, mrp.batch_type, CAST(mrp.date_planned_start AS TEXT),
                    mrp.product_issued, mrp.product_received, mrp.product_balance, mrp.state, mrp.warehouse_id
                 FROM mrp_production mrp
                 LEFT JOIN mrp_bom mbom ON mbom.id=mrp.bom_id
                 LEFT JOIN product_category pcat ON mrp.grade_id=pcat.id
                 WHERE mrp.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') %s; '''%(sql_ext1)

        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)


    @http.route('/api/weightscale/get_operation_result', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def get_operation_result(self, **post):
        warehouse_id = int(post.get('warehouse_id'))
        sql_ext1 = ''
        if warehouse_id:
            sql_ext1 = 'AND mrp.warehouse_id = %s'%(warehouse_id)
        # sql = '''SELECT distinct mrp_result.pending_grn, spk.sp_name, mrp_result.product_qty, 
        #             mrp_result.production_weight, spk.state_kcs, mrp_result.production_id, mrp_result.mrp_result_id,
        #             mrp_result.product_id, mrp_result.packing_id, mrp_result.zone_id, mrp_result.qty_bags,
        #             mrp_result.notes, mrp_result.tare_weight, mrp_result.operation_result_id, mrp_result.scale_grp_id 
        #         FROM (SELECT id mrp_result_id, picking_id, product_id, operation_result_id, si_id, production_id, 
        #          packing_id, zone_id, notes, pending_grn, qty_bags, production_weight, product_qty, tare_weight, scale_grp_id
        #         FROM mrp_operation_result_produced_product) mrp_result
        #         LEFT JOIN (SELECT id sp_id, name sp_name, origin, state sp_state, state_kcs, picking_type_code 
        #                    FROM stock_picking) spk
        #                     ON mrp_result.picking_id=spk.sp_id
        #         LEFT JOIN (SELECT id mrp_id, name mrp_name, state mrp_state, warehouse_id, create_date
        #                    FROM mrp_production) mrp 
        #                     ON mrp.mrp_id=mrp_result.production_id
        #         WHERE mrp.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') %s;'''%(sql_ext1) 
        sql = '''SELECT * FROM
                (SELECT distinct mrp_result.pending_grn, spk.sp_name, mrp_result.state, mrp_result.product_qty, 
                    mrp_result.production_weight, spk.state_kcs, mrp_result.production_id, mrp_result.mrp_result_id,
                    mrp_result.product_id, mrp_result.packing_id, mrp_result.zone_id, mrp_result.qty_bags, mrp_result.notes, 
                    mrp_result.tare_weight, mrp_result.operation_result_id, mrp_result.scale_grp_id, mrp_result.create_date  
                FROM (SELECT id mrp_result_id, picking_id, product_id, operation_result_id, si_id, production_id, state,
                 packing_id, zone_id, notes, pending_grn, qty_bags, production_weight, product_qty, tare_weight, scale_grp_id, 
                 CAST(create_date at time zone 'utc' at time zone 'ict' AS TEXT) AS create_date 
                FROM mrp_operation_result_produced_product) mrp_result
                LEFT JOIN (SELECT id sp_id, name sp_name, origin, state sp_state, state_kcs, picking_type_code 
                           FROM stock_picking) spk
                            ON mrp_result.picking_id=spk.sp_id
                LEFT JOIN (SELECT id mrp_id, name mrp_name, state mrp_state, warehouse_id, create_date
                           FROM mrp_production) mrp 
                            ON mrp.mrp_id=mrp_result.production_id
                WHERE mrp.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month') %s) grp
                LEFT JOIN (SELECT id mor_id, name mor_name FROM mrp_operation_result) mor
                            ON mor.mor_id=grp.operation_result_id;'''%(sql_ext1)
                            
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                'Result': result
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/weightscale/get_scale_lines', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def get_scale_lines(self):
        sql = '''SELECT CAST(mrp_scale.create_date at time zone 'utc' at time zone 'ict' AS TEXT) AS create_date, mrp_scale.usr_api_create, 
                        mrp_scale.product_id, mrp_scale.packing_id, mrp_scale.weight_scale, mrp_scale.bag_no, mrp_scale.tare_weight, 
                        mrp_scale.net_weight, mrp_scale.operation_result_id, mrp_scale.id, mrp_scale.shift_name, mrp_scale.packing_branch_id, 
                        mrp_scale.pallet_weight, mrp_scale.lining_bag::int, mrp_scale.scale_grp_id, mrp_scale.scale_grp_line_id, 
                        mrp_scale.picking_scale_id, mrp_scale.scale_gip_id, mrp_scale.scale_gip_line_id, mrp_scale.old_weight, 
                        mrp_scale.bag_code, mrp_scale.state_scale
                    FROM mrp_operation_result_scale mrp_scale
                    LEFT JOIN mrp_operation_result_produced_product mrp_pp ON mrp_pp.operation_result_id = mrp_scale.operation_result_id
                    LEFT JOIN mrp_production mrp on mrp.id = mrp_pp.production_id
                    LEFT JOIN stock_picking sp ON sp.id=mrp_scale.picking_scale_id
                    WHERE (mrp_pp.state='draft' AND mrp.state='confirmed') OR (sp.state_kcs='waiting' AND sp.state not in ('done','cancel')) 
                        Order by mrp_scale.id'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/weightscale/test_create_mor', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def test_create_mor(self, **post):
        flag = post.get('flag')
        warehouse_id = post.get('warehouse_id')

        production_shift = post.get('production_shift')

        user_import_id = post.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(post.get('user_import_id'))

        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))
        production_id = post.get('production_id')
        if production_id and isinstance(production_id, str):
            production_id = int(post.get('production_id'))        

        pending_grp_name = post.get(u'pending_grp_name')
        
        pending_grp_obj = request.env['mrp.operation.result.produced.product'].sudo().search([('pending_grn','=',pending_grp_name)])

        user = request.env['res.users'].sudo().search([('id', '=', user_import_id)])
        
        if not pending_grp_obj.operation_result_id: # and flag == u'Create'
            vals = {'end_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'start_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'production_shift': production_shift,
                    'create_uid': user_import_id,
                    'user_import_id': user_import_id,
                    'date_result': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'production_id': production_id,
                    'warehouse_id': warehouse_id}

            result_id = request.env['mrp.operation.result'].with_user(user_import_id).create(vals)
            # result_id = request.env['mrp.operation.result'].sudo(user).create(vals)

    @http.route('/api/weightscale/get_users_list', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def get_users_list(self):
        sql = '''SELECT rp.name, rp.email, ru.id From res_users ru Join res_partner rp On ru.partner_id=rp.id
                    WHERE ru.login = 'admin' OR rp.partner_code like '%NED%'  
                    or (rp.is_supplier_coffee = False and rp.is_customer_coffee = False)'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    def _get_numeric(self, number):
        if number and isinstance(number, str):
            new_number = float(number) or 0.0
            return new_number

    @http.route('/api/weightscale/create_production_result', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def create_production_result(self, **post):
        flag = post.get('flag')
        scale_no = post.get('scale_no')
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))
        production_id = post.get('production_id')
        if production_id and isinstance(production_id, str):
            production_id = int(post.get('production_id'))        
        product_id = post.get('product_id')
        if product_id and isinstance(product_id, str):
            product_id = int(post.get('product_id'))
        packing_id = post.get('packing_id')
        if packing_id and isinstance(packing_id, str):
            packing_id = int(post.get('packing_id'))
        pending_grp_name = post.get(u'pending_grp_name')
        zone_id = post.get('zone_id')
        if zone_id and isinstance(zone_id, str):
            zone_id = int(post.get('zone_id'))

        contract = post.get(u'contract')
        notes = post.get(u'notes')

        scale_grp_id = post.get('scale_grp_id')
        if scale_grp_id and isinstance(scale_grp_id, str):
            scale_grp_id = int(post.get('scale_grp_id'))
        scale_grp_line_id = post.get('scale_grp_line_id')
        if scale_grp_line_id and isinstance(scale_grp_line_id, str):
            scale_grp_line_id = int(post.get('scale_grp_line_id'))
        # print(scale_grp_line_id)

        scale_packing_id = post.get('scale_packing_id')
        if scale_packing_id and isinstance(scale_packing_id, str):
            scale_packing_id = int(post.get('scale_packing_id'))
        scale_tare_weight = self._get_numeric(post.get('scale_tare_weight'))
        scale_basis_weight = self._get_numeric(post.get('scale_basis_weight'))
        scale_net_weight = self._get_numeric(post.get('scale_net_weight'))

        production_shift = post.get('production_shift')
        shift_name = post.get('shift_name')

        user_import_id = post.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(post.get('user_import_id'))

        packing_branch_id = post.get('packing_branch_id')
        if packing_branch_id and isinstance(packing_branch_id, str):
            packing_branch_id = int(post.get('packing_branch_id'))

        pallet_weight = self._get_numeric(post.get('pallet_weight'))
               
        lining_bag = str(post.get('lining_bag'))
        if lining_bag == 'True':
            lining_bag = 1
        else:
            lining_bag = 0

        bag_no = post.get('bag_no')
        if bag_no and isinstance(bag_no, str):
            bag_no = int(post.get('bag_no'))

        # product_obj = request.env['product.product'].sudo().search([('id','=', product_id)])
        product_id = request.env['product.product'].sudo().browse(product_id)
        contract_obj = request.env['shipping.instruction'].sudo().search([('name','=', contract)])
        production_obj = request.env['mrp.production'].sudo().search([('id','=',production_id)])
        pending_grp_obj = request.env['mrp.operation.result.produced.product'].sudo().search([('scale_grp_id','=',scale_grp_id)])
        mrp_operation_obj = request.env['mrp.operation.result'].sudo().search([('id','=', pending_grp_obj.operation_result_id.id)])

        if not mrp_operation_obj: # and flag == u'Create'
            vals = {'end_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'start_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'production_shift': production_shift,
                    'create_uid': user_import_id,
                    'user_import_id': user_import_id,
                    'date_result': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'production_id': production_id,
                    'warehouse_id': warehouse_id}
            result_id = request.env['mrp.operation.result'].with_user(182).create(vals)

            if result_id:
                scale_line = {'product_id': product_id.id,
                            'operation_result_id': result_id.id,
                            'packing_id': scale_packing_id,
                            'weight_scale': scale_basis_weight,
                            'bag_no': bag_no,
                            'tare_weight': scale_tare_weight,
                            'net_weight': scale_net_weight,
                            'scale_grp_id': scale_grp_id,
                            'scale_grp_line_id': scale_grp_line_id,
                            'usr_api_create': user_import_id,
                            'create_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                            'shift_name': shift_name,
                            'packing_branch_id': packing_branch_id,
                            'pallet_weight': pallet_weight,
                            'lining_bag': lining_bag,
                            'scale_no': scale_no,
                            }
                odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)

                tmp = { 'product_id': product_id.id,
                        'zone_id': zone_id,
                        'packing_id': packing_id,
                        'qty_bags': bag_no,
                        'tare_weight': scale_tare_weight + pallet_weight,
                        'product_uom': product_id.uom_id.id,
                        'product_qty': scale_net_weight,
                        'production_weight': scale_basis_weight,
                        'si_id': contract_obj.id,
                        'notes':notes,
                        'production_id':production_id,
                        'pending_grn': pending_grp_name,
                        'operation_result_id': result_id.id,
                        'scale_grp_id': scale_grp_id,
                        'create_uid': user_import_id,
                        }
                result_produced_product_id = request.env['mrp.operation.result.produced.product'].with_user(182).create(tmp)

                result_produced_product_id.create_update_stack_wip()

                mess = {
                    'mor_name': result_id.name,
                    'operation_result_id': result_id.id,
                    'mrp_result_id': result_produced_product_id.id,
                    'odoo_scale_line_id': odoo_scale_id.id,
                    'produced_product_state': result_produced_product_id.state
                    }
                return json.dumps(mess)

        else:
            # Neu co phieu mrp.operation.result thi update thong tin GRP tam
            if flag == u'EditGRP':
                pending_grp_obj.with_user(user_import_id).update({'product_id': product_id.id,
                                        'packing_id': packing_id,
                                        'zone_id': zone_id,
                                        'si_id': contract_obj.id,
                                        'notes':notes,
                                        })
                mess = {
                    'message': 'Update MOR info successfully!'
                    }
            else:
                # TH co phieu MOR va them dong can moi
                get_scale_id = 0
                if not mrp_operation_obj.scale_ids.filtered(lambda x: x.scale_grp_line_id == scale_grp_line_id):
                    scale_line = {'product_id': product_id.id,
                        'operation_result_id': mrp_operation_obj.id,
                        'packing_id': scale_packing_id,
                        'weight_scale': scale_basis_weight,
                        'bag_no': bag_no,
                        'tare_weight': scale_tare_weight,
                        'net_weight': scale_net_weight,
                        'packing_branch_id': packing_branch_id,
                        'pallet_weight': pallet_weight,
                        'lining_bag': lining_bag,
                        'scale_grp_id': scale_grp_id,
                        'scale_grp_line_id': scale_grp_line_id,
                        'usr_api_create': user_import_id,
                        'create_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'shift_name': shift_name,
                        'scale_no': scale_no,
                        }
                    odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)
                    get_scale_id = odoo_scale_id.id
                
                else:   # TH co phieu MOR va can lai Bao/Pallet
                    for move in mrp_operation_obj.scale_ids.filtered(lambda x: x.scale_grp_line_id == scale_grp_line_id):
                        move.sudo().update({
                            'packing_id': scale_packing_id,
                            'weight_scale': scale_basis_weight,
                            'bag_no': bag_no,
                            'tare_weight': scale_tare_weight,
                            'net_weight': scale_net_weight,
                            'packing_branch_id': packing_branch_id,
                            'pallet_weight': pallet_weight,
                            'lining_bag': lining_bag,
                            'scale_no': scale_no,
                            })
                        get_scale_id = move.id

                # Cap nhat trong luong tong cho phieu MOR
                grp_gross_weight = grp_net_weight = total_tare_weight = 0.0
                total_qty_bag = 0
                for line in mrp_operation_obj.scale_ids:
                    if line.state_scale in ('cancel'):
                        continue
                    grp_gross_weight += line.weight_scale or 0.0
                    total_qty_bag += line.bag_no or 0
                    total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                    grp_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0

                for move in mrp_operation_obj.produced_products.filtered(lambda x: x.product_id == product_id and x.scale_grp_id == scale_grp_id):
                    move.with_user(182).update({
                        'product_id': product_id.id,
                        'zone_id': zone_id,
                        'packing_id': packing_id,
                        'qty_bags': total_qty_bag,
                        'tare_weight': total_tare_weight,
                        'product_uom': product_id.uom_id.id,
                        'product_qty': grp_net_weight,
                        'production_weight': grp_gross_weight,
                        'si_id': contract_obj.id,
                        'notes':notes,
                        })
                mess = {
                    'mor_name': mrp_operation_obj.name,
                    'operation_result_id': mrp_operation_obj.id,
                    'mrp_result_id': mrp_operation_obj.produced_products.id,
                    'odoo_scale_line_id': get_scale_id,
                    'produced_product_state': mrp_operation_obj.produced_products.state
                    }
                return json.dumps(mess)


    @http.route('/api/weightscale/mrp_production_post_grp', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def mrp_production_post_grp(self, **post):
        user_import_id = post.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(post.get('user_import_id'))

        scale_grp_id = post.get('scale_grp_id')
        if scale_grp_id and isinstance(scale_grp_id, str):
            scale_grp_id = int(post.get('scale_grp_id'))
      
        total_row = post.get('total_row')
        if total_row and isinstance(total_row, str):
            total_row = int(post.get('total_row'))

        operation_result_id = post.get('operation_result_id')
        if operation_result_id and isinstance(operation_result_id, str):
            operation_result_id = int(post.get('operation_result_id'))

        operation_result_obj = request.env['mrp.operation.result'].sudo().search([('id','=',operation_result_id)])
        produced_product = request.env['mrp.operation.result.produced.product'].sudo().search([('scale_grp_id','=',scale_grp_id)])
        
        total_odoo_row = 0
        for line in operation_result_obj.scale_ids:
            total_odoo_row += 1

        if total_row == total_odoo_row:
            picking_obj = produced_product.with_user(user_import_id).create_kcs()

            # print(produced_product.picking_id.name,  'stock_picking_state_kcs  %s'%(produced_product.picking_id.state_kcs))
            mess = {
                'message': 'Post MOR to KCS successfully!',
                'stock_picking_name': produced_product.picking_id.name,
                'stock_picking_state_kcs': produced_product.picking_id.state_kcs
                }
            return json.dumps(mess)
            # if picking_obj:
            #     mess = {
            #         'message': 'Post MOR to KCS successfully!',
            #         'stock_picking_name': produced_product.picking_id.name,
            #         'stock_picking_state_kcs': produced_product.picking_id.state_kcs
            #         }
            #     return json.dumps(mess)
            # else:
            #     mess = {
            #         'message': 'Not create Picking yet!',
            #         }
            #     return json.dumps(mess)
        else:
            mess = {
                'message': 'Total line of weight scale different Odoo scale line!',
                }
            return json.dumps(mess)



    @http.route('/api/weightscale/cancel_grp_temp', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def post_cancel_grp_temp(self, **post):
        mrp_result_id = post.get('mrp_result_id')
        if mrp_result_id and isinstance(mrp_result_id, str):
            mrp_result_id = int(post.get('mrp_result_id'))

        pending_grp_obj = request.env['mrp.operation.result.produced.product'].sudo().search([('id','=',mrp_result_id)])
        if pending_grp_obj:
            pending_grp_obj.button_cancel()

            mess = {
                'message': 'MOR cancel successfully!',
                'mrp_state': pending_grp_obj.state,
                'mrp_result_id': pending_grp_obj.id
                }
            return json.dumps(mess)



    @http.route('/api/weightscale/get_request_materials_line', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def get_request_materials_line(self, **post):
        warehouse_id = int(post.get('warehouse_id'))
        sql = '''SELECT mrp.id production_id, mrp.name mrp_name, line.id rml_id, line.product_id, pp.default_code, line.stack_id, 
                sl.name stack_name, line.packing_id, line.bag_no, sl.init_qty qty_stack, line.product_qty, Case When sum(sp.total_init_qty) is null then 0 else sum(sp.total_init_qty) END AS issue_qty, 
                line.product_qty - Case When sum(sp.total_init_qty) is null then 0 else sum(sp.total_init_qty) END as to_be_issue,
                rm.id pmr_id, rm.name pmr_name, zone.id zone_id, zone.name zone_name, line.state rml_state
            FROM request_materials_line line
            JOIN request_materials rm on rm.id = line.request_id
            LEFT JOIN picking_request_move_ref refs on line.id = refs.picking_id
            LEFT JOIN stock_picking sp ON sp.id = refs.request_id
            JOIN mrp_production mrp on mrp.id = rm.production_id
            JOIN product_product pp on pp.id = line.product_id
            JOIN stock_lot sl on sl.id = line.stack_id
            JOIN stock_zone zone on zone.id = sl.zone_id
            Where mrp.state='confirmed' AND zone.name!='Hopper' AND mrp.warehouse_id = %s
            GROUP BY mrp.id, mrp.name, line.id, line.product_id, pp.default_code, line.stack_id, sl.name,
            line.packing_id, line.bag_no, sl.init_qty, line.product_qty, rm.id, rm.name, zone.id, zone.name'''%(warehouse_id)
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)


    @http.route('/api/weightscale/get_gip_list', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def get_gip_list(self):
        sql = '''SELECT sp.id sp_id, sp.name, sp.lot_id, sl.name stack_name, sp.production_id, mrp.name mrp_name, sml.init_qty, sml.bag_no, 
                sp.packing_id, sp.state_kcs, rml.id rml_id, rm.id rm_id, rm.name rm_name, sp.state sp_state, sml.tare_weight,
                sml.gross_weight, sml.product_id, sml.scale_gip_id
            FROM stock_move_line sml
            JOIN stock_picking sp ON sp.id = sml.picking_id
            JOIN picking_request_move_ref refs on sp.id = refs.request_id 
            JOIN request_materials_line rml on rml.id = refs.picking_id
            JOIN request_materials rm on rm.id = rml.request_id
            JOIN mrp_production mrp on mrp.id = rm.production_id
            JOIN stock_lot sl on sl.id = sml.lot_id
            WHERE sp.picking_type_code='production_out' AND sml.scale_gip_id > 0
            AND mrp.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '1 month')'''
                # AND sp.production_id =6474 and sp.lot_id=80243

        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)


    @http.route('/api/weightscale/create_gip_picking', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def create_gip_picking(self, **post):
        scale_no = post.get('scale_no')
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))

        request_materials_line_id = post.get('request_materials_line_id')
        if request_materials_line_id and isinstance(request_materials_line_id, str):
            request_materials_line_id = int(post.get('request_materials_line_id'))
        
        product_id = post.get('product_id')
        if product_id and isinstance(product_id, str):
            product_id = int(post.get('product_id'))
        scale_packing_id = post.get('scale_packing_id')
        if scale_packing_id and isinstance(scale_packing_id, str):
            scale_packing_id = int(post.get('scale_packing_id'))
       
        scale_basis_weight = self._get_numeric(post.get('scale_basis_weight'))
       
        bag_no = post.get('bag_no')
        if bag_no and isinstance(bag_no, str):
            bag_no = int(post.get('bag_no'))
        
        scale_tare_weight = self._get_numeric(post.get('scale_tare_weight'))
        scale_net_weight = self._get_numeric(post.get('scale_net_weight'))

        scale_gip_id = post.get('scale_gip_id')
        if scale_gip_id and isinstance(scale_gip_id, str):
            scale_gip_id = int(post.get('scale_gip_id'))
        scale_gip_line_id = post.get('scale_gip_line_id')
        if scale_gip_line_id and isinstance(scale_gip_line_id, str):
            scale_gip_line_id = int(post.get('scale_gip_line_id'))

        user_import_id = post.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(post.get('user_import_id'))

        shift_name = post.get('shift_name')
        production_shift = post.get('production_shift')

        packing_branch_id = post.get('packing_branch_id')
        if packing_branch_id and isinstance(packing_branch_id, str):
            packing_branch_id = int(post.get('packing_branch_id'))

        pallet_weight = self._get_numeric(post.get('pallet_weight'))
        
        old_weight = self._get_numeric(post.get('old_weight'))
        bag_code = post.get('bag_code')
        
        lining_bag = str(post.get('lining_bag'))
        if lining_bag == 'True':
            lining_bag = 1
        else:
            lining_bag = 0

        bag_qty = post.get('bag_qty')
        if bag_qty and isinstance(bag_qty, str):
            bag_qty = int(post.get('bag_qty'))

        picking_id = post.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(post.get('picking_id'))

        product_id = request.env['product.product'].sudo().browse(product_id)

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])
        if not stock_picking_obj:
            result_obj = request.env['request.materials.line'].sudo().browse(request_materials_line_id)
            # Check MRP state before get weight_scale
            if result_obj.request_id.production_id.state == 'done':
                mess = {
                    'err_code': 'SUD23-00003',
                    'message': '''%s has been Done, can't create!''' %(result_obj.request_id.production_id.name),
                    }
                # print(mess)
                return json.dumps(mess)

            warehouse_id = result_obj.request_id.warehouse_id or request.env['stock.warehouse'].sudo().search([('id', '=', warehouse_id)], limit=1)
            
            location_id = False
            if result_obj and result_obj.stack_id:
                location_id =  warehouse_id.wh_raw_material_loc_id
            crop_id = request.env['ned.crop'].sudo().search([('state', '=', 'current')], limit=1)
            
            vals = {
                'name': '/', 
                'picking_type_id': warehouse_id.production_out_type_id.id, 
                'date_done': time.strftime('%Y-%m-%d %H:%M:%S'), 
                'partner_id': False, 
                'crop_id':crop_id.id,
                'location_id': location_id and location_id.id or False, 
                'production_id': result_obj.request_id.production_id.id or False,  
                'location_dest_id': warehouse_id.production_out_type_id.default_location_dest_id.id or False,
                'request_materials_id':result_obj.request_id.id,
                'warehouse_id':warehouse_id.id,
                'state':'draft',
                'state_kcs': 'waiting',
                }  
            create_picking = request.env['stock.picking'].with_user(182).create(vals)
            result_obj.sudo().write({'picking_ids': [(4, create_picking.id)]})
            
            product_uom_qty = scale_net_weight - (scale_net_weight * abs(result_obj.stack_id.avg_deduction/100)) or 0.0
            spl_val ={
                'picking_id': create_picking.id or False, 
                'product_uom_id': result_obj.product_id.uom_id.id or False,
                'init_qty':scale_net_weight or 0.0,
                'gross_weight': scale_basis_weight,
                'qty_done': product_uom_qty or 0.0, 
                'reserved_uom_qty':product_uom_qty or 0.0,
                'price_unit': 0.0,
                'picking_type_id': create_picking.picking_type_id.id or False,
                'location_id': create_picking.location_id.id or False,
                'location_dest_id': create_picking.location_dest_id.id or False,
                'company_id': request.env.user.company_id.id, 
                'zone_id': result_obj.stack_id.zone_id.id or False, 
                'product_id': result_obj.product_id.id or False,
                'date': create_picking.date_done or False, 
                'currency_id': False,
                'state':'draft', 
                'warehouse_id': create_picking.warehouse_id.id or False,
                'lot_id':result_obj.stack_id.id,
                'production_id': create_picking.production_id.id or False,
                'packing_id':result_obj.stack_id and result_obj.stack_id.packing_id and result_obj.stack_id.packing_id.id or False,
                'bag_no':bag_no,
                'tare_weight': scale_tare_weight + pallet_weight,
                'scale_gip_id': scale_gip_id,
                'material_id': result_obj.request_id.production_id.id or False,
                }
            move_id = request.env['stock.move.line'].with_user(182).create(spl_val)

            scale_line = {'product_id': product_id.id,
                'picking_scale_id': create_picking.id,
                'packing_id': scale_packing_id,
                'weight_scale': scale_basis_weight,
                'bag_no': bag_no,
                'tare_weight': scale_tare_weight,
                'net_weight': scale_net_weight,
                'old_weight': old_weight,
                'bag_code': bag_code,
                'scale_gip_id': scale_gip_id,
                'scale_gip_line_id': scale_gip_line_id,
                'usr_api_create': user_import_id,
                'create_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                'shift_name': shift_name,
                'packing_branch_id': packing_branch_id,
                'pallet_weight': pallet_weight,
                'lining_bag': lining_bag,
                'scale_no': scale_no,
                }
            odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)

            mess = {
                'err_code': 'SUD23-00000',
                'message': '%s created successfully!' %(create_picking.name),
                'stock_picking_name': create_picking.name,
                'stock_picking_id': create_picking.id,
                'stock_picking_state': create_picking.state,
                'stock_move_line_id': create_picking.move_line_ids_without_package.id,
                'odoo_scale_line_id': odoo_scale_id.id,
                }
            return json.dumps(mess)

        else:
            # Check MRP state before get weight_scale
            if stock_picking_obj.production_id.state == 'done':
                mess = {
                    'err_code': 'SUD23-00004',
                    'message': '''%s has been Done, can't add new scale_line!''' %(stock_picking_obj.production_id.name),
                    }
                # print(mess)
                return json.dumps(mess)

            odoo_scale_line_id = 0
            # TH co phieu GIP va them dong can moi
            if not stock_picking_obj.scale_ids.filtered(lambda x: x.scale_gip_line_id == scale_gip_line_id):
                scale_line = {'product_id': product_id.id,
                    'picking_scale_id': stock_picking_obj.id,
                    'packing_id': scale_packing_id,
                    'weight_scale': scale_basis_weight,
                    'bag_no': bag_no,
                    'tare_weight': scale_tare_weight,
                    'net_weight': scale_net_weight,
                    'old_weight': old_weight,
                    'bag_code': bag_code,
                    'scale_gip_id': scale_gip_id,
                    'scale_gip_line_id': scale_gip_line_id,
                    'usr_api_create': user_import_id,
                    'create_date': time.strftime('%Y-%m-%d %H:%M:%S'),
                    'shift_name': shift_name,
                    'packing_branch_id': packing_branch_id,
                    'pallet_weight': pallet_weight,
                    'lining_bag': lining_bag,
                    'scale_no': scale_no,
                    }
                odoo_scale_id = request.env['mrp.operation.result.scale'].with_user(182).create(scale_line)
                odoo_scale_line_id = odoo_scale_id.id
            # TH co phieu GIP va can lai Bao/Pallet
            else:
                for move in stock_picking_obj.scale_ids.filtered(lambda x: x.scale_gip_line_id == scale_gip_line_id):
                    move.sudo().update({
                        'packing_id': scale_packing_id,
                        'weight_scale': scale_basis_weight,
                        'bag_no': bag_no,
                        'tare_weight': scale_tare_weight,
                        'net_weight': scale_net_weight,
                        'old_weight': old_weight,
                        'bag_code': bag_code,
                        'packing_branch_id': packing_branch_id,
                        'pallet_weight': pallet_weight,
                        'lining_bag': lining_bag,
                        'scale_no': scale_no,
                        })
                    odoo_scale_line_id = move.id

            # Cap nhat trong luong tong cho phieu GIP
            gip_gross_weight = gip_net_weight = total_tare_weight = product_uom_qty = 0.0
            total_qty_bag = 0
            for line in stock_picking_obj.scale_ids:
                if line.state_scale in ('cancel'):
                    continue
                gip_gross_weight += line.weight_scale or 0.0
                total_qty_bag += line.bag_no or 0
                total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                gip_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0
                
            for move in stock_picking_obj.move_line_ids_without_package.filtered(lambda x: x.product_id == product_id and x.scale_gip_id == scale_gip_id):
                product_uom_qty = gip_net_weight - (gip_net_weight * abs(move.lot_id.avg_deduction/100)) or 0.0
                move.with_user(182).update({
                                    'gross_weight': gip_gross_weight,
                                    'init_qty': gip_net_weight,
                                    'bag_no': total_qty_bag,
                                    'tare_weight': total_tare_weight,
                                    'qty_done': product_uom_qty or 0.0, 
                                    'reserved_uom_qty':product_uom_qty or 0.0,
                              })
            mess = {
                'err_code': 'SUD23-00000',
                'message': '%s add new scale_line successfully!' %(stock_picking_obj.name),
                'stock_picking_name': stock_picking_obj.name,
                'stock_picking_id': stock_picking_obj.id,
                'stock_picking_state': stock_picking_obj.state,
                'stock_move_line_id': stock_picking_obj.move_line_ids_without_package.id,
                'odoo_scale_line_id': odoo_scale_line_id,
                }
            return json.dumps(mess)

    @http.route('/api/weightscale/gip_picking_route_qc', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def gip_picking_route_qc(self, **post):
        user_import_id = post.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(post.get('user_import_id'))

        picking_id = post.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(post.get('picking_id'))

        total_row = post.get('total_row')
        if total_row and isinstance(total_row, str):
            total_row = int(post.get('total_row'))

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])

        total_odoo_row = 0
        for line in stock_picking_obj.scale_ids:
            total_odoo_row += 1

        if total_row == total_odoo_row:
            stock_picking_obj.button_qc_assigned()
            stock_picking_obj.button_sd_validate()
            stock_picking_obj.with_user(182).update({'state_kcs': 'draft'})
            mess = {
                'message': 'Route GIP receipt to KCS successfully!',
                'stock_picking_state': stock_picking_obj.state,
                'stock_picking_state_kcs': stock_picking_obj.state_kcs
                }
            return json.dumps(mess)
        else:
            mess = {
                'message': 'Total line of weight scale different Odoo scale line!',
                }
            return json.dumps(mess)


    @http.route('/api/weightscale/cancel_scale', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def cancel_scale(self, **post):
        user_import_id = post.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(post.get('user_import_id'))

        scale_line_id = post.get('scale_line_id')
        if scale_line_id and isinstance(scale_line_id, str):
            scale_line_id = int(post.get('scale_line_id'))

        picking_id = post.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(post.get('picking_id'))

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])
        # print(stock_picking_obj.id)

        operation_result_id = post.get('operation_result_id')
        if operation_result_id and isinstance(operation_result_id, str):
            operation_result_id = int(post.get('operation_result_id'))

        mrp_operation_obj = request.env['mrp.operation.result'].sudo().search([('id','=', operation_result_id)])
        # print(mrp_operation_obj.id)

        if stock_picking_obj:
            scale_line_obj = request.env['mrp.operation.result.scale'].sudo().search([('scale_gip_line_id','=',scale_line_id)])
            scale_line_obj.with_user(user_import_id).update({'state_scale': 'cancel',})

            # Cap nhat trong luong tong cho phieu GIP
            gip_gross_weight = gip_net_weight = total_tare_weight = product_uom_qty = 0.0
            total_qty_bag = 0
            for line in stock_picking_obj.scale_ids:
                if line.state_scale in ('cancel'):
                    continue
                gip_gross_weight += line.weight_scale or 0.0
                total_qty_bag += line.bag_no or 0
                total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                gip_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0
                
            for move in stock_picking_obj.move_line_ids_without_package.filtered(lambda x: x.scale_gip_id == scale_line_obj.scale_gip_id):
                product_uom_qty = gip_net_weight - (gip_net_weight * abs(move.stack_id.avg_deduction/100)) or 0.0
                move.with_user(user_import_id).update({
                                    'gross_weight': gip_gross_weight,
                                    'init_qty': gip_net_weight,
                                    'bag_no': total_qty_bag,
                                    'tare_weight': total_tare_weight,
                                    'qty_done': product_uom_qty or 0.0, 
                                    'reserved_uom_qty':product_uom_qty or 0.0,
                              })

                mess = {
                    'message': 'Cancel scale line successfully!',
                    }
                return json.dumps(mess)

        if mrp_operation_obj:
            scale_line_obj = request.env['mrp.operation.result.scale'].sudo().search([('scale_grp_line_id','=',scale_line_id)])
            scale_line_obj.with_user(user_import_id).update({'state_scale': 'cancel',})

            # Cap nhat trong luong tong cho phieu GIP
            grp_gross_weight = grp_net_weight = total_tare_weight = 0.0
            total_qty_bag = 0
            for line in mrp_operation_obj.scale_ids:
                if line.state_scale in ('cancel'):
                    continue
                grp_gross_weight += line.weight_scale or 0.0
                total_qty_bag += line.bag_no or 0
                total_tare_weight += line.tare_weight + line.pallet_weight or 0.0
                grp_net_weight += line.weight_scale - (line.tare_weight + line.pallet_weight) or 0.0
            # print(grp_gross_weight, total_qty_bag, total_tare_weight, grp_net_weight)
            # print(mrp_operation_obj.produced_products.id)
            for move in mrp_operation_obj.produced_products.filtered(lambda x: x.scale_grp_id == scale_line_obj.scale_grp_id):
                # print(move.stack_wip_id)
                move.with_user(user_import_id).update({
                    'qty_bags': total_qty_bag,
                    'tare_weight': total_tare_weight,
                    'product_qty': grp_net_weight,
                    'production_weight': grp_gross_weight,
                    })                

                mess = {
                    'message': 'Cancel scale line successfully!',
                    }
                return json.dumps(mess)


    @http.route('/api/weightscale/sql_update', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def sql_update(self, **post):
        sql_update_query = post.get('sql_update_query')
        sql = '''%s'''%(sql_update_query)
        # print(sql)
        records = request.cr.execute(sql_update_query)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(records)

        
    @http.route('/api/weightscale/cancel_gip_draff', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def post_cancel_gip_draff(self, **post):
        picking_id = post.get('picking_id')
        if picking_id and isinstance(picking_id, str):
            picking_id = int(post.get('picking_id'))

        stock_picking_obj = request.env['stock.picking'].sudo().search([('id','=',picking_id)])
        if stock_picking_obj:
            stock_picking_obj.action_cancel()

            mess = {
                'message': 'GIP cancel successfully!',
                'picking_gip_state': stock_picking_obj.state,
                'picking_gip_id': stock_picking_obj.id
                }
            return json.dumps(mess)



