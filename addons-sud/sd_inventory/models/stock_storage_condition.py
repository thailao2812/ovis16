# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
from odoo.tools import float_round

from datetime import datetime
from pytz import timezone

import logging
_logger = logging.getLogger(__name__)

DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
NAME_DATETIME_FORMAT = "%Y%m%d.%H%M"


class StockStorageCondition(models.Model):
    _name = 'stock.storage.condition'
    _description = 'Stock Storage Condition'

    name = fields.Char(string='Name', compute='_compute_name', store=True)
    zone_id = fields.Many2one('stock.zone', string='Zone', required=True)
    inspection_time = fields.Datetime(string='Inspection Date', default=fields.Datetime.now(), required=True)
    time_string = fields.Char(string='Inspection Time', compute='_compute_time_string', store=True)
    humidity = fields.Float(string='Humidity', required=True, digits=(12, 2), group_operator='avg')
    temperature = fields.Float(string='Temperature', required=True, digits=(12, 2), group_operator='avg')
    temperature_unit = fields.Selection([('celcius', '°C'), ('fahrenheit', '°F')],
                                        string='Temp. Unit', default='celcius')
    inspector_id = fields.Many2one('res.users', string='Inspector', default=lambda self: self.env.user)

    @api.depends('zone_id', 'inspection_time')
    def _compute_name(self):
        user_tz = self.env.context.get(u'tz', u'UTC')
        utc_tz = timezone(u'UTC')
        for record in self:
            if record.zone_id and record.inspection_time:
                # naive_inspection_time = datetime.strptime(record.inspection_time, DATETIME_FORMAT)
                naive_inspection_time = record.inspection_time
                
                utc_inspection_time = utc_tz.localize(naive_inspection_time)
                inspection_time = utc_inspection_time.astimezone(timezone(user_tz))
                record.name = '%s %s' % (record.zone_id.name, inspection_time.strftime(NAME_DATETIME_FORMAT))

    @api.depends('inspection_time')
    def _compute_time_string(self):
        user_tz = self.env.context.get(u'tz', u'UTC')
        utc_tz = timezone(u'UTC')
        for record in self:
            # naive_inspection_time = datetime.strptime(record.inspection_time, DATETIME_FORMAT)
            naive_inspection_time = record.inspection_time
            utc_inspection_time = utc_tz.localize(naive_inspection_time)
            inspection_time = utc_inspection_time.astimezone(timezone(user_tz))
            record.time_string = inspection_time.strftime("%H:%M")
