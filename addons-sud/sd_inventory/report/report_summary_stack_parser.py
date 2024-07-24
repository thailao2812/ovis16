# -*- encoding: utf-8 -*-
from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

import datetime
import time
import pytz
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT

bank_name =False
partner = False
account_holder = False
acc_number = False

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

import datetime
from datetime import datetime
from pytz import timezone
import time
from datetime import datetime, timedelta

class Parser(models.AbstractModel):
    _name = 'report.report_summary_stack'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_summary_stack'
    
    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        
        localcontext.update({
            'get_line': self.get_line,
            'return_format_datetime': self.return_format_datetime,
            'sum_init_qty': self.sum_init_qty,
            'return_data_grn_grp': self.return_data_grn_grp
        })
        return localcontext
    
    def get_line(self, stack):
        stack = stack.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code in ['production_in', 'incoming']
                                                 and x.picking_id.state == 'done')
        
        return stack

    def return_format_datetime(self, date_input):
        date = date_input + timedelta(hours=7)
        return date

    def sum_init_qty(self, stack):
        total = sum(i.init_qty for i in stack.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code in ['production_in', 'incoming']
                                                                          and x.picking_id.state == 'done'))
        total_bags_no = sum(i.bag_no for i in stack.move_line_ids.filtered(lambda x: x.picking_id.picking_type_id.code in ['production_in', 'incoming']
                                                                                and x.picking_id.state == 'done'))
        return '{:,}'.format(int(total)), '{:,}'.format(int(total_bags_no))

    def return_data_grn_grp(self, line):
        if line.picking_id.picking_type_id.code == 'incoming':
            return '', line.picking_id.vehicle_no
        if line.picking_id.picking_type_id.code == 'production_in':
            return line.picking_id.production_id.name, ''
    
    
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
