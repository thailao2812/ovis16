import odoorpc
from odoo import http, _
from odoo.http import request
from odoo.exceptions import AccessError
import json
import random
import urllib.request
# class StockPickingAPI(http.Controller):

#     @http.route('/api/stock_pickings/<name>', type='json', auth='user')
#     def update_stock_picking(self, name, **kw):
        
#         # Check and raise exception if user not logged in
#         if not http.request.env.user.id:
#             raise AccessError(_("Only authenticated users can access this API"))

#         # Get stock picking record
#         picking = http.request.env['stock.picking'].search([('name', '=', name)])
#         if not picking:
#             return {'error': 'Stock picking %s not found' % name}
        
#         # Update vehicle number 
#         picking.write({
#             'vehicle_no': '47C-11111' 
#         })
        
#         return {'success': 'Stock picking %s updated' % name}


class StockPickingAPI(http.Controller):

    @http.route('/api/pickings/<picking_name>', type='json', auth='user')
    def update_picking(self, picking_name):
        # Connect to Odoo
        odoo = odoorpc.ODOO('localhost', port=8069)
        odoo.login('db_name', 'username', 'password')
        
        # Update picking 
        picking = odoo.env['stock.picking'].search([('name','=',picking_name)])
        picking.write({'vehicle_no': '47C-11111'})
        
        # Return response
        return {'success': True}

    @http.route('/api/get_list_security', type='json', auth='user')
    def get_list_security(self):
        security_gates = http.request.env['ned.security.gate'].search([('state', 'in', ['pur_approved','qc_approved'])])
        security_data = []
        for gate in security_gates:
            security_data.append({
                'name': gate.name,
                'date': gate.date,
                'state': gate.state
            })
        data = {'status' : 200, 'responce' : security_data, 'message' : "List of security gates fetch successfully"}
        return data