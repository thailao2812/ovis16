# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, tools
from odoo.exceptions import ValidationError
import time
from datetime import timedelta

class DirectLabour(models.Model):
    _name = 'direct.labour'
    _description = 'Direct Labour'
    _inherit = ['mail.thread']
    
    # emp_id = fields.Many2one('hr.employee', 'Employee', required=True)
    hour_nbr =  fields.Float('Number of Hours', required=True)
    result_id = fields.Many2one('mrp.operation.result', 'Operation Result')
    ot_hour = fields.Float('Number of OT Hours')
    date = fields.Date(string="Date")
    production_id = fields.Many2one('mrp.production', string = 'Manufacturing')
    shift_foreman = fields.Char(string="Shift foreman")
    operating_time = fields.Float(string="Operating time",default = 8)
    running_time = fields.Float(string="Running time")
    stop_time_machine = fields.Float(string="Stop time")
    notes = fields.Char(string="Notes / Remarks")
    
    
    @api.depends('operating_time', 'running_time', 'stop_time_machine')
    def compute_downtimes_per_shift(self):
        for i in self:
            i.downtimes_per_shift = i.operating_time - i.running_time - i.stop_time_machine
            
    downtimes_per_shift = fields.Float(string="Downtimes Per Shift", compute="compute_downtimes_per_shift",store = True)