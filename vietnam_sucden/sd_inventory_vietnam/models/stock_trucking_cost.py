# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression
import time
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from datetime import timedelta, datetime, date


class StockTruckingCost(models.Model):
    _inherit = 'stock.trucking.cost'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    place = fields.Char(string='Place')
    name = fields.Char(string="Name", compute='_compute_name', store=True)

    @api.depends('date_from', 'date_to', 'place')
    def _compute_name(self):
        for record in self:
            record.name = ''
            if record.date_from and record.date_to and record.place:
                record.name = record.place + '('+ str(record.date_from) + ' --> ' + str(record.date_to) + ')'

