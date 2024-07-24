import datetime
import json
from odoo import http
from odoo.http import request
from json import JSONEncoder

# subclass JSONEncoder
class DateTimeEncoder(JSONEncoder):

    #Override the default method
    def default(self, obj):
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        
class RestAPI(http.Controller):
        
    @http.route('/api/products', type='http', method=['GET'], auth='custom_auth', sitemap=False)
    def api_get_products(self, **kwargs):
        query_result = request.env['product.product'].search_read([('default_code','!=','')], fields=['id', 'default_code', 'display_wb'])
        
        result = {
            'status': 'Success',
            'data': query_result
        }
        
        response_headers = [('Content-Type', 'application/json')]
        response = request.make_response(json.dumps(result), headers=response_headers, status=200)
        
        return response

    @http.route('/api/suppliers', type='http', methods=['GET'], auth='custom_auth', sitemap=False)
    def api_get_suppliers(self, **kwargs):
        query = '''
            SELECT id, shortname
            FROM res_partner
            WHERE (is_supplier_coffee = true OR is_customer_coffee = true)
            AND shortname IS NOT NULL
        '''
        request.cr.execute(query)
        query_result = request.cr.dictfetchall()

        result = {
            'status': 'Success',
            'data': query_result
        }

        response_headers = [('Content-Type', 'application/json')]
        response = request.make_response(json.dumps(result), headers=response_headers, status=200)
        return response  
          
    @http.route('/api/security_gate', type='http', methods=['GET'], auth='custom_auth', sitemap=False)
    def get_list_security(self, **kwargs):
        querry_result = request.env['ned.security.gate.queue'].search_read([('state', 'in', ['pur_approved','qc_approved'])])
        result = {
            'status': 'Success',
            'data': querry_result
        }
        response_headers = [('Content-Type', 'application/json')]
        response_body = json.dumps(result, indent=4, cls=DateTimeEncoder)
        return request.make_response(response_body, headers=response_headers, status=200)
    
    @http.route('/api/create_stock_lot', type='http', auth='user', methods=['POST'], csrf=False)
    def create_stock_lot(self, zone_id=None, product_id=None, **kwargs):
        if zone_id and product_id:
            zone_id = int(zone_id)
            product_id = int(product_id)

            stock_lot_vals = {
                'name': '/',
                'zone_id': zone_id,
                'product_id': product_id,
                'stack_type': 'stacked',
                'company_id': request.env.user.company_id.id
            }

            stock_lot = request.env['stock.lot'].sudo().create(stock_lot_vals)

            response = {
                'status': 'Success',
                'message': 'Stock Lot created successfully!',
                'data': {'stock_lot_id': stock_lot.id}
            }
            return request.make_response(json.dumps(response), headers=[('Content-Type', 'application/json')], status=200)
        else:
            response = {
                'status': 'Error',
                'message': 'Zone ID and Product ID are required fields.'
            }
            return request.make_response(json.dumps(response), headers=[('Content-Type', 'application/json')], status=400)
        
    @http.route('/api/create_stock_picking', type='http', auth='user', methods=['POST'], csrf=False)
    def create_stock_picking(self, **kwargs):
        stock_picking_vals = {
            'name': '/',
            'picking_type_id': 1,
            'location_id': 1,
            'location_dest_id': 1,
            'company_id': request.env.user.company_id.id
            }
        
# write  @http.route('/api/packing', type='http', method=['GET'], auth='custom_auth', sitemap=False)
