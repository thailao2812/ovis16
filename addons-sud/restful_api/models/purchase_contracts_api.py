# -*- coding: utf-8 -*-

# from odoo.http import http
from odoo import SUPERUSER_ID
# from odoo.addons.website import slug, unslug
from odoo.http import route, request, json
from odoo import http
from odoo.exceptions import AccessError, UserError
# from models import JWTAuth
from datetime import datetime, date as date_object



class API_Purchase_Contracts(http.Controller):

    @http.route('/api/purcontracts/overview', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_purcontracts_overview(self, **post):
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        sql = '''
	            SELECT row_number() OVER () AS id, sum(contract_qty) contract_qty, sum(received) received_qty, sum(receivable_qty) receivable_qty, 
					sum(fixed_qty) fixed_qty, sum(received_unfixed) unfixed_qty, order_id, sum(faq_qty) faq_qty, sum(grade_qty) grade_qty,
					Case When contract_type = 'purchase' Then 'NVP' When contract_type = 'consign' Then 'NPE' Else 'PTBF' End As contract_type
				from api_purchase_contracts
				WHERE (DATE(timezone('UTC',date::timestamp)) between '%s' and '%s')
				Group By contract_type, order_id
              '''%(from_date, to_date)
        # print sql    
        records = request.cr.execute(sql)
        result = request.env.cr.dictfetchall()
        # result_detail = []
        # sql2 = '''
        #         SELECT row_number() OVER () AS id, sum(contract_qty) contract_qty, sum(received) received_qty, sum(receivable_qty) receivable_qty, 
        #             sum(fixed_qty) fixed_qty, sum(received_unfixed) unfixed_qty, order_id,
        #             Case When contract_type = 'purchase' Then 'NVP' When contract_type = 'consign' Then 'NPE' Else 'PTBF' End As contract_type,
        #             Case When product = 'FAQ' Then 'FAQ' Else 'Grade' End As product_type
        #         from api_purchase_contracts
        #         WHERE (DATE(timezone('UTC',date::timestamp)) between '%s' and '%s')
        #         Group By contract_type, order_id, Case When product = 'FAQ' Then 'FAQ' Else 'Grade' End
        #       '''%(from_date, to_date)
        # records2 = request.cr.execute(sql2)
        # result_detail = request.env.cr.dictfetchall()

        if result == []:
            mess = {
                'message': 'Record does not exist.',
                }
            return json.dumps(mess)
        else:
            return json.dumps(result)
            # return json.dumps({"master": result, "detail": result_detail})

    @http.route('/api/purcontracts/nvp_npe_detail', type='http', auth='none', methods=['POST'], website = True, csrf=False)
    def get_purcontracts_nvp_npe_detail(self, **post):
        from_date  = str(post.get('from_date'))
        to_date = str(post.get('to_date'))
        contract_type = str(post.get('contract_type'))
        sql = '''
                SELECT sum(contract_qty) AS contract_qty, sum(received) AS received, sum(receivable_qty) AS receivable_qty, 
                    sum(fixed_qty) AS fixed_qty, sum(received_unfixed) AS received_unfixed, partner_name, sum(diff_price)/count(*) AS diff_price
                FROM api_purchase_contracts
                WHERE (DATE(timezone('UTC',date::timestamp)) between '%s' and '%s') and contract_type = '%s' Group By partner_name
              '''%(from_date, to_date, contract_type)
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