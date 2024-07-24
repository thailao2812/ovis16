from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
import re
# from pip._vendor.pygments.lexer import _inherit
DATE_FORMAT = "%Y-%m-%d"

class SucdenSynConfig(models.Model):
    _inherit = 'sucden.syn.config'
    
    def sys_purchase_contract(self):
        sql ='''
                      product_id ,
                        picking_type_id ,
                        warehouse_id ,
                        location_id ,
                        location_dest_id ,
                        user_id ,
                        name ,
                        type  ,
                        state ,
                        request_date ,
                        notes  ,
                        total_qty ,
                        picking_id 
        '''
    