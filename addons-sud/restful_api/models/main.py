# -*- coding: utf-8 -*-

# from odoo.http import http
from odoo import SUPERUSER_ID
from odoo import http
# from odoo.addons.website import slug, unslug
from odoo.http import route, request, json
from odoo.exceptions import AccessError, UserError
import jwt

# class MainJson(http.Controller):

# # Create route web/sesssion/authenticate method to authenticate user and generate access token

# 	# @http.route('/web/session/authenticate', type='json', auth='none', methods=['POST'], csrf=False)
# 	# def authenticate(self, db, login, password, base_location=None):
# 	# 	request.session.authenticate(db, login, password)
# 	# 	return request.env['ir.http'].session_info()
 
#     @http.route('/web/session/authenticate', type='json', auth='none', methods=['POST'], csrf=False)
#     def authenticate(self, login, password, db=None):
#         request.session.authenticate(db, login, password)
#         access_token = jwt.encode({'session_id': request.session.sid}, 'secret', algorithm='HS256')
#         return {
#             'access_token': access_token
#         }
      
#   @http.route('/auth/signin', type='http', methods=['POST'], auth='none', website = True, csrf=False)
#   def sign_in(self, **post):

#     login = post.get('login')
#     password = post.get('password')
#     uid = request.session.authenticate(request.session.db, login, password)
#     if uid:
#       user = request.env['res.users'].sudo().search([('id', '=', uid)])
#       if user:

#         sql = '''
#             SELECT rp.name, rp.email, ru.mobi_app_level
#             From res_users ru Join res_partner rp On ru.partner_id=rp.id
#             Where ru.id = %s
#             '''%(uid)
#         records = request.cr.execute(sql)
#         result = request.env.cr.dictfetchall()

#         access_token = jwt().generate_token(uid)
#         response = {
#           'message': 'You logged in successfully.',
#           'errors': '',
#           'access_token': access_token.decode(),
#           'user_info': result
#         }

#       else:
#         response = {
#           'message': 'Can not find user',
#           'errors': 'Login Fails',
#           'access_token': ''
#         }
#     else:
#       response = {
#         'message': 'Can not find user',
#         'errors': 'Login Fails',
#         'access_token': ''
#       }
#     return json.dumps(response)

#   @http.route('/myprofile', type='http', auth='none', website=True, csrf=False)
#   def my_profile(self):
#     # auth_header = request.httprequest.headers.get('Authenticate')
#     auth_header = request.httprequest.headers.get('Authenticate')
#     access_token = auth_header.split(' ')[1]
#     access_token = access_token.split('"')[1]
#     # print auth_header
#     # print access_token
#     if jwt().decode_token(auth_header) in ('Expired token. Please login to get a new token', 'Invalid token. Please register or login'):
#         return json.dumps({'message':jwt().decode_token(auth_header)})
#     else:
#       # user = request.env['res.users'].sudo().search([('id', '=', uid)])
#       # # partner_id = int(user.partner_id)
#       # # partner = request.env['res.partner'].sudo().search([('id','=', partner_id)])
#       # # result = partner.read(['id', 'name', 'display_name', 'company_type', 'street', 'city'])
#       # result = user.read(['login', 'partner_id'])
#       # return json.dumps(result)
#       uid = jwt().decode_token(access_token)['sub']
#       sql = '''
#           SELECT rp.name, rp.email, ru.mobi_app_level
#           From res_users ru Join res_partner rp On ru.partner_id=rp.id
#           Where ru.id = %s
#           '''%(uid)
#       records = request.cr.execute(sql)
#       result = request.env.cr.dictfetchall()
#       return json.dumps(result)


#   @http.route('/auth/signout', type='json', auth='user', methods=['DELETE'], website = True)
#   def sign_out(self):
#     ###LOGIC CODE###
#     return 1

#   # @http.route('/respartner/json', type='http', auth='public')
#   # def books_json(self):
#   #   records = request.env['res.partner'].sudo().search([])
#   #   result = records.read(['name'])
#   #   return json.dumps(result)

#   @http.route('/api/inventory/views', type='http', auth='none', methods=['GET'], website = True, csrf=False)
#   def get_stock_invent_view(self):
#     sql = '''
#           SELECT * from api_invent_view
#         '''
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

#   @http.route('/api/inventory/get_fot_pending_list', type='http', auth='none', methods=['GET'], website = True, csrf=False)
#   def get_fot_pending_list(self):
#     sql = '''
#          SELECT row_number() OVER () AS id, sm.init_qty stock_weight, grn_br.name grn_br_name, grn_fac.name grn_fac_name
#            FROM stock_picking grn_br
#              LEFT JOIN stock_picking grn_fac ON grn_br.id = grn_fac.backorder_id
#              JOIN stock_move_line sm ON grn_br.id = sm.picking_id
#           WHERE grn_br.transfer_picking_type = true AND grn_fac.name IS NULL AND grn_br.state::text <> 'cancel'::text
#         '''
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

#   @http.route('/api/inventory/intransit', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_invent_transit(self, **post):
#     stock_id = int(post.get('stock_id'))
#     sql = ''
#     if stock_id == 2:
#       sql = '''
#             SELECT row_number() OVER () AS id, 2 AS stock_id, grn_br.name, sm.init_qty qty from stock_picking grn_br
#               LEFT JOIN (select * from stock_picking where to_picking_type_id is null) grn_fa ON grn_br.id=grn_fa.backorder_id
#               JOIN stock_move_line sm ON grn_br.id=sm.picking_id
#               where grn_br.to_picking_type_id is not null and grn_fa.state not in ('done','cancel') and grn_br.picking_type_code='incoming'
#               and grn_br.state='done' and DATE(timezone('UTC',date_tz::timestamp)) >= date(TIMESTAMP '10/01/2017')
#           '''
#     elif stock_id == 3:
#       sql = '''
#             SELECT row_number() OVER () AS id, 3 AS stock_id, name, do_qty qty from sale_contract where invoiced_qty=0 and do_qty >0 and DATE(timezone('UTC',date::timestamp)) >= date(TIMESTAMP '10/01/2017')
#           '''
#     else:
#       sql = '''
#             SELECT row_number() OVER () AS id, 4 AS stock_id, grn_br.name, sm.init_qty qty from stock_picking grn_br
#             LEFT JOIN (select * from stock_picking) grn_fa ON grn_br.id=grn_fa.backorder_id
#             JOIN stock_move_line sm ON grn_br.id=sm.picking_id
#             where grn_br.picking_type_code='transfer_out' and grn_br.state='done' and grn_fa.name is null
#             and DATE(timezone('UTC',date_tz::timestamp)) >= date(TIMESTAMP '10/01/2017')
#           '''
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

#   @http.route('/api/inventory', type='http', auth='none', methods=['GET'], website = True, csrf=False)
#   def get_stock_invent(self):
#     sql = '''
#           SELECT row_number() OVER () AS id, case When ss.warehouse_id =-1 then 'In Production' 
#             When ss.warehouse_id =-2 then 'WIP (Pending Approval)'
#             When ss.warehouse_id =-3 then 'WIP (Approved)'
#             Else swh.name End AS stockname, 
#             ss.warehouse_id AS stock_id, init_qty, bag_qty
#           FROM (Select ss.warehouse_id, sum(ss.init_qty) AS init_qty, sum(ss.bag_qty) bag_qty
#             FROM stock_stack ss JOIN product_category pc ON ss.categ_id=pc.id
#             where ss.init_qty != 0 And pc.name != 'Loss' AND ss.name not like '%WIP%' Group by ss.warehouse_id Union
#           Select -1 AS warehouse_id, case when sum(product_balance) is null then 0 else sum(product_balance) END AS init_qty, 0 bag_qty
#             FROM mrp_production Where state = 'in_production' Union
#           Select -2 AS warehouse_id, case when sum(total_init_qty) is null then 0 else sum(total_init_qty) END AS init_qty, sum(total_bag) bag_qty
#             FROM stock_picking Where state = 'assigned' AND state_kcs = 'draft' AND picking_type_code = 'production_in' Union
#           Select -3 AS warehouse_id, case when sum(ss.init_qty) is null then 0 else sum(ss.init_qty) END AS init_qty, sum(ss.bag_qty) bag_qty
#             FROM stock_stack ss JOIN product_category pc ON ss.categ_id=pc.id
#             where ss.remaining_qty != 0 And pc.name != 'Loss' AND ss.name like '%WIP%' Group by ss.warehouse_id) ss
#           LEFT Join stock_warehouse swh On ss.warehouse_id=swh.id
#           Where init_qty > 0 OR ss.warehouse_id < 0 Order By ss.warehouse_id DESC
#         '''
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

#   @http.route('/stock/product', type='http', methods=['POST'], auth='none', website = True, csrf=False)
#   def get_stock_product(self, **post):
#     limit_size = 10
#     page_no = (int(post.get('pageno')) - 1) * int(limit_size)

#     warehouse_id = post.get('warehouse_id') 
#     sql = '''
#         SELECT case when ss.warehouse_id is null then 'Unknow Stock' else swh.name End as stockname, 
#           case when ss.warehouse_id is null then -1 else ss.warehouse_id End as stock_id, pp.default_code AS product_name, ss.product_id, 
#           ctg.name AS prod_group, ss.init_qty, ss.bag_qty, ss.MC, ss.FM, ss.BB
#               FROM (Select warehouse_id, product_id, sum(init_qty) AS init_qty, sum(bag_qty) As bag_qty,
#                     sum(mc)/count(*) MC, sum(fm)/count(*) FM,
#                     sum((black + broken))/count(*) BB
#                 FROM public.stock_stack where remaining_qty <> 0 and bag_qty <> 0 Group by warehouse_id, product_id
#                 order by warehouse_id, product_id) ss
#               left join stock_warehouse swh On ss.warehouse_id=swh.id
#               left join product_product pp On ss.product_id=pp.id
#               join product_template pt ON pp.product_tmpl_id=pt.id
#               Join product_category ctg ON pt.categ_id=ctg.id
#             WHERE (case when ss.warehouse_id is null then -1 else ss.warehouse_id End) = %s 
#             ORDER BY ctg.name LIMIT %s OFFSET %s 
#             '''%(warehouse_id, limit_size, page_no)
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

#   @http.route('/stock/zone', type='http', methods=['POST'], auth='none', website = True, csrf=False)
#   def get_stock_zone(self, **post):
#     limit_size = 10
#     page_no = (int(post.get('pageno')) - 1) * int(limit_size)

#     warehouse_id = post.get('warehouse_id') 
#     sql = '''
#             SELECT case when ss.warehouse_id is null then 'Unknow Stock' else swh.name End as stockname, 
#             case when ss.warehouse_id is null then -1 else ss.warehouse_id End as stock_id, sz.name AS zone_name, 
#                   ss.MC, ss.FM, ss.BB, ss.zone_id, ss.init_qty, ss.bag_qty
#             FROM (Select warehouse_id, zone_id, sum(init_qty) AS init_qty, sum(bag_qty) As bag_qty,
#                     sum(mc)/count(*) MC, sum(fm)/count(*) FM,
#                     sum((black + broken))/count(*) BB
#               FROM public.stock_stack where remaining_qty <> 0 and bag_qty <> 0 Group by warehouse_id, zone_id
#               order by warehouse_id, zone_id) ss
#             left join stock_warehouse swh On ss.warehouse_id=swh.id
#             Join stock_zone sz On ss.zone_id=sz.id
#             WHERE (case when ss.warehouse_id is null then -1 else ss.warehouse_id End) = %s 
#             ORDER BY sz.name LIMIT %s OFFSET %s
#             '''%(warehouse_id, limit_size, page_no)
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

#   @http.route('/stock/product/stack', type='http', methods=['POST'], auth='none', website = True, csrf=False)
#   def get_product_stack(self, **post):
#     limit_size = 10
#     page_no = (int(post.get('pageno')) - 1) * int(limit_size)

#     warehouse_id = post.get('warehouse_id') 
#     product_id = post.get('product_id') 
#     sql = '''
#             SELECT case when ss.warehouse_id is null then 'Unknow Stock' else swh.name End as stockname, 
#               case when ss.warehouse_id is null then -1 else ss.warehouse_id End as stock_id, pp.default_code AS product_name, 
#               ss.product_id, sz.name AS zone_name, ss.name stack, np.name AS packing_type, date, ss.init_qty, ss.bag_qty, ss.mc, ss.fm, ss.BB
#               FROM (Select warehouse_id, product_id, production_id, zone_id, name, packing_id, date, init_qty, bag_qty,
#                   mc, fm, (black + broken) as BB
#                 FROM public.stock_stack where remaining_qty <> 0 and bag_qty <> 0
#                 order by warehouse_id, product_id, zone_id) ss
#               left join stock_warehouse swh On ss.warehouse_id=swh.id
#               left join product_product pp On ss.product_id=pp.id
#               Join stock_zone sz On ss.zone_id=sz.id
#               Join ned_packing np On ss.packing_id=np.id
#               WHERE (case when ss.warehouse_id is null then -1 else ss.warehouse_id End) = %s and ss.product_id = %s LIMIT %s OFFSET %s
#             '''%(warehouse_id, product_id, limit_size, page_no)
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

#   @http.route('/stock/zone/stack', type='http', methods=['POST'], auth='none', website = True, csrf=False)
#   def get_zone_stack(self, **post):
#     limit_size = 10
#     page_no = (int(post.get('pageno')) - 1) * int(limit_size)

#     warehouse_id = post.get('warehouse_id') 
#     zone_id = post.get('zone_id') 
#     sql = '''
#             SELECT case when ss.warehouse_id is null then 'Unknow Stock' else swh.name End as stockname, 
#               case when ss.warehouse_id is null then -1 else ss.warehouse_id End as stock_id, pp.default_code AS product_name, 
#               ss.product_id, sz.name AS zone_name, ss.zone_id, ss.name stack, np.name AS packing_type, date, ss.init_qty, ss.bag_qty, ss.mc, ss.fm, ss.BB
#               FROM (Select warehouse_id, product_id, production_id, zone_id, name, packing_id, date, init_qty, bag_qty,
#                     mc, fm, (black + broken) as BB
#                 FROM public.stock_stack where remaining_qty <> 0 and bag_qty <> 0
#                 order by warehouse_id, product_id, zone_id) ss
#               left join stock_warehouse swh On ss.warehouse_id=swh.id
#               left join product_product pp On ss.product_id=pp.id
#               Join stock_zone sz On ss.zone_id=sz.id
#               Join ned_packing np On ss.packing_id=np.id
#               WHERE (case when ss.warehouse_id is null then -1 else ss.warehouse_id End) = %s and ss.zone_id = %s LIMIT %s OFFSET %s
#             '''%(warehouse_id, zone_id, limit_size, page_no)
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     return json.dumps(result)

# class ReportAPI(http.Controller):

#   @http.route('/inbound/faqdeviation', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_faqdeviation(self, **post):
#       limit_size = 10
#       page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#       from_date  = str(post.get('from_date'))
#       to_date = str(post.get('to_date'))
#       sql = '''
#           SELECT row_number() OVER () AS newid, * FROM v_grn_matching WHERE brn_fac > 0.2
#               AND DATE(timezone('UTC',branch_date_received::timestamp)) between '%s' and '%s'
#           LIMIT %s OFFSET %s 
#             '''%(from_date, to_date, limit_size, page_no)
#       records = request.cr.execute(sql)
#       result = request.env.cr.dictfetchall()
#       if result == []:
#           mess = {
#               'message': 'Record does not exist.',
#               }
#           return json.dumps(mess)
#       else:
#           return json.dumps(result)

#   @http.route('/outbound/fobdeviation', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_fobdeviation(self, **post):
#       limit_size = 10
#       page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#       from_date  = str(post.get('from_date'))
#       to_date = str(post.get('to_date'))
#       sql = '''
#           SELECT row_number() OVER () AS newid, *, 
#             CASE WHEN transportation_loss > 0 AND weightfactory > 0 AND shipped_weight > 0
#               AND (transportation_loss / weightfactory * 100 > 0.1) 
#               THEN transportation_loss - (weightfactory * 0.1 / 100)
#               ELSE 0 END AS claim_percent
#             FROM v_fob_deviation WHERE 
#               (CASE WHEN transportation_loss > 0 AND weightfactory > 0 AND shipped_weight > 0
#               AND (transportation_loss / weightfactory * 100 > 0.1) 
#               THEN transportation_loss - (weightfactory * 0.1 / 100)
#               ELSE 0 END) > 0 AND DATE(timezone('UTC',fob_date::timestamp)) between '%s' and '%s'
#           LIMIT %s OFFSET %s 
#             '''%(from_date, to_date, limit_size, page_no)
#       records = request.cr.execute(sql)
#       result = request.env.cr.dictfetchall()
#       if result == []:
#           mess = {
#               'message': 'Record does not exist.',
#               }
#           return json.dumps(mess)
#       else:
#           return json.dumps(result)

#   @http.route('/outbound/fobfranchise', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_fobfranchise(self, **post):
#       limit_size = 10
#       page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#       from_date  = str(post.get('from_date'))
#       to_date = str(post.get('to_date'))
#       sql = '''
#           SELECT row_number() OVER () AS newid, *
#             FROM v_fob_weight_franchise 
#           WHERE franchise_out != '' AND
#               DATE(timezone('UTC',factory_etd::timestamp)) between '%s' and '%s'
#           LIMIT %s OFFSET %s 
#             '''%(from_date, to_date, limit_size, page_no)
#       records = request.cr.execute(sql)
#       result = request.env.cr.dictfetchall()
#       if result == []:
#           mess = {
#               'message': 'Record does not exist.',
#               }
#           return json.dumps(mess)
#       else:
#           return json.dumps(result)

#   @http.route('/api/reports/longshort', type='http', auth='none', methods=['GET'], website = True, csrf=False)
#   def get_longshort(self):
#     sql = '''
#           SELECT row_number() OVER () AS id, prod_group as code_param, concat(prod_group,' (',count(*),')') product_group, 
#             sum(sitting_stock) sitting_stock, CASE WHEN sum(faq_derivable) IS NULL THEN 0 ELSE sum(faq_derivable) END AS faq_derivable, 
#             sum(npe_received_unfixed) npe_received_unfixed, 
#             sum(gross_ls) gross_ls, sum(nvp_receivable) nvp_receivable, sum(unshipped_qty) unshipped_qty, sum(net_ls) net_ls, 
#             sum(sale_next1_unshipped) sale_next1_unshipped, sum(next1_net_ls) next1_net_ls,
#             sum(sale_next2_unshipped) sale_next2_unshipped, sum(next2_net_ls) next2_net_ls,
#             sum(sale_next3_unshipped) sale_next3_unshipped, sum(next3_net_ls) next3_net_ls,
#             sum(sale_next4_unshipped) sale_next4_unshipped, sum(next4_net_ls) next4_net_ls,
#             sum(sale_next5_unshipped) sale_next5_unshipped, sum(next5_net_ls) next5_net_ls,
#             sum(sale_next6_unshipped) sale_next6_unshipped, sum(next6_net_ls) next6_net_ls
#             from v_long_short_v2 Group by prod_group Order by prod_group
#           '''
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     if result == []:
#         mess = {
#             'message': 'Record does not exist.',
#             }
#         return json.dumps(mess)
#     else:
#         return json.dumps(result)

#   @http.route('/api/reports/longshort/detail', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_longshort_detail(self, **post):
#     prod_group = post.get('prod_group') 
#     sql = '''
#           SELECT row_number() OVER () AS id, prod_group, product, sitting_stock, faq_derivable, 
#             npe_received_unfixed, gross_ls, nvp_receivable, unshipped_qty, net_ls, 
#             sale_next1_unshipped, next1_net_ls,
#             sale_next2_unshipped, next2_net_ls,
#             sale_next3_unshipped, next3_net_ls,
#             sale_next4_unshipped, next4_net_ls,
#             sale_next5_unshipped, next5_net_ls,
#             sale_next6_unshipped, next6_net_ls
#             from v_long_short_v2 Where prod_group = '%s'
#           '''%(prod_group)
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     if result == []:
#         mess = {
#             'message': 'Record does not exist.',
#             }
#         return json.dumps(mess)
#     else:
#         return json.dumps(result)

#   @http.route('/api/reports/operation', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_operation(self, **post):
#       # limit_size = 10
#       # page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#       from_date  = str(post.get('from_date'))
#       to_date = str(post.get('to_date'))
#       status = post.get('status')
#       if post.get('status') == 'Shipped':
#         status = '''AND status = 'Done' '''
#       else:
#         status = '''AND status != 'Done' '''
        
#       sql = '''
#           SELECT row_number() OVER () AS id, customer code_param, concat(Customer,' (',count(*),')') customer, 
#             sum(si_quantity) si_quantity, 
#             Case When sum(production_progress) Is null then 0 else sum(production_progress) End as production_progress,
#             sum(do_quantity) do_quantity, 
#             sum(gdn_quantity) shipped from v_shipment
#           WHERE (DATE(timezone('UTC',closing_time::timestamp)) between '%s' and '%s') %s
#           Group by Customer
#           '''%(from_date, to_date, status)
#       records = request.cr.execute(sql)
#       result = request.env.cr.dictfetchall()
#       if result == []:
#           mess = {
#               'message': 'Record does not exist.',
#               }
#           return json.dumps(mess)
#       else:
#           return json.dumps(result)

#   @http.route('/api/reports/operation/detail', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_operation_detail(self, **post):
#       limit_size = 10
#       page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#       from_date  = str(post.get('from_date'))
#       to_date = str(post.get('to_date'))
#       code_param = post.get('code_param')
#       status = post.get('status')
#       if post.get('status') == 'Executed':
#         status = '''AND status = 'Done' '''
#       else:
#         status = '''AND status != 'Done' '''

#       sql = '''
#           SELECT row_number() OVER () AS id, s_contract, customer, product, specification, si_quantity,
#             closing_time, factory_etd, production_progress, do_quantity, gdn_quantity AS shipped 
#           FROM v_shipment WHERE customer::text = '%s'::text AND (DATE(timezone('UTC',closing_time::timestamp)) between '%s' and '%s') %s
#           LIMIT %s OFFSET %s
#             '''%(code_param, from_date, to_date, status, limit_size, page_no)
#       # print sql
#       records = request.cr.execute(sql)
#       result = request.env.cr.dictfetchall()
#       if result == []:
#           mess = {
#               'message': 'Record does not exist.',
#               }
#           return json.dumps(mess)
#       else:
#           return json.dumps(result)

#   @http.route('/api/reports/production/batchmrp', type='http', methods=['GET'], auth='none', website = True, csrf=False)
#   def get_mrp_batchno(self):
#     sql = '''
#           SELECT name, notes FROM mrp_production Where state = 'done' Order by date_planned desc
#           '''
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     if result == []:
#         mess = {
#             'message': 'Record does not exist.',
#             }
#         return json.dumps(mess)
#     else:
#         return json.dumps(result)

#     # records = request.env['mrp.production'].sudo().search([('state','=','done')])
#     # result = records.read(['name', u'notes'])
#     # return json.dumps(result)

#   @http.route('/api/reports/production/piechart', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def get_production_pie(self, **post):
#     code_param = str(post.get('code_param'))
#     sql = '''
#           SELECT qty.prod_group, qty.net_quantity, round(qty.net_quantity/(Select sum(net_quantity) From v_production_report 
#                                                                             Where operation_type = 'IN' AND batch_no = '%s' AND state = 'done') * 100, 2) grade_percent 
#           From (SELECT prod_group, sum(net_quantity) net_quantity
#                   from v_production_report Where operation_type = 'OUT' AND batch_no = '%s' AND prod_group != 'Loss' AND state = 'done'
#                   Group by prod_group
#                 Union All
#                 Select 'LOSS' As prod_group, qty_in.quantity_In - qty_out.quantity_Out net_quantity
#                 From ((Select batch_no, sum(net_quantity) quantity_Out From v_production_report
#                     Where operation_type = 'OUT' AND prod_group != 'Loss' AND state = 'done' Group By batch_no) qty_out
#                   JOIN (Select batch_no, sum(net_quantity) quantity_In From v_production_report 
#                     Where operation_type = 'IN' AND state = 'done' Group By batch_no) qty_in
#                   ON qty_out.batch_no = qty_in.batch_no)
#                 Where qty_out.batch_no = '%s') qty
#           '''%(code_param, code_param, code_param)
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     if result == []:
#         mess = {
#             'message': 'Record does not exist.',
#             }
#         return json.dumps(mess)
#     else:
#         return json.dumps(result)


#   @http.route('/stock/stack', type='http', methods=['POST'], auth='none', website = True, csrf=False)
#   def stock_stack_json(self, **post):
#     limit_size = 10
#     page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#     records = request.env['npe.unfixed.master'].sudo().search([], limit=limit_size, offset=page_no)
#     result = records.read(['partner_ids', 'name', 'unfixed', 'qty_received', 'link_to_detail'])
#     return json.dumps(result)

#   @http.route('/api/reports/delivery-registration', type='http', auth='none', methods=['POST'], website = True, csrf=False)
#   def api_delivery_registration(self, **post):
#     # limit_size = 10
#     # page_no = (int(post.get('pageno')) - 1) * int(limit_size)
#     from_date  = str(post.get('from_date'))
#     to_date = str(post.get('to_date'))
#     sql = '''
#       SELECT row_number() OVER (ORDER BY sw.name) AS id, sw.name, 
#       case when rp.shortname is not null then rp.shortname else rp.name end as supplier, 
#       count(se.supplier_id) dr_num, sum(se.approx_quantity) approx_quantity,
#           case when sum(sp.received_qty) is not null then sum(sp.received_qty) else 0 end as received_qty, 
#           sum(Case When sp.first_weight > 0 AND sp.second_weight = 0 Then 1 ELSE 0 END) AS offloading
#           FROM ned_security_gate_queue se
#           JOIN res_partner rp ON se.supplier_id=rp.id
#           JOIN stock_warehouse sw ON se.warehouse_id=sw.id
#           LEFT JOIN (SELECT sp.security_gate_id, sum(sm.init_qty) received_qty, 
#                  sum(first_weight) first_weight, sum(second_weight) second_weight,
#                  date(timezone('UTC',sp.date_done::timestamp)) date_done
#                  FROM stock_picking sp
#                  LEFT JOIN stock_move_line sm ON sm.picking_id=sp.id
#                  GROUP BY sp.security_gate_id, date(timezone('UTC',sp.date_done::timestamp))) sp ON sp.security_gate_id=se.id
#           WHERE ((DATE(timezone('UTC',se.arrivial_time::timestamp)) between (DATE(timezone('UTC','%s'::timestamp)) - integer '3') and '%s') AND
#             --(sp.first_weight is not null OR sp.first_weight > 0)
#             (DATE(timezone('UTC',sp.date_done::timestamp)) between '%s' AND '%s'))
#             OR ((DATE(timezone('UTC',se.arrivial_time::timestamp)) between (DATE(timezone('UTC','%s'::timestamp)) - integer '3') and '%s') AND
#             se.state not in ('cancel', 'reject','approved','closed'))
#             and se.state not in ('cancel', 'reject')
#           Group By case when rp.shortname is not null then rp.shortname else rp.name end, sw.name
#           '''%(from_date, to_date,from_date, to_date,from_date, to_date)
#     records = request.cr.execute(sql)
#     result = request.env.cr.dictfetchall()
#     if result == []:
#         mess = {
#             'message': 'Record does not exist.',
#             }
#         return json.dumps(mess)
#     else:
#         return json.dumps(result)