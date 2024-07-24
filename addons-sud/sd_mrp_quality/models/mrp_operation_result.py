# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
import time
from datetime import timedelta
# from pip._vendor.pygments.lexer import _inherit
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"    
from odoo.exceptions import UserError, ValidationError

from datetime import datetime


class MrpOperationResult(models.Model):
    _inherit = 'mrp.operation.result'
    # _order = 'start_date'
    
    def compute_result_scade(self):
        sql ='''
            select product_id, sum(bag_no) bag_no, sum(net_weight) net_weight
            from mrp_operation_result_scale
            where operation_result_id = %s
            group by product_id
        '''%(self.id)
        self.env.cr.execute(sql)
        for line in self.env.cr.dictfetchall():
            product_id = line['product_id']
            bag_no = line['bag_no']
            net_weight = line['net_weight']
            
            
            
            
        return
    
        
        