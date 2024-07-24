# -*- coding: utf-8 -*-
import re
import math
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class DeliveryOrder(models.Model):
    _inherit = "delivery.order"
    
        
    def printout_deilvery_order(self):
        return self.env.ref(
        'sd_pur_sales.report_delivery_orders').report_action(self)
        
        # elif self.type == 'Transfer':
        #     return self.env.ref(
        #     'sd_pur_sales.report_delivery_orders').report_action(self)