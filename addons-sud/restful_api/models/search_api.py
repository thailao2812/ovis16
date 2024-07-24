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
    
    @http.route('/api/search/security_gate', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def list_security_gate(self, **post):
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))

        warehouse_id_list = post.get('warehouse_id_list')

        sql_check_country = '''SELECT name FROM res_company WHERE name ilike '%VN%' or name ilike '%VIỆT NAM%';'''
        records = request.cr.execute(sql_check_country)
        result = request.env.cr.dictfetchall()
        print(result)
        sql = ''
        if result == []:
            sql = '''SELECT sec.id, sec.name, sec.warehouse_id, sec.supplier_id, sec.customer_id, sec.license_plate as vehicle, sec.first_cont, sec.last_cont, sec.estimated_bags, 
                    sec.parking_order, spt.code, spt.name picking_name, sec.state, pp.default_code, pp.id product_id, sec.type_transfer, sec.districts_id, sec.packing_id,
                    CAST(sec.time_out AS TEXT), sec.estate_name 
                    FROM ned_security_gate_queue sec 
                    LEFT JOIN stock_picking_type spt ON sec.picking_type_id=spt.id 
                    LEFT JOIN security_gate_product_rel sec_rel ON sec.id=sec_rel.security_gate_id
                    LEFT JOIN product_product pp ON sec_rel.product_id=pp.id
                    WHERE sec.warehouse_id is not null
                    AND date(timezone('UTC',sec.arrivial_time::timestamp)) >= date(TIMESTAMP 'now') - integer '4'
                    AND sec.warehouse_id in (%s); '''%(warehouse_id_list)
        else:
            sql = '''SELECT sec.id, sec.name, sec.warehouse_id, sec.supplier_id, sec.customer_id, sec.license_plate as vehicle, sec.first_cont, sec.last_cont, sec.estimated_bags, 
                    sec.parking_order, spt.code, spt.name picking_name, sec.state, pp.default_code, pp.id product_id, sec.type_transfer, sec.districts_id, sec.packing_id,
                    CAST(sec.time_out AS TEXT)
                    FROM ned_security_gate_queue sec 
                    LEFT JOIN stock_picking_type spt ON sec.picking_type_id=spt.id 
                    LEFT JOIN security_gate_product_rel sec_rel ON sec.id=sec_rel.security_gate_id
                    LEFT JOIN product_product pp ON sec_rel.product_id=pp.id
                    WHERE sec.warehouse_id is not null
                    AND date(timezone('UTC',sec.arrivial_time::timestamp)) >= date(TIMESTAMP 'now') - integer '4'
                    AND sec.warehouse_id = %s; '''%(warehouse_id)

        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:

            return json.dumps(result)

    @http.route('/api/search/security_gate_exstore', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def security_gate_exstore(self, **post):
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))

        sql = '''SELECT sec.id, sec.name, sec.warehouse_id, sec.customer_id, sec.license_plate as vehicle, sec.first_cont, sec.last_cont, sec.estimated_bags, 
                sec.parking_order, sec.state, pp.default_code, pp.id product_id
                FROM ned_security_gate_queue sec 
                LEFT JOIN stock_picking_type spt ON sec.picking_type_id=spt.id 
                LEFT JOIN security_gate_product_rel sec_rel ON sec.id=sec_rel.security_gate_id
                LEFT JOIN product_product pp ON sec_rel.product_id=pp.id
                WHERE sec.warehouse_id is not null AND type_transfer='queue-exstore'
                AND date(timezone('UTC',sec.arrivial_time::timestamp)) >= date(TIMESTAMP 'now') - integer '4'
                AND sec.warehouse_id = %s; '''%(warehouse_id)

        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:

            return json.dumps(result)

    @http.route('/api/search/getlist_security', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_purchase_getlist(self):
        sql = '''SELECT sec.id, sec.name, sw.name warehouse_name, rp.name supplier_name, sec.license_plate as vehicle, sec.warehouse_id,
                    sec.estimated_bags, sec.approx_quantity, sec.state, sec.mc, sec.moldy, sec.burn, sec.odor, sec.black, sec.broken, 
                    sec.brown, sec.screen, sec.remarks, pp.default_code AS product
                FROM ned_security_gate_queue sec
                JOIN stock_warehouse sw ON sec.warehouse_id=sw.id
                JOIN res_partner rp ON sec.supplier_id=rp.id
                LEFT JOIN security_gate_product_rel sec_product ON sec.id=sec_product.security_gate_id
                LEFT JOIN product_product pp ON pp.id=sec_product.product_id
                WHERE state in ('pur_approved','qc_approved'); '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/search/get_gdn_list', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def get_gdn_list(self):
        # THÊM ĐK field LINK VỚI PHIẾU DR
        sql = '''SELECT sp.id, sp.name, sp.partner_id, sp.warehouse_id, sp.vehicle_no, sp.backorder_id, 
                    sp.weightbridge_update, sp.origin, sp.state, sml.product_id, sml.lot_id, sml.packing_id
                FROM stock_picking sp
                JOIN stock_move_line sml ON sml.picking_id=sp.id
                WHERE sp.picking_type_code='outgoing'
                AND date(timezone('UTC',sp.create_date::timestamp)) >= date(TIMESTAMP 'now') - integer '7'; '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    #New Json
        # mess=False
        # if result == []:
        #     mess =False
        # else:
        #     mess =True
        # return json.dumps([{"message": mess, "data": result}])

    @http.route('/api/search/purchase_approve', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def list_purchase_approve(self, **post):
        gate_id = post.get('gate_id')
        if gate_id and isinstance(gate_id, str):
            gate_id = int(post.get('gate_id'))
        if gate_id: 
            gate_id = request.env['ned.security.gate.queue'].sudo().browse(gate_id)

        if not gate_id:
            mess = {
                'message': 'Gate does not exist.',
                }
            return json.dumps(mess)
        else:
            if gate_id.state != 'pur_approved':
                mess = {
                    'message': 'This ticket has been approved.',
                    }
                return json.dumps(mess)
            else:
                gate_id.sudo().update({
                        'arrivial_time': datetime.now(),
                        'state': 'qc_approved'
                    })
                mess = {
                    'message': gate_id.name,
                    }
        return json.dumps(mess)

    @http.route('/api/search/qc_scan', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def list_purchase_scan(self, **post):
        dr_name = post.get(u'dr_name')
        gate_id = request.env['ned.security.gate.queue'].sudo().search([('name','=',dr_name)], limit=1)
        if not gate_id:
            mess = 'DR does not exist.'
            return json.dumps([{"message": mess}])
        else:
            if gate_id.state != 'qc_approved':
                mess = {
                    'message': 'This ticket has been approved.',
                    }
                return json.dumps(mess)
            else:
                mess = {
                    'message': gate_id.id,
                    }
        return json.dumps(mess)

# Onchange for DR ticket
    @http.route('/api/search/dr_ticket_onchange', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def dr_ticket_onchange(self, **post):
        # Find & get DR ID
        # gate_id = post.get('gate_id')
        gate_id = post.get('gate_id')
        if gate_id and isinstance(gate_id, str):
            gate_id = int(post.get('gate_id')) or 0
        sample_weight = post.get('sample_weight')
        if sample_weight and isinstance(sample_weight, str):
            sample_weight = int(post.get('sample_weight')) or 0
        bb_sample_weight = post.get('bb_sample_weight')
        if bb_sample_weight and isinstance(bb_sample_weight, str):
            bb_sample_weight = int(post.get('bb_sample_weight')) or 0
        mc_degree = self._get_numeric(post.get('mc_degree'))
        fm_gram = self._get_numeric(post.get('fm_gram'))
        black_gram = self._get_numeric(post.get('black_gram'))
        broken_gram = self._get_numeric(post.get('broken_gram'))
        brown_gram = self._get_numeric(post.get('brown_gram'))
        mold_gram = self._get_numeric(post.get('mold_gram'))
        cherry_gram = self._get_numeric(post.get('cherry_gram'))
        excelsa_gram = self._get_numeric(post.get('excelsa_gram'))
        screen20_gram = self._get_numeric(post.get('screen20_gram'))
        screen19_gram = self._get_numeric(post.get('screen19_gram'))
        screen18_gram = self._get_numeric(post.get('screen18_gram'))
        screen16_gram = self._get_numeric(post.get('screen16_gram'))
        screen13_gram = self._get_numeric(post.get('screen13_gram'))
        belowsc12_gram = self._get_numeric(post.get('belowsc12_gram'))
        burned_gram = self._get_numeric(post.get('burned_gram'))
        insect_gram = self._get_numeric(post.get('insect_gram'))
        immature_gram = self._get_numeric(post.get('immature_gram'))

        if gate_id: 
            gate_id = request.env['ned.security.gate.queue'].sudo().browse(gate_id)
        if not gate_id:
            mess = {'message': 'DR ticket does not exist.',}
        else:
            if sample_weight == 0 or bb_sample_weight == 0:
                mess = {'message': 'Sample weight and BB Sample weight must be greater than 0',}
            else:
                # Onchange event
                mess = {}
                gate_id.sample_weight = sample_weight
                gate_id.bb_sample_weight = bb_sample_weight
                if mc_degree:
                    gate_id.mc_degree = mc_degree
                    mc = gate_id._percent_mc() or 0.0
                    mess = {'mc_percent': round(mc,2),}

                if fm_gram:
                    gate_id.fm_gram = fm_gram
                    fm = gate_id._percent_fm() or 0.0
                    gate_id.fm=fm
                    mess.update({'fm_percent': round(fm,2),})
                # black broken brown
                if black_gram:
                    gate_id.black_gram = black_gram
                    black = gate_id._percent_black() or 0.0
                    gate_id.black  = black
                    mess.update({'black_percent': round(black,2),})
                if broken_gram:
                    gate_id.broken_gram = broken_gram
                    broken = gate_id._percent_broken() or 0.0
                    gate_id.broken = broken
                    mess.update({'broken_percent': round(broken,2),})
                if brown_gram:
                    gate_id.brown_gram = brown_gram
                    brown = gate_id._percent_brown() or 0.0
                    gate_id.brown = brown
                    mess.update({'brown_percent': round(brown,2),})

                if mold_gram:
                    gate_id.mold_gram = mold_gram
                    mold = gate_id._percent_mold() or 0.0
                    gate_id.mold=mold
                    mess.update({'mold_percent': round(mold,2),})
                if cherry_gram:
                    gate_id.cherry_gram = cherry_gram
                    cherry = gate_id._percent_cherry() or 0.0
                    mess.update({'cherry_percent': round(cherry,2),})
                if excelsa_gram:
                    gate_id.excelsa_gram = excelsa_gram
                    excelsa = gate_id._percent_excelsa() or 0.0
                    gate_id.excelsa=excelsa
                    mess.update({'excelsa_percent': round(excelsa,2),})
                # SCR18 -> 20
                if screen20_gram:
                    gate_id.screen20_gram = screen20_gram
                    screen20 = gate_id._percent_screen20() or 0.0
                    gate_id.screen20 = screen20
                    mess.update({'screen20_percent': round(screen20,2),})
                if screen19_gram:
                    gate_id.screen19_gram = screen19_gram
                    screen19 = gate_id._percent_screen19() or 0.0
                    gate_id.screen19 = screen19
                    mess.update({'screen19_percent': round(screen19,2),})
                if screen18_gram:
                    gate_id.screen18_gram = screen18_gram
                    screen18 = gate_id._percent_screen18() or 0.0
                    gate_id.screen18 = screen18
                    mess.update({'screen18_percent': round(screen18,2),})
                if screen16_gram:
                    gate_id.screen16_gram = screen16_gram
                    screen16 = gate_id._percent_screen16() or 0.0
                    gate_id.screen16 = screen16
                    mess.update({'screen16_percent': round(screen16,2),})
                if screen13_gram:
                    gate_id.screen13_gram = screen13_gram
                    screen13 = gate_id._percent_screen13() or 0.0
                    gate_id.screen13 = screen13
                    mess.update({'screen13_percent': round(screen13,2),})
                if belowsc12_gram:
                    gate_id.belowsc12_gram = belowsc12_gram
                    belowsc12 = gate_id._percent_belowsc12() or 0.0
                    gate_id.belowsc12 = belowsc12
                    mess.update({'belowsc12_percent': round(belowsc12,2),})
                # SCR12
                if belowsc12_gram or screen13_gram or screen16_gram or screen18_gram or screen19_gram or screen20_gram:                
                    greatersc12_gram = gate_id._greatersc12_gram() or 0.0
                    mess.update({'greatersc12_gram': round(greatersc12_gram,2),})
                    greatersc12 = gate_id._percent_greatersc12() or 0.0
                    mess.update({'greatersc12_percent': round(greatersc12,2),})

                if burned_gram:
                    gate_id.burned_gram = burned_gram
                    burned = gate_id._percent_burned() or 0.0
                    gate_id.burned = burned
                    mess.update({'burned_percent': round(burned,2),})
                if insect_gram:
                    gate_id.insect_gram = insect_gram
                    insect = gate_id._percent_insect() or 0.0
                    gate_id.insect = insect
                    mess.update({'insect_percent': round(insect,2),})
                if immature_gram:
                    gate_id.immature_gram = immature_gram
                    immature = gate_id._percent_immature() or 0.0
                    gate_id.immature = immature
                    mess.update({'immature_percent': round(immature,2),})
                if mess == {}:
                    mess = {'message': 'No quality criteria have been entered to calculate the deduction',}
        return json.dumps(mess)
# Cong thuc rieng cho insect
    @api.depends('bb_sample_weight','insect_gram')
    def _percent_insect(self):
        for this in self:
            if this.bb_sample_weight > 0 and this.insect_gram > 0:
                insect = this.insect_gram / this.bb_sample_weight or 0.0000
                this.insect = insect * 100
            else:
                this.insect = 0.0
            return this.insect

# QC Approve DR ticket
    @http.route('/api/search/qc_approve', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def list_qc_approve(self, **post):
        gate_id = post.get('gate_id')
        sample_weight = post.get('sample_weight')
        if sample_weight and isinstance(sample_weight, str):
            sample_weight = int(post.get('sample_weight')) or 0
        bb_sample_weight = post.get('bb_sample_weight')
        if bb_sample_weight and isinstance(bb_sample_weight, str):
            bb_sample_weight = int(post.get('bb_sample_weight')) or 0
        mc_degree = self._get_numeric(post.get('mc_degree'))
        fm_gram = self._get_numeric(post.get('fm_gram'))
        black_gram = self._get_numeric(post.get('black_gram'))
        broken_gram = self._get_numeric(post.get('broken_gram'))
        brown_gram = self._get_numeric(post.get('brown_gram'))
        mold_gram = self._get_numeric(post.get('mold_gram'))
        cherry_gram = self._get_numeric(post.get('cherry_gram'))
        excelsa_gram = self._get_numeric(post.get('excelsa_gram'))
        screen20_gram = self._get_numeric(post.get('screen20_gram'))
        screen19_gram = self._get_numeric(post.get('screen19_gram'))
        screen18_gram = self._get_numeric(post.get('screen18_gram'))
        screen16_gram = self._get_numeric(post.get('screen16_gram'))
        screen13_gram = self._get_numeric(post.get('screen13_gram'))
        belowsc12_gram = self._get_numeric(post.get('belowsc12_gram'))
        burned_gram = self._get_numeric(post.get('burned_gram'))
        insect_gram = self._get_numeric(post.get('insect_gram'))
        immature_gram = self._get_numeric(post.get('immature_gram'))
        mc_percent = self._get_numeric(post.get('mc_percent'))
        fm_percent = self._get_numeric(post.get('fm_percent'))
        black_percent = self._get_numeric(post.get('black_percent'))
        broken_percent = self._get_numeric(post.get('broken_percent'))
        brown_percent = self._get_numeric(post.get('brown_percent'))
        mold_percent = self._get_numeric(post.get('mold_percent'))
        cherry_percent = self._get_numeric(post.get('cherry_percent'))
        excelsa_percent = self._get_numeric(post.get('excelsa_percent'))
        screen20_percent = self._get_numeric(post.get('screen20_percent'))
        screen19_percent = self._get_numeric(post.get('screen19_percent'))
        screen18_percent = self._get_numeric(post.get('screen18_percent'))
        screen16_percent = self._get_numeric(post.get('screen16_percent'))
        screen13_percent = self._get_numeric(post.get('screen13_percent'))
        greatersc12_gram = self._get_numeric(post.get('greatersc12_gram'))
        greatersc12_percent = self._get_numeric(post.get('greatersc12_percent'))
        belowsc12_percent = self._get_numeric(post.get('belowsc12_percent'))
        burned_percent = self._get_numeric(post.get('burned_percent'))
        insect_percent = self._get_numeric(post.get('insect_percent'))
        immature_percent = self._get_numeric(post.get('immature_percent'))
        odor = post.get('odor')
        remarks = post.get('remarks')
        dr_state = post.get(u'dr_state')
        if gate_id and isinstance(gate_id, str):
            gate_id = int(post.get('gate_id'))
        if gate_id: 
            gate_id = request.env['ned.security.gate.queue'].sudo().browse(gate_id)
        # print gate_id
        if not gate_id:
            mess = {
                'message': 'DR ticket does not exist.',
                }
            return json.dumps(mess)
        else:
            if gate_id.state != 'qc_approved':
                mess = {
                    'message': 'This ticket has been approved.',
                    }
                return json.dumps(mess)
            else:
                if dr_state == 'approve':
                    gate_id.sudo().update({
                            'sample_weight': sample_weight,
                            'bb_sample_weight': bb_sample_weight,
                            'mc_degree': mc_degree,
                            'mc': mc_percent,
                            'fm_gram': fm_gram,
                            'fm': fm_percent,
                            'black_gram': black_gram,
                            'black': black_percent,
                            'broken_gram': broken_gram,
                            'broken': broken_percent,
                            'brown_gram': brown_gram,
                            'brown': brown_percent,
                            'mold_gram': mold_gram,
                            'mold': mold_percent,
                            'cherry_gram': cherry_gram,
                            'cherry': cherry_percent,
                            'excelsa_gram': excelsa_gram,
                            'excelsa': excelsa_percent,
                            'screen20_gram': screen20_gram,
                            'screen20': screen20_percent,
                            'screen19_gram': screen19_gram,
                            'screen19': screen19_percent,
                            'screen18_gram': screen18_gram,
                            'screen18': screen18_percent,
                            'screen16_gram': screen16_gram,
                            'screen16': screen16_percent,
                            'screen13_gram': screen13_gram,
                            'screen13': screen13_percent,
                            'greatersc12_gram': greatersc12_gram,
                            'greatersc12': greatersc12_percent,
                            'belowsc12_gram': belowsc12_gram,
                            'belowsc12': belowsc12_percent,
                            'burned_gram': burned_gram,
                            'burned': burned_percent,
                            'insect_gram': insect_gram,
                            'insect': insect_percent,
                            'immature_gram': immature_gram,
                            'immature': immature_percent,
                            'odor': odor,
                            'remarks': remarks,
                            'state': 'wh_approved',
                            'date_approve': datetime.now().strftime(DEFAULT_SERVER_DATETIME_FORMAT)
                        })
                    mess = {
                        'message': ' QC Approved.',
                        }
                    return json.dumps(mess)
                elif dr_state == 'reject':
                    gate_id.sudo().update({
                            'state': 'reject',
                        })
                    mess = {
                        'message': ' QC Rejected.',
                        }
                    return json.dumps(mess)
                else:
                    gate_id.sudo().update({
                            'state': 'cancel',
                        })
                    mess = {
                        'message': ' QC Cancelled.',
                        }
                    return json.dumps(mess)

                # Create Picking
                # flag = False
                # license_plate = ''
                # l = 0
                # while l < len(gate_id.license_plate.strip()):
                #     if gate_id.license_plate[l] not in utr:
                #         license_plate += gate_id.license_plate[l]
                #     l+=1
                # for maxdate in request.env['stock.picking'].sudo().search([('partner_id','=',gate_id.supplier_id.id),
                #                                               ('transfer_picking_type','=',True),
                #                                               ('check_link_backorder','=',False),
                #                                               ('state','=','done')], order='date_done desc', limit=1):
                #     vehicle_no = ''
                #     i =0
                #     if maxdate.vehicle_no:

                #         for pick in request.env['stock.picking'].sudo().search([('partner_id','=',gate_id.supplier_id.id),
                #                                                       ('transfer_picking_type','=',True),
                #                                                       ('check_link_backorder','=',False),
                #                                                       ('state','=','done'),
                #                                                       ('date_done','<=',str(maxdate.date_done)[0:10] + ' 23:59:59'),
                #                                                       ('date_done','>=',str(maxdate.date_done)[0:10] + ' 00:00:00')]):                    
                #             vehicle_no = ''
                #             i =0
                #             if pick.vehicle_no:
                #                 while i < len(pick.vehicle_no.strip()):
                #                     if pick.vehicle_no[i] not in utr:
                #                         vehicle_no += pick.vehicle_no[i]
                #                     i+=1
                #                 if license_plate.lower() == vehicle_no.lower():
                #                     flag = True
                #                     new_picking_id = request.env['stock.picking'].sudo().create_pick(pick,gate_id.picking_type_id,pick.location_dest_id.id,gate_id.warehouse_id.wh_input_stock_loc_id.id)
                #                     request.env['stock.picking'].sudo().search([('backorder_id','=',pick.id)]).write({'security_gate_id':gate_id.id,
                #                                                                                                 'districts_id':gate_id.districts_id.id})

                #                     mess = {
                #                         'message': gate_id.name,
                #                         'picking_id': new_picking_id.name,
                #                         }
                #                     return json.dumps(mess)
                # if not flag:
                #     stock_picking_data = {
                #         'origin': gate_id.name,
                #         'warehouse_id': gate_id.warehouse_id.id,
                #         'partner_id': gate_id.supplier_id.id, 
                #         'vehicle_no': gate_id.license_plate, 
                #         'picking_type_id': gate_id.picking_type_id.id,
                #         'location_id': gate_id.picking_type_id.default_location_src_id.id or False, 
                #         'location_dest_id': gate_id.warehouse_id.wh_input_stock_loc_id.id, 
                #         'certificate_id': gate_id.certificate_id.id or False, 
                #         'estimated_bags': gate_id.estimated_bags or False,
                #         'security_gate_id':gate_id.id,
                #         'date_done':datetime.now(),
                #         'districts_id':gate_id.districts_id.id,
                #     }
                #     new_picking_id = request.env['stock.picking'].sudo().create(stock_picking_data)
                # # print pick.id, pick.name
                #     mess = {
                #         'message': gate_id.name,
                #         'picking_id': new_picking_id.name,
                #         }
                #     return json.dumps(mess)


    @http.route('/api/search/res_districts', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_res_districts(self):
        sql = '''SELECT id, name FROM res_district Where active=True; '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)


    @http.route('/api/search/building', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_building(self):
        sql = '''SELECT id, name FROM building_warehouse;'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/search/stock_zone', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def list_stock_zone(self, **post):
        warehouse_id = post.get('warehouse_id')
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))

        warehouse_id_list = post.get('warehouse_id_list')
        print(warehouse_id)
        sql = ''
        if warehouse_id:
            sql = '''SELECT id, name, warehouse_id from stock_zone
                WHERE warehouse_id = %s and warehouse_id is not null and active = True; '''%(warehouse_id)
        else:
            sql = '''SELECT id, name, warehouse_id from stock_zone
                WHERE warehouse_id in (%s) and warehouse_id is not null and active = True; '''%(warehouse_id_list)

        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)


    @http.route('/api/search/stock_stack', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def list_stock_stack(self, **post):
        warehouse_id = post.get('warehouse_id')
        zone_id = post.get('zone_id')
        stack_max_id = post.get('stack_max_id')
        query=''
        query1=''
        sql=''
        # print warehouse_id
        if warehouse_id and isinstance(warehouse_id, str):
            warehouse_id = int(post.get('warehouse_id'))
        if zone_id and isinstance(zone_id, str):
            zone_id = int(post.get('zone_id'))
            query=' and ss.zone_id = %s '%(zone_id)
        if stack_max_id and isinstance(stack_max_id, str):
            stack_max_id = int(post.get('stack_max_id'))
            query1=' and ss.id > %s '%(stack_max_id)

        warehouse_id_list = post.get('warehouse_id_list')

        # print stack_max_id
        if zone_id == 'None' or zone_id == '':
            if warehouse_id:
                sql = '''SELECT ss.id, ss.name, ss.init_qty, ss.zone_id, sz.name zone_name, CAST(ss.create_date AS TEXT), ss.product_id
                    from stock_lot ss
                    JOIN stock_zone sz ON sz.id = ss.zone_id
                    WHERE ss.warehouse_id = %s and ss.active = True AND ss.init_invetory = False 
                    and (ss.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '12 month') or ss.init_qty > 0) Order By ss.init_qty desc
                    ; '''%(warehouse_id)
            else:
                sql = '''SELECT ss.id, ss.name, ss.init_qty, ss.zone_id, sz.name zone_name, CAST(ss.create_date AS TEXT), ss.product_id
                    from stock_lot ss
                    JOIN stock_zone sz ON sz.id = ss.zone_id
                    WHERE ss.warehouse_id in (%s) and ss.active = True AND ss.init_invetory = False 
                    and (ss.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '12 month') or ss.init_qty > 0) Order By ss.init_qty desc
                    ; '''%(warehouse_id_list)
        else:
            if warehouse_id:
                sql = '''SELECT ss.id, ss.name, ss.init_qty, ss.zone_id, sz.name zone_name, CAST(ss.create_date AS TEXT), ss.product_id
                    from stock_lot ss
                    JOIN stock_zone sz ON sz.id = ss.zone_id
                    WHERE ss.warehouse_id = %s and ss.active = True AND ss.init_invetory = False %s 
                    and (ss.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '12 month') or ss.init_qty > 0) Order By ss.init_qty desc
                    ; '''%(warehouse_id,query)
            else:
                sql = '''SELECT ss.id, ss.name, ss.init_qty, ss.zone_id, sz.name zone_name, CAST(ss.create_date AS TEXT), ss.product_id
                    from stock_lot ss
                    JOIN stock_zone sz ON sz.id = ss.zone_id
                    WHERE ss.warehouse_id in (%s) and ss.active = True AND ss.init_invetory = False %s 
                    and (ss.create_date >= date_trunc('month', CURRENT_DATE - INTERVAL '12 month') or ss.init_qty > 0) Order By ss.init_qty desc
                    ; '''%(warehouse_id_list, query)

                    # And date(timezone('UTC',ss.date::timestamp)) >= date(TIMESTAMP '2018/11/01') or ss.init_qty>0 
        # print sql
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)



    @http.route('/api/search/delivery_order', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def list_delivery_order(self):
        sql = '''SELECT id from delivery_order where state ='approved' and picking_id is null; '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    # QC App phần nhập quality GRN trên mobile

    @http.route('/api/search/getlist_grn_qc', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def getlist_grn_qc(self):
        sql = '''SELECT sp.id, sp.name grn_name, sw.name warehouse_name, rp.name supplier_name, sp.vehicle_no vehicle, sp.warehouse_id,
                sz.name zone_name, ss.name stack_name, sm.init_qty, sec.name dr_name, pp.default_code product, sp.use_sample
                FROM stock_picking sp
                LEFT JOIN ned_security_gate_queue sec ON sp.security_gate_id=sec.id
                JOIN stock_warehouse sw ON sp.warehouse_id=sw.id
                LEFT JOIN res_partner rp ON sp.partner_id=rp.id
                JOIN product_product pp ON pp.id=sp.product_id
                LEFT JOIN stock_move_line sm ON sp.id=sm.picking_id
                LEFT JOIN stock_stack ss ON sp.id=ss.picking_id
                LEFT JOIN stock_zone sz ON ss.zone_id=sz.id
                WHERE sp.state = 'assigned' And sp.state_kcs='draft' And sp.picking_type_code  = 'incoming'; '''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/search/update_grn_use_sample', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def update_grn_use_sample(self, **post):
        grn_id = post.get('grn_id')
        if grn_id and isinstance(grn_id, str):
            grn_id = int(post.get('grn_id')) or 0

        use_sample = post.get('use_sample')
        if use_sample == 'False' or use_sample == '' or use_sample == 'false' or use_sample == '0':
            use_sample = False
        else:
            use_sample = True
        sp_id = request.env['stock.picking'].sudo().search([('id','=',grn_id)], limit=1)
        # use_sample_state = sp_id.use_sample
        if sp_id.use_sample != use_sample:
            sql = '''UPDATE stock_picking SET use_sample = %s
                    WHERE id = %s'''%(use_sample,grn_id)
            request.cr.execute(sql)
            mess = {'message': sp_id.name + ' updated.',}
        else:
            mess = {'message': 'Nothing change.',}
        return json.dumps(mess)

    @http.route('/api/search/getlist_qc_sample', type='http', methods=['GET'], auth='none', website = True, csrf=False)
    def getlist_qc_sample(self):
        sql = '''SELECT sp.*, rp.name supplier_name, pp.default_code product
                FROM kcs_sample sp
                LEFT JOIN res_partner rp ON sp.partner_id=rp.id
                JOIN product_product pp ON pp.id=sp.product_id'''
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/search/getlist_grn_for_qc_sample', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def getlist_grn_for_qc_sample(self, **post):
        sample_id = post.get('sample_id')
        if sample_id and isinstance(sample_id, str):
            sample_id = 'AND kcs_sp.id = %s'%(int(post.get('sample_id')))
        else:
            sample_id = 'AND kcs_sp.id is null'
        sql = '''SELECT kcs_sp.id sample_id, kcs_sp.name sample_name, sp.id grn_id, sp.name grn_name
                FROM stock_picking sp
                LEFT JOIN kcs_sample_stock_picking_rel kcs_rel On kcs_rel.picking_id=sp.id
                LEFT JOIN kcs_sample kcs_sp On kcs_rel.kcs_sample_id=kcs_sp.id
                WHERE sp.use_sample = True %s'''%(sample_id)
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'No GRN found in ready state.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/search/scan_grn_qc', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def scan_grn_qc(self, **post):
        dr_name = post.get(u'dr_name')
        gate_id = request.env['ned.security.gate.queue'].sudo().search([('name','=',dr_name)], limit=1)

        if not gate_id:
            mess = {
                'message': 'Record does not exist.',
                }
            # return json.dumps([{"message": mess}])
        else:
            grn_id = request.env['stock.picking'].sudo().search([('security_gate_id','=',gate_id.id)], limit=1)
            # print gate_id
            if not grn_id:
                mess = {'GRN does not exist.',}
                # return json.dumps([{"message": mess}])
            else:
                if grn_id.state_kcs == 'approved':
                    mess = {
                        'message': 'This ticket has been approved.',
                        }
                    # return json.dumps(mess)
                elif grn_id.state == 'assigned' and grn_id.state_kcs == 'draft':
                    rkl_id = request.env['request.kcs.line'].sudo().search([('picking_id','=',grn_id.id)], limit=1)
                    if not rkl_id:
                        grn_id.btt_loads()

                    mess = {
                        'message': grn_id.id,
                        }                    
                else:
                    mess = {
                        'message': 'GRN does not exist.',
                        }
        return json.dumps(mess)

    @http.route('/api/search/quality_detail_onchange', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def quality_detail_onchange(self, **post):
        # Find & get grn_id
        grn_id = post.get('grn_id')
        if grn_id and isinstance(grn_id, str):
            grn_id = int(post.get('grn_id')) or 0
        sample_weight = post.get('sample_weight')
        if sample_weight and isinstance(sample_weight, str):
            sample_weight = int(post.get('sample_weight')) or 0
        bb_sample_weight = post.get('bb_sample_weight')
        if bb_sample_weight and isinstance(bb_sample_weight, str):
            bb_sample_weight = int(post.get('bb_sample_weight')) or 0
        mc_degree = self._get_numeric(post.get('mc_degree'))
        fm_gram = self._get_numeric(post.get('fm_gram'))
        black_gram = self._get_numeric(post.get('black_gram'))
        broken_gram = self._get_numeric(post.get('broken_gram'))
        brown_gram = self._get_numeric(post.get('brown_gram'))
        mold_gram = self._get_numeric(post.get('mold_gram'))
        cherry_gram = self._get_numeric(post.get('cherry_gram'))
        excelsa_gram = self._get_numeric(post.get('excelsa_gram'))
        screen20_gram = self._get_numeric(post.get('screen20_gram'))
        screen19_gram = self._get_numeric(post.get('screen19_gram'))
        screen18_gram = self._get_numeric(post.get('screen18_gram'))
        screen16_gram = self._get_numeric(post.get('screen16_gram'))
        screen13_gram = self._get_numeric(post.get('screen13_gram'))
        belowsc12_gram = self._get_numeric(post.get('belowsc12_gram'))
        burned_gram = self._get_numeric(post.get('burned_gram'))
        eaten_gram = self._get_numeric(post.get('insect_gram'))
        immature_gram = self._get_numeric(post.get('immature_gram'))
        deduction_manual = self._get_numeric(post.get('deduction_manual'))
        check_deduction = post.get('check_deduction')

        # Find & get request kcs id
        # sp_id = request.env['stock_picking'].sudo().search([('id','=',grn_id)])
        # use_sample = sp_id.use_sample
        sp_rkl_id = request.env['request.kcs.line'].sudo().search([('picking_id','=',grn_id)])
        if not sp_rkl_id:
            mess = {'message': 'Request KCS Line does not exist.',}
        else:
            rkl_id = request.env['request.kcs.line'].sudo().browse(sp_rkl_id.id)
            if sample_weight == 0 or bb_sample_weight == 0:
                mess = {'message': 'Sample weight and BB Sample weight must be greater than 0',}
            else:
                # Onchange event
                mess = {}
                rkl_id.sample_weight = sample_weight
                rkl_id.bb_sample_weight = bb_sample_weight
                if mc_degree:
                    rkl_id.mc_degree = mc_degree
                    mc = rkl_id._percent_mc() or 0.0
                    mc_deduct = rkl_id._mc_deduct() or 0.0
                    rkl_id.mc_deduct = mc_deduct
                    mess = {'mc_percent': round(mc,2), 'mc_deduct': round(mc_deduct,2),}

                if fm_gram:
                    rkl_id.fm_gram = fm_gram
                    fm = rkl_id._percent_fm() or 0.0
                    rkl_id.fm=fm
                    fm_deduct = rkl_id._fm_deduct() or 0.0
                    rkl_id.fm_deduct = fm_deduct
                    mess.update({'fm_percent': round(fm,2),'fm_deduct': round(fm_deduct,2),})
                # black broken brown
                if black_gram:
                    rkl_id.black_gram = black_gram
                    black = rkl_id._percent_black() or 0.0
                    rkl_id.black  = black
                    mess.update({'black_percent': round(black,2),})
                if broken_gram:
                    rkl_id.broken_gram = broken_gram
                    broken = rkl_id._percent_broken() or 0.0
                    rkl_id.broken = broken
                    mess.update({'broken_percent': round(broken,2),})
                if black_gram or broken_gram:
                    broken_deduct = rkl_id._broken_deduct() or 0.0
                    rkl_id.broken_deduct = broken_deduct
                    mess.update({'broken_deduct': round(broken_deduct,2),})
                if brown_gram:
                    rkl_id.brown_gram = brown_gram
                    brown = rkl_id._percent_brown() or 0.0
                    rkl_id.brown = brown
                    mess.update({'brown_percent': round(brown,2),})
                    brown_deduct = rkl_id._brown_deduct() or 0.0
                    rkl_id.brown_deduct = brown_deduct
                    mess.update({'brown_deduct': round(brown_deduct,2),})
                # BBB
                if black_gram or broken_gram or brown_gram:
                    bbb_deduct = rkl_id._bbb_deduct() or 0.0
                    rkl_id.bbb = bbb_deduct
                    mess.update({'bbb_deduct': round(bbb_deduct,2),})

                if mold_gram:
                    rkl_id.mold_gram = mold_gram
                    mold = rkl_id._percent_mold() or 0.0
                    rkl_id.mold=mold
                    mold_deduct = rkl_id._mold_deduct() or 0.0
                    rkl_id.mold_deduct = mold_deduct
                    mess.update({'mold_percent': round(mold,2),'mold_deduct': round(mold_deduct,2),})
                if cherry_gram:
                    rkl_id.cherry_gram = cherry_gram
                    cherry = rkl_id._percent_cherry() or 0.0
                    mess.update({'cherry_percent': round(cherry,2),})
                if excelsa_gram:
                    rkl_id.excelsa_gram = excelsa_gram
                    excelsa = rkl_id._percent_excelsa() or 0.0
                    rkl_id.excelsa=excelsa
                    excelsa_deduct = rkl_id._excelsa_deduct() or 0.0
                    rkl_id.excelsa_deduct = excelsa_deduct
                    mess.update({'excelsa_percent': round(excelsa,2),'excelsa_deduct': round(excelsa_deduct,2),})
                # SCR18 -> 20
                if screen20_gram:
                    rkl_id.screen20_gram = screen20_gram
                    screen20 = rkl_id._percent_screen20() or 0.0
                    rkl_id.screen20 = screen20
                    mess.update({'screen20_percent': round(screen20,2),})
                if screen19_gram:
                    rkl_id.screen19_gram = screen19_gram
                    screen19 = rkl_id._percent_screen19() or 0.0
                    rkl_id.screen19 = screen19
                    mess.update({'screen19_percent': round(screen19,2),})
                if screen18_gram:
                    rkl_id.screen18_gram = screen18_gram
                    screen18 = rkl_id._percent_screen18() or 0.0
                    rkl_id.screen18 = screen18
                    mess.update({'screen18_percent': round(screen18,2),})
                if screen18_gram or screen19_gram or screen20_gram:
                    oversc18_deduct = rkl_id._screen18_deduct() or 0.0
                    rkl_id.oversc18 = oversc18_deduct
                    mess.update({'screen18_deduct': round(oversc18_deduct,2),})
                if screen16_gram:
                    rkl_id.screen16_gram = screen16_gram
                    screen16 = rkl_id._percent_screen16() or 0.0
                    rkl_id.screen16 = screen16
                    mess.update({'screen16_percent': round(screen16,2),})
                if screen16_gram or screen18_gram or screen19_gram or screen20_gram:
                    oversc16_deduct = rkl_id._screen16_deduct() or 0.0
                    rkl_id.oversc16 = oversc16_deduct
                    mess.update({'screen16_deduct': round(oversc16_deduct,2),})
                if screen13_gram:
                    rkl_id.screen13_gram = screen13_gram
                    screen13 = rkl_id._percent_screen13() or 0.0
                    rkl_id.screen13 = screen13
                    mess.update({'screen13_percent': round(screen13,2),})
                if screen13_gram or screen16_gram or screen18_gram or screen19_gram or screen20_gram:
                    oversc13_deduct = rkl_id._screen13_deduct() or 0.0
                    rkl_id.oversc13 = oversc13_deduct
                    mess.update({'screen13_deduct': round(oversc13_deduct,2),})
                if belowsc12_gram:
                    rkl_id.belowsc12_gram = belowsc12_gram
                    belowsc12 = rkl_id._percent_belowsc12() or 0.0
                    rkl_id.belowsc12 = belowsc12
                    mess.update({'belowsc12_percent': round(belowsc12,2),})
                    oversc12_deduct = rkl_id._screen12_deduct() or 0.0
                    rkl_id.oversc12 = oversc12_deduct
                    mess.update({'belowsc12_deduct': round(oversc12_deduct,2),})
                # SCR12
                if belowsc12_gram or screen13_gram or screen16_gram or screen18_gram or screen19_gram or screen20_gram:                
                    greatersc12_gram = rkl_id._greatersc12_gram() or 0.0
                    mess.update({'greatersc12_gram': round(greatersc12_gram,2),})
                    greatersc12 = rkl_id._percent_greatersc12() or 0.0
                    mess.update({'greatersc12_percent': round(greatersc12,2),})

                if burned_gram:
                    rkl_id.burned_gram = burned_gram
                    burned = rkl_id._percent_burned() or 0.0
                    rkl_id.burned = burned
                    mess.update({'burned_percent': round(burned,2),})
                    burned_deduct = rkl_id._burned_deduct() or 0.0
                    rkl_id.burned_deduct = burned_deduct
                    mess.update({'burned_deduct': round(burned_deduct,2),})
                if eaten_gram:
                    rkl_id.eaten_gram = eaten_gram
                    eaten = rkl_id._percent_eaten() or 0.0
                    rkl_id.eaten = eaten
                    mess.update({'insect_percent': round(eaten,2),})
                    eaten_deduct = rkl_id._eaten_deduct() or 0.0
                    rkl_id.eaten_deduct = eaten_deduct
                    mess.update({'insect_deduct': round(eaten_deduct,2),})
                if immature_gram:
                    rkl_id.immature_gram = immature_gram
                    immature = rkl_id._percent_immature() or 0.0
                    rkl_id.immature = immature
                    mess.update({'immature_percent': round(immature,2),})
                # Deduction %
                if belowsc12_gram or screen13_gram or screen16_gram or screen18_gram or screen19_gram or screen20_gram or mc_degree or fm_gram or black_gram or broken_gram or brown_gram or mold_gram or excelsa_gram or cherry_gram or burned_gram or eaten_gram:                
                    deduction = rkl_id._compute_deduction_origin() or 0.0
                    rkl_id.deduction = deduction
                    mess.update({'deduction': round(deduction,2),})
                # Deduction Weight & Basis Weight
                    compute_deduction = rkl_id._compute_deduction()
                    rkl_id.qty_reached = compute_deduction[0]
                    rkl_id.basis_weight = compute_deduction[1]
                    mess.update({'deduction_weight': rkl_id.qty_reached, 'basis_weight': rkl_id.basis_weight,})
                if deduction_manual:
                    check_deduction = rkl_id._onchange_deducttion_manual()
                    mess.update({'check_deduction': check_deduction,})
                if check_deduction:
                    deduction_manual = rkl_id._onchange_check_deducttion()
                    mess.update({'deduction_manual': round(deduction_manual[0],2), 'deduction': round(deduction_manual[1],2),})
                if mess == {}:
                    mess = {'message': 'No quality criteria have been entered to calculate the deduction',}
        return json.dumps(mess)

    def _get_numeric(self, number):
        if number and isinstance(number, str):
            new_number = float(number) or 0.0
            return new_number

    @http.route('/api/search/grn_qc_approve', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def grn_qc_approve(self, **post):
        grn_id = post.get('grn_id')
        if grn_id and isinstance(grn_id, str):
            grn_id = int(post.get('grn_id')) or 0
        sample_weight = post.get('sample_weight')
        if sample_weight and isinstance(sample_weight, str):
            sample_weight = int(post.get('sample_weight')) or 0
        bb_sample_weight = post.get('bb_sample_weight')
        if bb_sample_weight and isinstance(bb_sample_weight, str):
            bb_sample_weight = int(post.get('bb_sample_weight')) or 0
        mc_degree = self._get_numeric(post.get('mc_degree'))
        fm_gram = self._get_numeric(post.get('fm_gram'))
        black_gram = self._get_numeric(post.get('black_gram'))
        broken_gram = self._get_numeric(post.get('broken_gram'))
        brown_gram = self._get_numeric(post.get('brown_gram'))
        mold_gram = self._get_numeric(post.get('mold_gram'))
        cherry_gram = self._get_numeric(post.get('cherry_gram'))
        excelsa_gram = self._get_numeric(post.get('excelsa_gram'))
        screen20_gram = self._get_numeric(post.get('screen20_gram'))
        screen19_gram = self._get_numeric(post.get('screen19_gram'))
        screen18_gram = self._get_numeric(post.get('screen18_gram'))
        screen16_gram = self._get_numeric(post.get('screen16_gram'))
        screen13_gram = self._get_numeric(post.get('screen13_gram'))
        belowsc12_gram = self._get_numeric(post.get('belowsc12_gram'))
        burned_gram = self._get_numeric(post.get('burned_gram'))
        eaten_gram = self._get_numeric(post.get('insect_gram'))
        immature_gram = self._get_numeric(post.get('immature_gram'))
        deduction_manual = self._get_numeric(post.get('deduction_manual'))
        check_deduction = post.get('check_deduction')
        mc_percent = self._get_numeric(post.get('mc_percent'))
        mc_deduct = self._get_numeric(post.get('mc_deduct'))
        fm_percent = self._get_numeric(post.get('fm_percent'))
        fm_deduct = self._get_numeric(post.get('fm_deduct'))
        black_percent = self._get_numeric(post.get('black_percent'))
        broken_percent = self._get_numeric(post.get('broken_percent'))
        broken_deduct = self._get_numeric(post.get('broken_deduct'))
        brown_percent = self._get_numeric(post.get('brown_percent'))
        brown_deduct = self._get_numeric(post.get('brown_deduct'))
        bbb_deduct = self._get_numeric(post.get('bbb_deduct'))
        mold_percent = self._get_numeric(post.get('mold_percent'))
        mold_deduct = self._get_numeric(post.get('mold_deduct'))
        cherry_percent = self._get_numeric(post.get('cherry_percent'))
        excelsa_percent = self._get_numeric(post.get('excelsa_percent'))
        excelsa_deduct = self._get_numeric(post.get('excelsa_deduct'))
        screen20_percent = self._get_numeric(post.get('screen20_percent'))
        screen19_percent = self._get_numeric(post.get('screen19_percent'))
        screen18_percent = self._get_numeric(post.get('screen18_percent'))
        screen18_deduct = self._get_numeric(post.get('screen18_deduct'))
        screen16_percent = self._get_numeric(post.get('screen16_percent'))
        screen16_deduct = self._get_numeric(post.get('screen16_deduct'))
        screen13_percent = self._get_numeric(post.get('screen13_percent'))
        screen13_deduct = self._get_numeric(post.get('screen13_deduct'))
        greatersc12_gram = self._get_numeric(post.get('greatersc12_gram'))
        greatersc12_percent = self._get_numeric(post.get('greatersc12_percent'))
        belowsc12_percent = self._get_numeric(post.get('belowsc12_percent'))
        belowsc12_deduct = self._get_numeric(post.get('belowsc12_deduct'))
        burned_percent = self._get_numeric(post.get('burned_percent'))
        burned_deduct = self._get_numeric(post.get('burned_deduct'))
        insect_percent = self._get_numeric(post.get('insect_percent'))
        insect_deduct = self._get_numeric(post.get('insect_deduct'))
        immature_percent = self._get_numeric(post.get('immature_percent'))
        sampler = post.get(u'sampler')
        deduction = self._get_numeric(post.get('deduction'))
        deduction_weight = self._get_numeric(post.get('deduction_weight'))
        basis_weight = self._get_numeric(post.get('basis_weight'))
        origin_deduction = self._get_numeric(post.get('deduction'))
        grn_qc_state = post.get(u'grn_qc_state')

        if check_deduction == 'False' or check_deduction == '' or check_deduction == 'false' or check_deduction == '0':
            check_deduction = False
        else:
            check_deduction = True

        if grn_id: 
            grn_id = request.env['stock.picking'].sudo().browse(grn_id)
        # print gate_id
        if not grn_id:
            mess = {
                'message': 'GRN does not match.',
                }
            # print mess
            return json.dumps(mess)
        else:
            vals ={}
            vals ={'sample_weight': sample_weight,
                    'bb_sample_weight': bb_sample_weight,
                    'mc_degree': mc_degree,
                    'mc': mc_percent,
                    'mc_deduct': mc_deduct,
                    'fm_gram': fm_gram,
                    'fm': fm_percent,
                    'fm_deduct': fm_deduct,
                    'black_gram': black_gram,
                    'black': black_percent,
                    'broken_gram': broken_gram,
                    'broken': broken_percent,
                    'broken_deduct': broken_deduct,
                    'brown_gram': brown_gram,
                    'brown': brown_percent,
                    'brown_deduct': brown_deduct,
                    'bbb': bbb_deduct,
                    'mold_gram': mold_gram,
                    'mold': mold_percent,
                    'mold_deduct': mold_deduct,
                    'cherry_gram': cherry_gram,
                    'cherry': cherry_percent,
                    'excelsa_gram': excelsa_gram,
                    'excelsa': excelsa_percent,
                    'excelsa_deduct': excelsa_deduct,
                    'screen20_gram': screen20_gram,
                    'screen20': screen20_percent,
                    'screen19_gram': screen19_gram,
                    'screen19': screen19_percent,
                    'screen18_gram': screen18_gram,
                    'screen18': screen18_percent,
                    'oversc18': screen18_deduct,
                    'screen16_gram': screen16_gram,
                    'screen16': screen16_percent,
                    'oversc16': screen16_deduct,
                    'screen13_gram': screen13_gram,
                    'screen13': screen13_percent,
                    'oversc13': screen13_deduct,
                    'greatersc12_gram': greatersc12_gram,
                    'greatersc12': greatersc12_percent,
                    'belowsc12_gram': belowsc12_gram,
                    'belowsc12': belowsc12_percent,
                    'oversc12': belowsc12_deduct,
                    'burned_gram': burned_gram,
                    'burned': burned_percent,
                    'burned_deduct': burned_deduct,
                    'eaten_gram': eaten_gram,
                    'eaten': insect_percent,
                    'insect_bean_deduct': insect_deduct,
                    'immature_gram': immature_gram,
                    'immature': immature_percent,
                    'sampler': sampler,
                    'deduction': deduction,
                    'qty_reached': deduction_weight,
                    'basis_weight': basis_weight,
                    'deduction_manual': deduction_manual,
                    'check_deduction': check_deduction,
                    'origin_deduction': deduction,
            }

            rkl_id = request.env['request.kcs.line'].sudo().search([('picking_id','=',grn_id.id)])

            if grn_qc_state == 'approve':
                if grn_id.state_kcs == 'approved':
                    mess = {
                        'message': 'This ticket has been approved.',
                        }
                elif grn_id.state_kcs == 'draft':
                    if not rkl_id:
                        mess = {'message': 'Request KCS Line does not exist.',}
                    else:
                        mess = {}
                        rkl_id.sudo().update(vals)

                        mess = {'message': 'Request KCS Line Approved.',}
                        grn_id.sudo().btt_approved()
                        mess.update({'message': ' GRN also approved.'})
                        return json.dumps(mess)
                else:
                    mess = {'message': 'Something wrong with state_kcs, please check this ticket again!',}
                # print mess
                return json.dumps(mess)

            elif grn_qc_state == 'reject':
                rkl_id.sudo().update(vals)

                mess = {'message': 'Request KCS Line saved.',}
                grn_id.sudo().btt_reject()
                # grn_id.sudo().update({
                #         'state': 'rejected',
                #     })
                mess = {
                    'message': 'GRN rejected.',
                    }
                return json.dumps(mess)
                # print mess

# APPROVE SAMPLE
    @http.route('/api/search/sample_detail_onchange', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def sample_detail_onchange(self, **post):
        # Find & get grn_id
        sample_weight = post.get('sample_weight')
        if sample_weight and isinstance(sample_weight, str):
            sample_weight = int(post.get('sample_weight')) or 0
        bb_sample_weight = post.get('bb_sample_weight')
        if bb_sample_weight and isinstance(bb_sample_weight, str):
            bb_sample_weight = int(post.get('bb_sample_weight')) or 0
        mc_degree = self._get_numeric(post.get('mc_degree'))
        fm_gram = self._get_numeric(post.get('fm_gram'))
        black_gram = self._get_numeric(post.get('black_gram'))
        broken_gram = self._get_numeric(post.get('broken_gram'))
        brown_gram = self._get_numeric(post.get('brown_gram'))
        mold_gram = self._get_numeric(post.get('mold_gram'))
        cherry_gram = self._get_numeric(post.get('cherry_gram'))
        excelsa_gram = self._get_numeric(post.get('excelsa_gram'))
        screen20_gram = self._get_numeric(post.get('screen20_gram'))
        screen19_gram = self._get_numeric(post.get('screen19_gram'))
        screen18_gram = self._get_numeric(post.get('screen18_gram'))
        screen16_gram = self._get_numeric(post.get('screen16_gram'))
        screen13_gram = self._get_numeric(post.get('screen13_gram'))
        belowsc12_gram = self._get_numeric(post.get('belowsc12_gram'))
        burned_gram = self._get_numeric(post.get('burned_gram'))
        eaten_gram = self._get_numeric(post.get('insect_gram'))
        immature_gram = self._get_numeric(post.get('immature_gram'))
        deduction_manual = self._get_numeric(post.get('deduction_manual'))

        rkl_id = request.env['kcs.sample'].sudo().search([], order='id desc', limit=1)
        if sample_weight == 0 or bb_sample_weight == 0:
            mess = {'message': 'Sample weight and BB Sample weight must be greater than 0',}
        else:
            # Onchange event
            mess = {}
            rkl_id.sample_weight = sample_weight
            rkl_id.bb_sample_weight = bb_sample_weight
            rkl_id.categ_id = rkl_id.onchange_product_id()
            if mc_degree:
                rkl_id.mc_degree = mc_degree
                mc = rkl_id._percent_mc() or 0.0
                mc_deduct = rkl_id._mc_deduct() or 0.0
                rkl_id.mc_deduct = mc_deduct
                mess = {'mc_percent': round(mc,2), 'mc_deduct': round(mc_deduct,2),}

            if fm_gram:
                rkl_id.fm_gram = fm_gram
                fm = rkl_id._percent_fm() or 0.0
                rkl_id.fm=fm
                fm_deduct = rkl_id._fm_deduct() or 0.0
                rkl_id.fm_deduct = fm_deduct
                mess.update({'fm_percent': round(fm,2),'fm_deduct': round(fm_deduct,2),})
            # black broken brown
            if black_gram:
                rkl_id.black_gram = black_gram
                black = rkl_id._percent_black() or 0.0
                rkl_id.black  = black
                mess.update({'black_percent': round(black,2),})
            if broken_gram:
                rkl_id.broken_gram = broken_gram
                broken = rkl_id._percent_broken() or 0.0
                rkl_id.broken = broken
                mess.update({'broken_percent': round(broken,2),})
            if black_gram or broken_gram:
                broken_deduct = rkl_id._broken_deduct() or 0.0
                rkl_id.broken_deduct = broken_deduct
                mess.update({'broken_deduct': round(broken_deduct,2),})
            if brown_gram:
                rkl_id.brown_gram = brown_gram
                brown = rkl_id._percent_brown() or 0.0
                rkl_id.brown = brown
                mess.update({'brown_percent': round(brown,2),})
                brown_deduct = rkl_id._brown_deduct() or 0.0
                rkl_id.brown_deduct = brown_deduct
                mess.update({'brown_deduct': round(brown_deduct,2),})
            # BBB
            if black_gram or broken_gram or brown_gram:
                bbb_deduct = rkl_id._bbb_deduct() or 0.0
                rkl_id.bbb = bbb_deduct
                mess.update({'bbb_deduct': round(bbb_deduct,2),})

            if mold_gram:
                rkl_id.mold_gram = mold_gram
                mold = rkl_id._percent_mold() or 0.0
                rkl_id.mold=mold
                mold_deduct = rkl_id._mold_deduct() or 0.0
                rkl_id.mold_deduct = mold_deduct
                mess.update({'mold_percent': round(mold,2),'mold_deduct': round(mold_deduct,2),})
            if cherry_gram:
                rkl_id.cherry_gram = cherry_gram
                cherry = rkl_id._percent_cherry() or 0.0
                mess.update({'cherry_percent': round(cherry,2),})
            if excelsa_gram:
                rkl_id.excelsa_gram = excelsa_gram
                excelsa = rkl_id._percent_excelsa() or 0.0
                rkl_id.excelsa=excelsa
                excelsa_deduct = rkl_id._excelsa_deduct() or 0.0
                rkl_id.excelsa_deduct = excelsa_deduct
                mess.update({'excelsa_percent': round(excelsa,2),'excelsa_deduct': round(excelsa_deduct,2),})
            # SCR18 -> 20
            if screen20_gram:
                rkl_id.screen20_gram = screen20_gram
                screen20 = rkl_id._percent_screen20() or 0.0
                rkl_id.screen20 = screen20
                mess.update({'screen20_percent': round(screen20,2),})
            if screen19_gram:
                rkl_id.screen19_gram = screen19_gram
                screen19 = rkl_id._percent_screen19() or 0.0
                rkl_id.screen19 = screen19
                mess.update({'screen19_percent': round(screen19,0),})
            if screen18_gram:
                rkl_id.screen18_gram = screen18_gram
                screen18 = rkl_id._percent_screen18() or 0.0
                rkl_id.screen18 = screen18
                mess.update({'screen18_percent': round(screen18,2),})
            if screen18_gram or screen19_gram or screen20_gram:
                oversc18_deduct = rkl_id._screen18_deduct() or 0.0
                rkl_id.oversc18 = oversc18_deduct
                mess.update({'screen18_deduct': round(oversc18_deduct,2),})
            if screen16_gram:
                rkl_id.screen16_gram = screen16_gram
                screen16 = rkl_id._percent_screen16() or 0.0
                rkl_id.screen16 = screen16
                mess.update({'screen16_percent': round(screen16,2),})
            if screen16_gram or screen18_gram or screen19_gram or screen20_gram:
                oversc16_deduct = rkl_id._screen16_deduct() or 0.0
                rkl_id.oversc16 = oversc16_deduct
                mess.update({'screen16_deduct': round(oversc16_deduct,2),})
            if screen13_gram:
                rkl_id.screen13_gram = screen13_gram
                screen13 = rkl_id._percent_screen13() or 0.0
                rkl_id.screen13 = screen13
                mess.update({'screen13_percent': round(screen13,2),})
            if screen13_gram or screen16_gram or screen18_gram or screen19_gram or screen20_gram:
                oversc13_deduct = rkl_id._screen13_deduct() or 0.0
                rkl_id.oversc13 = oversc13_deduct
                mess.update({'screen13_deduct': round(oversc13_deduct,2),})
            if belowsc12_gram:
                rkl_id.belowsc12_gram = belowsc12_gram
                belowsc12 = rkl_id._percent_belowsc12() or 0.0
                rkl_id.belowsc12 = belowsc12
                mess.update({'belowsc12_percent': round(belowsc12,2),})
                oversc12_deduct = rkl_id._screen12_deduct() or 0.0
                rkl_id.oversc12 = oversc12_deduct
                mess.update({'belowsc12_deduct': round(oversc12_deduct,2),})
            # SCR12
            if belowsc12_gram or screen13_gram or screen16_gram or screen18_gram or screen19_gram or screen20_gram:                
                greatersc12_gram = rkl_id._greatersc12_gram() or 0.0
                mess.update({'greatersc12_gram': round(greatersc12_gram,2),})
                greatersc12 = rkl_id._percent_greatersc12() or 0.0
                mess.update({'greatersc12_percent': round(greatersc12,2),})

            if burned_gram:
                rkl_id.burned_gram = burned_gram
                burned = rkl_id._percent_burned() or 0.0
                rkl_id.burned = burned
                mess.update({'burned_percent': round(burned,2),})
                burned_deduct = rkl_id._burned_deduct() or 0.0
                rkl_id.burned_deduct = burned_deduct
                mess.update({'burned_deduct': round(burned_deduct,2),})
            if eaten_gram:
                rkl_id.eaten_gram = eaten_gram
                eaten = rkl_id._percent_eaten() or 0.0
                rkl_id.eaten = eaten
                mess.update({'insect_percent': round(eaten,2),})
                insect_bean_deduct = rkl_id._insect_bean_deduct() or 0.0
                rkl_id.insect_bean_deduct = insect_bean_deduct
                mess.update({'insect_deduct': round(insect_bean_deduct,2),})
            if immature_gram:
                rkl_id.immature_gram = immature_gram
                immature = rkl_id._percent_immature() or 0.0
                rkl_id.immature = immature
                mess.update({'immature_percent': round(immature,2),})
            # Deduction %
            # if belowsc12_gram or screen13_gram or screen16_gram or screen18_gram or screen19_gram or screen20_gram or mc_degree or fm_gram or black_gram or broken_gram or brown_gram or mold_gram or excelsa_gram or cherry_gram or burned_gram or eaten_gram:                
            #     print 'AAAAA'
            deduction = rkl_id._compute_deduction() or 0.0
            rkl_id.deduction = deduction
            mess.update({'deduction': round(deduction,2),})
            # else:
            #     print 'BBBBB'

            # Deduction Weight & Basis Weight
                # compute_deduction = rkl_id._compute_deduction()
                # rkl_id.qty_reached = compute_deduction[0]
                # rkl_id.basis_weight = compute_deduction[1]
                # mess.update({'deduction_weight': rkl_id.qty_reached, 'basis_weight': rkl_id.basis_weight,})
            # if deduction_manual:
            #     check_deduction = rkl_id._onchange_deducttion_manual()
            #     mess.update({'check_deduction': check_deduction,})
            # if check_deduction:
            #     deduction_manual = rkl_id._onchange_check_deducttion()
            #     mess.update({'deduction_manual': deduction_manual[0], 'deduction': deduction_manual[1],})
            if mess == {}:
                mess = {'message': 'No quality criteria have been entered to calculate the deduction',}
        return json.dumps(mess)

    @http.route('/api/search/create_new_qc_sample', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def create_new_qc_sample(self, **post):
        partner_id = post.get('partner_id')
        if partner_id and isinstance(partner_id, str):
            partner_id = int(post.get('partner_id')) or 0
        product_id = post.get('product_id')
        if product_id and isinstance(product_id, str):
            product_id = int(post.get('product_id')) or 0

        sample_weight = post.get('sample_weight')
        if sample_weight and isinstance(sample_weight, str):
            sample_weight = int(post.get('sample_weight')) or 0
        bb_sample_weight = post.get('bb_sample_weight')
        if bb_sample_weight and isinstance(bb_sample_weight, str):
            bb_sample_weight = int(post.get('bb_sample_weight')) or 0
        mc_degree = self._get_numeric(post.get('mc_degree'))
        fm_gram = self._get_numeric(post.get('fm_gram'))
        black_gram = self._get_numeric(post.get('black_gram'))
        broken_gram = self._get_numeric(post.get('broken_gram'))
        brown_gram = self._get_numeric(post.get('brown_gram'))
        mold_gram = self._get_numeric(post.get('mold_gram'))
        cherry_gram = self._get_numeric(post.get('cherry_gram'))
        excelsa_gram = self._get_numeric(post.get('excelsa_gram'))
        screen20_gram = self._get_numeric(post.get('screen20_gram'))
        screen19_gram = self._get_numeric(post.get('screen19_gram'))
        screen18_gram = self._get_numeric(post.get('screen18_gram'))
        screen16_gram = self._get_numeric(post.get('screen16_gram'))
        screen13_gram = self._get_numeric(post.get('screen13_gram'))
        belowsc12_gram = self._get_numeric(post.get('belowsc12_gram'))
        burned_gram = self._get_numeric(post.get('burned_gram'))
        eaten_gram = self._get_numeric(post.get('insect_gram'))
        immature_gram = self._get_numeric(post.get('immature_gram'))
        deduction_manual = self._get_numeric(post.get('deduction_manual'))
        mc_percent = self._get_numeric(post.get('mc_percent'))
        mc_deduct = self._get_numeric(post.get('mc_deduct'))
        fm_percent = self._get_numeric(post.get('fm_percent'))
        fm_deduct = self._get_numeric(post.get('fm_deduct'))
        black_percent = self._get_numeric(post.get('black_percent'))
        broken_percent = self._get_numeric(post.get('broken_percent'))
        broken_deduct = self._get_numeric(post.get('broken_deduct'))
        brown_percent = self._get_numeric(post.get('brown_percent'))
        brown_deduct = self._get_numeric(post.get('brown_deduct'))
        bbb_deduct = self._get_numeric(post.get('bbb_deduct'))
        mold_percent = self._get_numeric(post.get('mold_percent'))
        mold_deduct = self._get_numeric(post.get('mold_deduct'))
        cherry_percent = self._get_numeric(post.get('cherry_percent'))
        excelsa_percent = self._get_numeric(post.get('excelsa_percent'))
        excelsa_deduct = self._get_numeric(post.get('excelsa_deduct'))
        screen20_percent = self._get_numeric(post.get('screen20_percent'))
        screen19_percent = self._get_numeric(post.get('screen19_percent'))
        screen18_percent = self._get_numeric(post.get('screen18_percent'))
        screen18_deduct = self._get_numeric(post.get('screen18_deduct'))
        screen16_percent = self._get_numeric(post.get('screen16_percent'))
        screen16_deduct = self._get_numeric(post.get('screen16_deduct'))
        screen13_percent = self._get_numeric(post.get('screen13_percent'))
        screen13_deduct = self._get_numeric(post.get('screen13_deduct'))
        greatersc12_gram = self._get_numeric(post.get('greatersc12_gram'))
        greatersc12_percent = self._get_numeric(post.get('greatersc12_percent'))
        belowsc12_percent = self._get_numeric(post.get('belowsc12_percent'))
        belowsc12_deduct = self._get_numeric(post.get('belowsc12_deduct'))
        burned_percent = self._get_numeric(post.get('burned_percent'))
        burned_deduct = self._get_numeric(post.get('burned_deduct'))
        insect_percent = self._get_numeric(post.get('insect_percent'))
        insect_deduct = self._get_numeric(post.get('insect_deduct'))
        immature_percent = self._get_numeric(post.get('immature_percent'))
        sampler = post.get(u'sampler')
        deduction = self._get_numeric(post.get('deduction'))
        listGRN = post.get('listGRN')
        sample_qc_state = post.get(u'sample_qc_state')


        if sample_qc_state == 'approve':
            vals = {
                'partner_id':partner_id,
                'product_id':product_id,
                'sample_weight': sample_weight,
                'bb_sample_weight': bb_sample_weight,
                'mc_degree': mc_degree,
                'mc': mc_percent,
                'mc_deduct': mc_deduct,
                'fm_gram': fm_gram,
                'fm': fm_percent,
                'fm_deduct': fm_deduct,
                'black_gram': black_gram,
                'black': black_percent,
                'broken_gram': broken_gram,
                'broken': broken_percent,
                'broken_deduct': broken_deduct,
                'brown_gram': brown_gram,
                'brown': brown_percent,
                'brown_deduct': brown_deduct,
                'bbb': bbb_deduct,
                'mold_gram': mold_gram,
                'mold': mold_percent,
                'mold_deduct': mold_deduct,
                'cherry_gram': cherry_gram,
                'cherry': cherry_percent,
                'excelsa_gram': excelsa_gram,
                'excelsa': excelsa_percent,
                'excelsa_deduct': excelsa_deduct,
                'screen20_gram': screen20_gram,
                'screen20': screen20_percent,
                'screen19_gram': screen19_gram,
                'screen19': screen19_percent,
                'screen18_gram': screen18_gram,
                'screen18': screen18_percent,
                'oversc18': screen18_deduct,
                'screen16_gram': screen16_gram,
                'screen16': screen16_percent,
                'oversc16': screen16_deduct,
                'screen13_gram': screen13_gram,
                'screen13': screen13_percent,
                'oversc13': screen13_deduct,
                'greatersc12_gram': greatersc12_gram,
                'greatersc12': greatersc12_percent,
                'belowsc12_gram': belowsc12_gram,
                'belowsc12': belowsc12_percent,
                'oversc12': belowsc12_deduct,
                'burned_gram': burned_gram,
                'burned': burned_percent,
                'burned_deduct': burned_deduct,
                'eaten_gram': eaten_gram,
                'eaten': insect_percent,
                'insect_bean_deduct': insect_deduct,
                'immature_gram': immature_gram,
                'immature': immature_percent,
                'sampler': sampler,
                'deduction': deduction,
                'deduction_manual': deduction_manual,
                }
            sample_name = request.env['kcs.sample'].sudo().create(vals)
            # print sample_name.name, sample_name.id
            sample_id = request.env['kcs.sample'].sudo().search([('id','=',sample_name.id)])
            # sample_id.categ_id = immature_gram
            sample_id.categ_id = sample_id.onchange_product_id()
            # print sample_id.categ_id
            mess = {'message': 'KCS Sample created successfully.',}
            return json.dumps(mess)
        else:
            mess = {'message': 'KCS Sample cancel action.',}
            return json.dumps(mess)


    @http.route('/api/search/create_grn_qc_sample', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def create_grn_qc_sample(self, **post):
        # var = {'partner_id':13936,
        #         'product_id':1176,
        #         'bb_sample_weight':222,
        #         }
        # sample_name = request.env['kcs.sample'].sudo().create(var)
        # print sample_name.name, sample_name.id

        # Test hàm create_tmp_id_sample
        # var = {'partner_id':0,'product_id':0,}
        # sample_name = request.env['kcs.sample'].sudo().create_tmp_id_sample(var)
        # print sample_name.name, sample_name.id
        max_sampleid = request.env['kcs.sample'].sudo().search([], order='id desc', limit=1)
        # name = request.env['kcs.sample'].browse(sec.change_warehouse_id.id).sequence_id.next_by_id()
        # print vals

    def create_tmp_id_sample(self,vals):
        if vals.get('name','/')=='/':
            vals['name'] = request.env['ir.sequence'].next_by_code('kcs.sample') or '/'
        return vals['id']
        # return super(KCSSample, self).create(vals)

    @http.route('/api/search/test_call_api', type='http', methods=['POST'], auth='none', website = True, csrf=False)
    def test_call_api(self, **post):
        grn_id = post.get('grn_id')
        if grn_id and isinstance(grn_id, str):
            grn_id = float(post.get('grn_id'))
        rkl_id = request.env['request.kcs.line'].sudo().search([('picking_id','=',grn_id)])

        mc_degree = post.get('mc')
        if mc_degree and isinstance(mc_degree, str):
            mc_degree = float(post.get('mc'))

        mc_degree = request.env['request.kcs.line'].sudo().browse(rkl_id.id)._percent_mc()



        
        
        
        
        
        
        
        
        
        
        
        
        
        
