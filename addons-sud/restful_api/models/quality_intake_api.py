# -*- coding: utf-8 -*-

# from odoo.http import http
from odoo import SUPERUSER_ID
# from odoo.addons.website import slug, unslug
from odoo.http import route, request, json
from odoo.exceptions import AccessError, UserError
# from models import JWTAuth
from datetime import datetime, date as date_object
from odoo import http



class QualityIntakeAPI(http.Controller):
    
    @http.route('/stock/intake', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_quality_intake(self, **post):
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        sql = ''
        if from_date == 'None' or to_date == 'None' or from_date == '' or to_date == '':
            sql = '''
                SELECT row_number() OVER () AS id, supplier_id, 
                    case when supplier is null then concat('Undefined (',count(*),')') else concat(supplier,' (',count(*),')') End As supplier,
                        sum((screen18 + screen16))/count(*) screen,
                        sum((black + broken))/count(*) BB,
                        sum(basis_weight) balance_basis,
                        count(*) as total_row
                FROM v_qc_details
                WHERE left(receipt_note,3)='GRN'
                    AND date(timezone('UTC',receiving_date::timestamp)) between date(TIMESTAMP 'yesterday') and date(TIMESTAMP 'now')
                GROUP BY supplier_id, supplier
                LIMIT %s OFFSET %s 
                  '''%(limit_size, page_no)
        else:
            sql = '''
                SELECT row_number() OVER () AS id, supplier_id,
                    case when supplier is null then 'Undefined' else supplier End As supplier,
                        sum((screen18 + screen16))/count(*) screen,
                        sum((black + broken))/count(*) BB,
                        sum(basis_weight) balance_basis,
                        count(*) as total_row
                FROM v_qc_details
                WHERE left(receipt_note,3)='GRN'
                    AND DATE(timezone('UTC',receiving_date::timestamp)) between '%s' and '%s'
                GROUP BY supplier_id, supplier
                LIMIT %s OFFSET %s 
                  '''%(from_date, to_date, limit_size, page_no)
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
        
    @http.route('/stock/intake/suplier', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_quality_intake_supplier(self, **post):
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        supplier_id = post.get('supplier_id')
        
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        query =''
        sql = ''
        if supplier_id == None or supplier_id == '' or supplier_id == 'null':
            query = 'supplier_id >=0 or supplier_id is null'
        else:
            query = 'supplier_id = %s'%(supplier_id)
        if from_date == 'None' or to_date == 'None' or from_date == '' or to_date == '':
            sql = '''
                SELECT row_number() OVER () AS id, supplier_id,
                        case when supplier is null then 'Undefined' else supplier End As supplier,
                        stack_id,
                        stack stack_name,
                        receipt_note GRN,
                        (screen18 + screen16) screen,
                        (black + broken) BB,
                        basis_weight balance_basis
                FROM v_qc_details
                WHERE left(receipt_note,3)='GRN'
                    AND date(timezone('UTC',receiving_date::timestamp)) between date(TIMESTAMP 'yesterday') and date(TIMESTAMP 'now')
                    AND %s
                LIMIT %s OFFSET %s 
                  '''%(query, limit_size, page_no)
             
        else:
            sql = '''
                SELECT row_number() OVER () AS id, supplier_id,
                        case when supplier is null then 'Undefined' else supplier End As supplier,
                        stack_id,
                        stack stack_name,
                        receipt_note GRN,
                        (screen18 + screen16) screen,
                        (black + broken) BB,
                        basis_weight balance_basis
                FROM v_qc_details
                WHERE left(receipt_note,3)='GRN'
                    AND DATE(timezone('UTC',receiving_date::timestamp)) between '%s' and '%s'
                AND %s
                LIMIT %s OFFSET %s 
                  '''%(from_date, to_date, query, limit_size, page_no)
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
            
    
    @http.route('/stock/intake/stack', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_quality_intake_stack(self, **post):
#         auth_header = request.httprequest.headers.get('Authenticate')
#         if JWTAuth().decode_token(auth_header) in ('Expired token. Please login to get a new token', 'Invalid token. Please register or login'):
#             return json.dumps({'message':JWTAuth().decode_token(auth_header)})
#         else:
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        stack_id = post.get('stack_id')
        supplier_id = post.get('supplier_id')
        grn_name = post.get('grn_name')
        sql = '''
            SELECT row_number() OVER () AS id, supplier_id,
                    case when supplier is null then 'Undefined' else supplier End As supplier,
                    stack_id,
                    stack,
                    receipt_note GRN,
                    mc,
                    fm,
                    black,
                    broken,
                    brown,
                    mold,
                    cherry,
                    excelsa,
                    screen18,
                    screen16,
                    screen13,
                    greatersc12,
                    belowsc12,
                    burned,
                    eaten,
                    immature,
                    basis_weight balance_basis
            FROM v_qc_details
            WHERE stack_id = %s AND supplier_id = %s AND receipt_note = '%s'
            LIMIT %s OFFSET %s 
              '''%(stack_id, supplier_id, grn_name, limit_size, page_no)

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
            
            
class NPEUnfixedAPI(http.Controller):
    
    @http.route('/api/npe/unfixed', type='http', auth='none', methods=['GET'], website = True, csrf=False)
    def get_npe_unfixed(self):
        sql = '''
            SELECT row_number() OVER () AS id,
                    vnuq.name partner, vnuq.partner_ids,
                    vnuq.province_id, vnuq.province_name,
                    vnuq.qty_contract qty_contract,
                    vnuq.qty_received qty_received,
                    vnuq.to_receive to_receive,
                    vnuq.qty_fixed qty_fixed,
                    vnuq.unfixed unfixed,
                    vnuq.screen18 + vnuq.screen16 screen,
                    vnuq.black + vnuq.broken BB,
                    vnuq.deduction
            FROM v_npe_unfixed_quality vnuq
            GROUP BY 
                    vnuq.name, vnuq.partner_ids,
                    vnuq.province_id, vnuq.province_name,
                    vnuq.qty_contract,
                    vnuq.qty_received,
                    vnuq.to_receive,
                    vnuq.qty_fixed,
                    vnuq.unfixed,
                    vnuq.screen18 + vnuq.screen16,
                    vnuq.black + vnuq.broken,
                    vnuq.deduction
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
        
    @http.route('/npe/unfixed/detail', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_npe_unfixed_detail(self, **post):
        npe = post.get('npe')
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        partner_id = post.get('partner_id')
        sql = '''
            SELECT *
            FROM v_npe_unfixed_detail
            WHERE partner_id = '%s'
            LIMIT %s OFFSET %s
              '''%(partner_id, limit_size, page_no)
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

class ReportAPI(http.Controller):
    
    @http.route('/report', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_row_report(self, **post):
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        year = datetime.now().year
        month = datetime.now().strftime('%m')
        if from_date == 'None' or from_date == '':
            from_date = '01-%s-'%(month) + str(year)
        if to_date == 'None' or to_date == '':
            to_date = datetime.now().date()
            
        sql = '''
            SELECT 'FAQ (FOT-Ned) deviation' as name_report,
                count(*) as item 
            FROM v_grn_matching
            WHERE date(timezone('UTC',factory_date_received::timestamp)) 
                between '%(from_date)s'  and '%(to_date)s'
                
            UNION ALL
            
            SELECT 'FOB Weight Franchise' as name_report,
                count(*) as item 
            FROM v_fob_weight_franchise
            WHERE date(timezone('UTC',shipment_date::timestamp)) 
                between '%(from_date)s'  and '%(to_date)s'
                
            UNION ALL
            
            SELECT 'FOB Diviation' as name_report,
                count(*) as item 
            FROM v_fob_deviation
            WHERE date(timezone('UTC',fob_date::timestamp)) 
                between '%(from_date)s'  and '%(to_date)s'
            LIMIT %(limit_size)s OFFSET %(page_no)s 
              '''%({'page_no': page_no, 
                    'limit_size': limit_size,
                    'from_date': from_date,
                    'to_date': to_date}
                    )
        #print sql
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        return json.dumps(result)
    
    @http.route('/report/fot', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_fot_report(self, **post):
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        year = datetime.now().year
        month = datetime.now().strftime('%m')
        if from_date == 'None' or from_date == '':
            from_date = '01-%s-'%(month) + str(year)
        if to_date == 'None' or to_date == '':
            to_date = datetime.now().date()
            
        sql = '''
            SELECT row_number() OVER () AS id, grn_branch,
                branch_id,
                shortname,
                branch_date_received,
                grn_factory,
                factory_date_received,
                deduction_branch,
                deduction_factory,
                brn_fac,
                deficit,
                net_weight_branch,
                net_weight_factory,
                net_weight_deficit,
                net_var,
                basis_weight_branch,
                basis_weight_factory,
                basis_weight_deficit,
                basis_var,
                mc_branch,
                mc_factory,
                fm_branch,
                fm_factory,
                black_branch,
                black_factory,
                broken_branch,
                broken_factory,
                brown_branch,
                brown_factory,
                cherry_branch,
                cherry_factory,
                screen18_branch,
                screen18_factory,
                screen16_branch,
                screen16_factory,
                screen13_branch,
                screen13_factory,
                belowsc12_branch,
                belowsc12_factory,
                vehicle_no
            FROM v_grn_matching
            WHERE date(timezone('UTC',factory_date_received::timestamp)) 
                between '%(from_date)s'  and '%(to_date)s'
            LIMIT %(limit_size)s OFFSET %(page_no)s 
              '''%({'page_no': page_no, 
                    'limit_size': limit_size,
                    'from_date': from_date,
                    'to_date': to_date}
                    )
        #print sql
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        return json.dumps(result)


    @http.route('/report/franchise', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_franchise_report(self, **post):
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        year = datetime.now().year
        month = datetime.now().strftime('%m')
        if from_date == 'None' or from_date == '':
            from_date = '01-%s-'%(month) + str(year)
        if to_date == 'None' or to_date == '':
            to_date = datetime.now().date()
            
        sql = '''
            SELECT row_number() OVER () AS id, shipment_date,
                    si_name,
                    customer,
                    product_name,
                    description,
                    product_qty,
                    gdn_weighbridge_qty,
                    franchise,
                    franchise_out
            FROM v_fob_weight_franchise
            WHERE date(timezone('UTC',shipment_date::timestamp)) 
                between '%(from_date)s'  and '%(to_date)s'
            LIMIT %(limit_size)s OFFSET %(page_no)s 
              '''%({'page_no': page_no, 
                    'limit_size': limit_size,
                    'from_date': from_date,
                    'to_date': to_date}
                    )
        #print sql
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        return json.dumps(result)

    @http.route('/report/diviation', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_diviation_report(self, **post):
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        year = datetime.now().year
        month = datetime.now().strftime('%m')
        if from_date == 'None' or from_date == '':
            from_date = '01-%s-'%(month) + str(year)
        if to_date == 'None' or to_date == '':
            to_date = datetime.now().date()
            
        sql = '''
            SELECT row_number() OVER () AS id, do_no,
                    fob_date,
                    si_no,
                    con_name,
                    product,
                    total_qty,
                    trucking_no,
                    placename,
                    pickingname,
                    state,
                    transrate,
                    bagsfactory,
                    bagshcm,
                    weightfactory,
                    shipped_weight,
                    storing_loss,
                    transportation_loss
            FROM v_fob_deviation
            WHERE date(timezone('UTC',fob_date::timestamp)) 
                between '%(from_date)s'  and '%(to_date)s'
            LIMIT %(limit_size)s OFFSET %(page_no)s 
              '''%({'page_no': page_no, 
                    'limit_size': limit_size,
                    'from_date': from_date,
                    'to_date': to_date}
                    )
        #print sql
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        return json.dumps(result)

        
    @http.route('/stock/npe', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_npe_unfixed_detail(self, **post):
        npe = post.get('npe')
        limit_size = 10
        page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        sql = '''
            SELECT row_number() OVER () AS id, vnuq.npe npe,
                    vnuq.partner partner,
                    vnuq.date_order date,
                    vnuq.qty_contract qty_contract,
                    vnuq.qty_received qty_received,
                    vnuq.to_receive to_receive,
                    vnuq.qty_fixed qty_fixed,
                    vnuq.unfixed unfixed
            FROM v_npe_unfixed_quality vnuq
            WHERE vnuq.npe = '%s'
            GROUP BY vnuq.npe,
                    vnuq.partner,
                    vnuq.date_order,
                    vnuq.qty_contract,
                    vnuq.qty_received,
                    vnuq.to_receive,
                    vnuq.qty_fixed,
                    vnuq.unfixed
            LIMIT %s OFFSET %s
              '''%(npe, limit_size, page_no)
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)

    @http.route('/api/report/purquality', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_purchase_quality_report(self, **post):
        # limit_size = 20
        # page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        year = datetime.now().year
        month = datetime.now().strftime('%m')
        if from_date == 'None' or from_date == '':
            from_date = '01-%s-'%(month) + str(year)
        if to_date == 'None' or to_date == '':
            to_date = datetime.now().date()
        supplier_id = post.get('supplier_id')
        query =''
        if supplier_id == None or supplier_id == '' or supplier_id == 'null':
            query = 'sp.partner_id > 0'
        else:
            query = 'sp.partner_id = %s'%(supplier_id)
        product_id = post.get('product_id')
        query1 =''
        if product_id == None or product_id == '' or product_id == 'null':
            query1 = 'sm.product_id >= 0'
        else:
            query1 = 'sm.product_id = %s'%(product_id)
            
        sql = '''
            SELECT row_number() OVER () AS id,
                sp.partner_id as supplier_id,
                sm.product_id as product_id,
                rp.shortname AS supplier_name,
                pp.default_code AS product,
                rcs.id province_id, rcs.name as source_province,
                sum(rkl.product_qty) AS net_qty,
                sum(rkl.mc * rkl.product_qty)/sum(rkl.product_qty) mc,
                sum(rkl.fm * rkl.product_qty)/sum(rkl.product_qty) fm,
                sum(rkl.black * rkl.product_qty)/sum(rkl.product_qty) black,
                sum(rkl.broken * rkl.product_qty)/sum(rkl.product_qty) broken,
                sum(rkl.brown * rkl.product_qty)/sum(rkl.product_qty) brown,
                sum(rkl.mold * rkl.product_qty)/sum(rkl.product_qty) mold,
                sum(rkl.cherry * rkl.product_qty)/sum(rkl.product_qty) cherry,
                sum(rkl.excelsa * rkl.product_qty)/sum(rkl.product_qty) excelsa,
                sum(rkl.screen20 * rkl.product_qty)/sum(rkl.product_qty) screen20,
                sum(rkl.screen19 * rkl.product_qty)/sum(rkl.product_qty) screen19,
                sum(rkl.screen18 * rkl.product_qty)/sum(rkl.product_qty) screen18,
                sum(rkl.screen16 * rkl.product_qty)/sum(rkl.product_qty) screen16,
                sum(rkl.screen13 * rkl.product_qty)/sum(rkl.product_qty) screen13,
                sum(rkl.greatersc12 * rkl.product_qty)/sum(rkl.product_qty) screen12,
                sum(rkl.belowsc12 * rkl.product_qty)/sum(rkl.product_qty) belowsc12,
                sum(rkl.burned * rkl.product_qty)/sum(rkl.product_qty) burned,
                sum(rkl.eaten * rkl.product_qty)/sum(rkl.product_qty) eaten,
                sum(rkl.immature * rkl.product_qty)/sum(rkl.product_qty) immature
            FROM stock_stack sc
                JOIN stock_picking sp ON sc.id = sp.stack_id
                LEFT JOIN stock_move_line sm ON sp.id = sm.picking_id
                JOIN request_kcs_line rkl ON sp.id = rkl.picking_id
                JOIN product_product pp ON sm.product_id = pp.id
                LEFT  JOIN res_partner rp ON sp.partner_id = rp.id
                LEFT  JOIN res_district rd ON sc.districts_id=rd.id
                JOIN res_country_state rcs ON rd.state_id = rcs.id
            Where sp.picking_type_code in ('incoming','transfer_in') and rkl.product_qty != 0 
                AND %s AND %s
                AND date(timezone('UTC',sp.date_done::timestamp)) between '%s' and '%s'
            Group by sp.partner_id, rp.shortname, pp.default_code, rcs.name, rcs.id, sm.product_id
            Order by rcs.name, rp.shortname
              '''%(query, query1, from_date, to_date)
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

    @http.route('/api/report/purprovince', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_purchase_provice_report(self, **post):
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        year = datetime.now().year
        month = datetime.now().strftime('%m')
        if from_date == 'None' or from_date == '':
            from_date = '01-%s-'%(month) + str(year)
        if to_date == 'None' or to_date == '':
            to_date = datetime.now().date()
            
        sql = '''
            SELECT row_number() OVER () AS id,
                rcs.id province_id, rcs.name as source_province
            FROM stock_stack sc
                JOIN stock_picking sp ON sc.id = sp.stack_id
                LEFT JOIN stock_move_line sm ON sp.id = sm.picking_id
                JOIN request_kcs_line rkl ON sp.id = rkl.picking_id
                JOIN product_product pp ON sm.product_id = pp.id
                LEFT  JOIN res_partner rp ON sp.partner_id = rp.id
                LEFT  JOIN res_district rd ON sc.districts_id=rd.id
                JOIN res_country_state rcs ON rd.state_id = rcs.id
            Where sp.picking_type_code in ('incoming','transfer_in') and rkl.product_qty != 0 and date(timezone('UTC',sp.date_done::timestamp)) 
                between '%(from_date)s'  and '%(to_date)s'
            Group by rcs.name, rcs.id
            Order by rcs.name
              '''%({'from_date': from_date,
                    'to_date': to_date})
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
            
    @http.route('/api/report/salequality', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_sale_quality_report(self, **post):
        # limit_size = 20
        # page_no = (int(post.get('pageno')) - 1) * int(limit_size)
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        year = datetime.now().year
        month = datetime.now().strftime('%m')
        if from_date == 'None' or from_date == '':
            from_date = '01-%s-'%(month) + str(year)
        if to_date == 'None' or to_date == '':
            to_date = datetime.now().date()
        customer_id = post.get('customer_id')
        query =''
        if customer_id == None or customer_id == '' or customer_id == 'null':
            query = 'sp.partner_id > 0'
        else:
            query = 'sp.partner_id = %s'%(customer_id)
        product_id = post.get('product_id')
        query1 =''
        if product_id == None or product_id == '' or product_id == 'null':
            query1 = 'sm.product_id >= 0'
        else:
            query1 = 'sm.product_id = %s'%(product_id)
            
        sql = '''
            SELECT row_number() OVER () AS id,
                rp.name AS customer_name, sp.partner_id AS customer_id, pp.default_code AS product, sm.product_id as product_id,
                sum(sm.weighbridge) AS net_qty,
                sum(ss.mc * sm.weighbridge)/sum(sm.weighbridge) mc,
                sum(ss.fm * sm.weighbridge)/sum(sm.weighbridge) fm,
                sum(ss.black * sm.weighbridge)/sum(sm.weighbridge) black,
                sum(ss.broken * sm.weighbridge)/sum(sm.weighbridge) broken,
                sum(ss.brown * sm.weighbridge)/sum(sm.weighbridge) brown,
                sum(ss.mold * sm.weighbridge)/sum(sm.weighbridge) mold,
                sum(ss.cherry * sm.weighbridge)/sum(sm.weighbridge) cherry,
                sum(ss.excelsa * sm.weighbridge)/sum(sm.weighbridge) excelsa,
                sum(ss.screen20 * sm.weighbridge)/sum(sm.weighbridge) screen20,
                sum(ss.screen19 * sm.weighbridge)/sum(sm.weighbridge) screen19,
                sum(ss.screen18 * sm.weighbridge)/sum(sm.weighbridge) screen18,
                sum(ss.screen16 * sm.weighbridge)/sum(sm.weighbridge) screen16,
                sum(ss.screen13 * sm.weighbridge)/sum(sm.weighbridge) screen13,
                sum(ss.greatersc12 * sm.weighbridge)/sum(sm.weighbridge) screen12,
                sum(ss.screen12 * sm.weighbridge)/sum(sm.weighbridge) belowsc12,
                sum(ss.burn * sm.weighbridge)/sum(sm.weighbridge) burned,
                sum(ss.eaten * sm.weighbridge)/sum(sm.weighbridge) eaten,
                sum(ss.immature * sm.weighbridge)/sum(sm.weighbridge) immature
            From sale_contract sc
                Join delivery_order de ON de.contract_id=sc.id
                Join stock_picking sp ON sp.id=de.picking_id
                JOIN stock_move_line sm ON sm.picking_id=sp.id
                JOIN product_product pp ON pp.id=sm.product_id
                JOIN res_partner rp ON rp.id=de.partner_id
                JOIN stock_stack ss ON ss.id = sp.stack_id
            Where sp.picking_type_code in ('outgoing','transfer_out') and sm.weighbridge != 0
                AND %s AND %s
                AND date(timezone('UTC',sp.date_done::timestamp)) between '%s' and '%s'
            Group by rp.name, sp.partner_id, pp.default_code, sm.product_id
            Order by rp.name
              '''%(query, query1, from_date, to_date)
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

# class ReportAPI(http.Controller):   
#     @http.route('/report', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#     def get_row_report(self, **post):
#         limit_size = 10
#         page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#         from_date  = str(post.get('from_date'))
#         to_date = str(post.get('to_date'))
#         year = datetime.now().year
#         month = datetime.now().strftime('%m')
#         if from_date == 'None' or from_date == '':
#             from_date = '01-%s-'%(month) + str(year)
#         if to_date == 'None' or to_date == '':
#             to_date = datetime.now().date()
            
#         sql = '''
#             SELECT 'FAQ (FOT-Ned) deviation' as name_report,
#                 count(*) as item 
#             FROM v_grn_matching
#             WHERE date(timezone('UTC',factory_date_received::timestamp)) 
#                 between '%(from_date)s'  and '%(to_date)s'
                
#             UNION ALL
            
#             SELECT 'FOB Weight Franchise' as name_report,
#                 count(*) as item 
#             FROM v_fob_weight_franchise
#             WHERE date(timezone('UTC',shipment_date::timestamp)) 
#                 between '%(from_date)s'  and '%(to_date)s'
                
#             UNION ALL
            
#             SELECT 'FOB Diviation' as name_report,
#                 count(*) as item 
#             FROM v_fob_deviation
#             WHERE date(timezone('UTC',fob_date::timestamp)) 
#                 between '%(from_date)s'  and '%(to_date)s'
#             LIMIT %(limit_size)s OFFSET %(page_no)s 
#               '''%({'page_no': page_no, 
#                     'limit_size': limit_size,
#                     'from_date': from_date,
#                     'to_date': to_date}
#                     )
#         #print sql
#         records = request.cr.execute(sql)
#         result = request.env.cr.dictfetchall()
#         return json.dumps(result)
    
#     @http.route('/report/fot', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#     def get_fot_report(self, **post):
#         limit_size = 10
#         page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#         from_date  = str(post.get('from_date'))
#         to_date = str(post.get('to_date'))
#         year = datetime.now().year
#         month = datetime.now().strftime('%m')
#         if from_date == 'None' or from_date == '':
#             from_date = '01-%s-'%(month) + str(year)
#         if to_date == 'None' or to_date == '':
#             to_date = datetime.now().date()
            
#         sql = '''
#             SELECT row_number() OVER () AS id, grn_branch,
#                 branch_id,
#                 shortname,
#                 branch_date_received,
#                 grn_factory,
#                 factory_date_received,
#                 deduction_branch,
#                 deduction_factory,
#                 brn_fac,
#                 deficit,
#                 net_weight_branch,
#                 net_weight_factory,
#                 net_weight_deficit,
#                 net_var,
#                 basis_weight_branch,
#                 basis_weight_factory,
#                 basis_weight_deficit,
#                 basis_var,
#                 mc_branch,
#                 mc_factory,
#                 fm_branch,
#                 fm_factory,
#                 black_branch,
#                 black_factory,
#                 broken_branch,
#                 broken_factory,
#                 brown_branch,
#                 brown_factory,
#                 cherry_branch,
#                 cherry_factory,
#                 screen18_branch,
#                 screen18_factory,
#                 screen16_branch,
#                 screen16_factory,
#                 screen13_branch,
#                 screen13_factory,
#                 belowsc12_branch,
#                 belowsc12_factory,
#                 vehicle_no
#             FROM v_grn_matching
#             WHERE date(timezone('UTC',factory_date_received::timestamp)) 
#                 between '%(from_date)s'  and '%(to_date)s'
#             LIMIT %(limit_size)s OFFSET %(page_no)s 
#               '''%({'page_no': page_no, 
#                     'limit_size': limit_size,
#                     'from_date': from_date,
#                     'to_date': to_date}
#                     )
#         #print sql
#         records = request.cr.execute(sql)
#         result = request.env.cr.dictfetchall()
#         return json.dumps(result)


#     @http.route('/report/franchise', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#     def get_franchise_report(self, **post):
#         limit_size = 10
#         page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#         from_date  = str(post.get('from_date'))
#         to_date = str(post.get('to_date'))
#         year = datetime.now().year
#         month = datetime.now().strftime('%m')
#         if from_date == 'None' or from_date == '':
#             from_date = '01-%s-'%(month) + str(year)
#         if to_date == 'None' or to_date == '':
#             to_date = datetime.now().date()
            
#         sql = '''
#             SELECT row_number() OVER () AS id, shipment_date,
#                     si_name,
#                     customer,
#                     product_name,
#                     description,
#                     product_qty,
#                     gdn_weighbridge_qty,
#                     franchise,
#                     franchise_out
#             FROM v_fob_weight_franchise
#             WHERE date(timezone('UTC',shipment_date::timestamp)) 
#                 between '%(from_date)s'  and '%(to_date)s'
#             LIMIT %(limit_size)s OFFSET %(page_no)s 
#               '''%({'page_no': page_no, 
#                     'limit_size': limit_size,
#                     'from_date': from_date,
#                     'to_date': to_date}
#                     )
#         #print sql
#         records = request.cr.execute(sql)
#         result = request.env.cr.dictfetchall()
#         return json.dumps(result)

#     @http.route('/report/diviation', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#     def get_diviation_report(self, **post):
#         limit_size = 10
#         page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#         from_date  = str(post.get('from_date'))
#         to_date = str(post.get('to_date'))
#         year = datetime.now().year
#         month = datetime.now().strftime('%m')
#         if from_date == 'None' or from_date == '':
#             from_date = '01-%s-'%(month) + str(year)
#         if to_date == 'None' or to_date == '':
#             to_date = datetime.now().date()
            
#         sql = '''
#             SELECT row_number() OVER () AS id, do_no,
#                     fob_date,
#                     si_no,
#                     con_name,
#                     product,
#                     total_qty,
#                     trucking_no,
#                     placename,
#                     pickingname,
#                     state,
#                     transrate,
#                     bagsfactory,
#                     bagshcm,
#                     weightfactory,
#                     shipped_weight,
#                     storing_loss,
#                     transportation_loss
#             FROM v_fob_deviation
#             WHERE date(timezone('UTC',fob_date::timestamp)) 
#                 between '%(from_date)s'  and '%(to_date)s'
#             LIMIT %(limit_size)s OFFSET %(page_no)s 
#               '''%({'page_no': page_no, 
#                     'limit_size': limit_size,
#                     'from_date': from_date,
#                     'to_date': to_date}
#                     )
#         #print sql
#         records = request.cr.execute(sql)
#         result = request.env.cr.dictfetchall()
#         return json.dumps(result)
