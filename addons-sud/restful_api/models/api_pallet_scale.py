# -*- coding: utf-8 -*-

from datetime import datetime, timedelta
from odoo import api, http, fields, models, _
import openerp.addons.decimal_precision as dp
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


class APIPackingBranch(http.Controller):

    @http.route('/api/weightscale/pallet_list', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def get_pallet_list(self, **post):
        warehouse_id = int(post.get('warehouse_id'))
        sql_ext1 = ''
        if warehouse_id:
            sql_ext1 = 'WHERE warehouse_id = %s'%(warehouse_id)
        sql = '''SELECT id, packing_id, name, description_name, dimension, state, tare_weight, warehouse_id, 
                    CAST(create_date at time zone 'utc' at time zone 'ict' AS TEXT) AS create_date, user_import_id, scale_id 
                 FROM sud_packing_branch %s order by id; '''%(sql_ext1)

        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)


    @http.route('/api/weightscale/pallet_history_list', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def get_pallet_history_list(self):
        sql = '''SELECT id, repair_reason, tare_weight_old, tare_weight_new, repair_id, scale_id, scale_line_id, 
                    CAST(create_date at time zone 'utc' at time zone 'ict' AS TEXT) AS create_date, user_import_id 
                FROM sud_packing_branch_line order by id;'''
        print(sql)

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

    def _get_numeric(self, number):
        if number and isinstance(number, str):
            new_number = float(number) or 0.0
            return new_number


    @http.route('/api/weightscale/create_update_pallet', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def create_update_pallet(self, **post):
        flag = post.get('flag')
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))
        packing_id = post.get('packing_id')
        if packing_id and isinstance(packing_id, str):
            packing_id = int(post.get('packing_id'))
        dimension = post.get(u'dimension')

        scale_id = post.get('scale_id')
        if scale_id and isinstance(scale_id, str):
            scale_id = int(post.get('scale_id'))
        
        repair_reason = post.get(u'repair_reason')
        tare_weight_old = self._get_numeric(post.get('tare_weight_old'))
        tare_weight_new = self._get_numeric(post.get('tare_weight_new'))

        scale_line_id = post.get('scale_line_id')
        if scale_line_id and isinstance(scale_line_id, str):
            scale_line_id = int(post.get('scale_line_id'))

        user_import_id = post.get('user_import_id')
        if user_import_id and isinstance(user_import_id, str):
            user_import_id = int(post.get('user_import_id'))

        packing_branch_obj = request.env['sud.packing.branch'].sudo().search([('scale_id','=', scale_id)])

        if not packing_branch_obj:
            vals = {'packing_id': packing_id,
                    'description_name': 'New',
                    'dimension': dimension,
                    'warehouse_id': warehouse_id,
                    'scale_id': scale_id,
                    'user_import_id': user_import_id
                    }
            packing_branch_id = request.env['sud.packing.branch'].with_user(182).create(vals)
            if packing_branch_id:
                packing_branch_id.with_user(user_import_id).update({
                    'description_name': packing_branch_id.packing_id.name + '/' + packing_branch_id.name})

                tmp = {'repair_reason': repair_reason,
                    'tare_weight_old': tare_weight_old,
                    'tare_weight_new': tare_weight_new,
                    'scale_id': scale_id,
                    'repair_id': packing_branch_id.id,
                    'user_import_id': user_import_id,
                    'scale_line_id': scale_line_id
                    }
                packing_branch_line_id = request.env['sud.packing.branch.line'].with_user(182).create(tmp)
                packing_branch_id.button_done()

                mess = {
                    'name': packing_branch_id.name,
                    'description_name': packing_branch_id.description_name,
                    'scale_id': packing_branch_id.scale_id,
                    'packing_branch_id': packing_branch_id.id,
                    'packing_branch_line_id': packing_branch_line_id.id,
                    'scale_line_id': packing_branch_line_id.scale_line_id,
                    'tare_weight_old': packing_branch_line_id.tare_weight_old
                    }
                return json.dumps(mess)

        elif packing_branch_obj: # and (flag == u'Newline' or flag == u'Update')
            packing_obj = request.env['ned.packing'].sudo().search([('id','=', packing_id)])
            packing_branch_obj.with_user(user_import_id).update({
                'description_name': packing_obj.name + '/' + packing_branch_obj.name,
                'packing_id': packing_id,
                'dimension': dimension,
                'tare_weight': packing_branch_obj.tare_weight,
                })

            packing_branch_line_obj = request.env['sud.packing.branch.line'].sudo().search([('scale_line_id','=', scale_line_id)])
            if tare_weight_new == 0 and packing_branch_line_obj:
                packing_branch_line_obj.with_user(user_import_id).update({
                    'repair_reason': repair_reason,
                    'user_import_id': user_import_id
                    })
                packing_branch_obj.button_done()

                mess = {
                    'name': packing_branch_obj.name,
                    'description_name': packing_branch_obj.description_name,
                    'scale_id': packing_branch_obj.scale_id,
                    'packing_branch_id': packing_branch_obj.id,
                    'packing_branch_line_id': packing_branch_line_obj.id,
                    'scale_line_id': packing_branch_line_obj.scale_line_id,
                    'tare_weight_old': packing_branch_line_obj.tare_weight_old
                    }
                return json.dumps(mess)
            else:
                tmp = {'repair_reason': repair_reason,
                    'tare_weight_old': tare_weight_old,
                    'tare_weight_new': tare_weight_new,
                    'scale_id': scale_id,
                    'repair_id': packing_branch_obj.id,
                    'user_import_id': user_import_id,
                    'scale_line_id': scale_line_id
                    }
                packing_branch_line_obj = request.env['sud.packing.branch.line'].with_user(182).create(tmp)
                packing_branch_obj.button_done()

                mess = {
                    'name': packing_branch_obj.name,
                    'description_name': packing_branch_obj.description_name,
                    'scale_id': packing_branch_obj.scale_id,
                    'packing_branch_id': packing_branch_obj.id,
                    'packing_branch_line_id': packing_branch_line_obj.id,
                    'scale_line_id': packing_branch_line_obj.scale_line_id,
                    'tare_weight_old': packing_branch_line_obj.tare_weight_old
                    }
                return json.dumps(mess)

