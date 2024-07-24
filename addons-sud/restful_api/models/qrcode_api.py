# -*- coding: utf-8 -*-

import ast
from datetime import datetime
import time
# from odoo.http import http
from odoo import SUPERUSER_ID
from odoo.tools import float_is_zero, float_compare, DEFAULT_SERVER_DATETIME_FORMAT
# from odoo.addons.website import slug, unslug
from odoo.http import route, request, json
from odoo.exceptions import AccessError, UserError
# from models import JWTAuth
from odoo import http


class QRCodeAPI(http.Controller):

    @http.route('/api/qrcode', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def get_info_stack(self, token= None, **post):
        stack_name = post.get('stack')
        sql = '''
            SELECT
                ss.name stack_name,
                si.name contract_name,
                rp.display_name,
                si.factory_etd date_etd,
                ss.date date_in,
                pp.default_code product,
                ss.init_qty balance_weight,
                sz.name zone_name
            FROM stock_stack ss
                LEFT JOIN stock_contract_allocation sca ON ss.id = sca.stack_no
                    JOIN product_product pp ON pp.id = ss.product_id
                    JOIN stock_zone sz ON sz.id = ss.zone_id
                LEFT JOIN shipping_instruction si ON si.id = sca.shipping_id
                    LEFT JOIN res_partner rp ON rp.id = si.partner_id
            WHERE ss.name = '%s'
        '''%(stack_name)
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            if result[0]['balance_weight'] > 0:
                return json.dumps(result)
            else:
                mess = {
                    'message': 'Balance weight is zero.',
                    }
            return json.dumps(mess)

    @http.route('/api/qrcode/zone', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def get_zone(self, token= None, **post):
        sql = '''
            SELECT
                sz.name zone_name
            FROM stock_zone sz
                JOIN stock_warehouse sw ON sw.id = sz.warehouse_id
            WHERE sw.code != 'BCCE'
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
    

    @http.route('/api/qrcode/exzone', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def exchange_zone(self, token= None, **post):
        zone_name = post.get('zone_name')
        stack_name = post.get('stack_name')
        stack_id = request.env['stock.lot'].sudo().search([('name','=',stack_name)], limit=1)
        zone_id = request.env['stock.zone'].sudo().search([('name','=',zone_name)], limit=1)
        if not stack_id:
            mess = {
                'message': 'Stack does not exist.',
                }
            return json.dumps(mess)
        else:
            var = {
                'from_zone_id': stack_id.zone_id.id,
                'to_zone_id': zone_id.id,
                'name': "Exchange Stack: %s from %s to %s"%(stack_name, stack_id.zone_id.name, zone_name)
            }
            new_id = request.env['stock.lot.transfer'].sudo().create(var)
            stack_id.stack_his_ids = [(4, new_id.id)]
            stack_id.sudo().update({
                'zone_id' : zone_id.id
            })
            mess = {
                'message': 'Zone exchange uccessful!',
                }
            return json.dumps(mess)

    @http.route('/api/qrcode/stacktransfer', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def transfer_stack(self, token= None, **post):
        from_stack = post.get('from_stack')
        to_stack = post.get('to_stack')
        from_stack_id = request.env['stock.lot'].sudo().search([('name','=',from_stack)], limit=1)
        to_stack_id = request.env['stock.lot'].sudo().search([('name','=',to_stack)], limit=1)
        qty = post.get('qty')
        mess = ''
        if not from_stack_id:
            mess += '%s does not exist.'
        if not to_stack_id:
            mess += '\n%s does not exist.'
        if from_stack_id and to_stack_id and from_stack_id.product_id.id != to_stack_id.product_id.id:
            mess += '\nProduct not mapped.'
        if from_stack_id and from_stack_id.net_qty < qty:
            mess += '\nYou have only %s.'%(from_stack_id.net_qty)
        if mess != '':
            mess = {
                'message': mess,
                }
            return json.dumps(mess)
        else:
            #in
            picking_type_id = request.env['stock.picking.type'].sudo().search([('code','=','production_in'),('active','=',True)], limit=1)
            move_in_id = request.env['stock.move.line'].sudo().create({'picking_id': False, 
                        'name': from_stack_id.product_id.name or '', 
                        'product_id': from_stack_id.product_id.id or False,
                        'product_uom': from_stack_id.product_id.uom_id.id or False, 
                        'product_uom_qty': qty or 0.0,
                        'init_qty': qty or 0.0,
                        'price_unit': 0.0,
                        'picking_type_id': picking_type_id.id or False, 
                        'location_id': picking_type_id.default_location_src_id.id or False, 
                        'date_expected': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'location_dest_id': picking_type_id.default_location_dest_id.id or False, 
                        'type': picking_type_id.code or False,
                        'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), 
                        'partner_id': False,
                        'company_id': 1,
                        'state':'done', 
                        'scrapped': False, 
                        'zone_id':from_stack_id.zone_id.id,
                        'stack_id':to_stack_id.id,
                        'packing_id':False,
                        'warehouse_id': False})
            
            #out
            picking_out_type_id = request.env['stock.picking.type'].sudo().search([('code','=','production_out'),('active','=',True)], limit=1)
            request.env['stock.move.line'].sudo().create({'picking_id': False, 
                        'name': from_stack_id.product_id.name or '', 
                        'product_id': from_stack_id.product_id.id or False,
                        'product_uom': from_stack_id.product_id.uom_id.id or False, 
                        'product_uom_qty': qty or 0.0,
                        'init_qty': qty or 0.0,
                        'price_unit': 0.0,
                        'picking_type_id': picking_out_type_id.id or False, 
                        'location_id': picking_out_type_id.default_location_src_id.id or False, 
                        'date_expected': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT),
                        'location_dest_id': picking_out_type_id.default_location_dest_id.id or False, 
                        'type': picking_out_type_id.code or False,
                        'date': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT), 
                        'partner_id': False,
                        'company_id': 1,
                        'state':'done', 
                        'scrapped': False, 
                        'zone_id':from_stack_id.zone_id.id,
                        'stack_id':from_stack_id.id,
                        'packing_id':False,
                        'warehouse_id': False})
            mess = {
                'message': 'Stack transfer successful!',
                }
            return json.dumps(mess)