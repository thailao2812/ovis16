# -*- coding: utf-8 -*-
from odoo import api, fields, models, _, tools
from odoo.osv import expression
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict
import re

DATE_FORMAT = "%Y-%m-%d"
import datetime, time

from datetime import datetime


class OutturnPercent(models.Model):
    _name = "outturn.percent"

    categ_id = fields.Many2one('product.category', string='Outturn')
    percent = fields.Float(string='%')
    crop_id = fields.Many2one('ned.crop', string='Season Wise')
    expected = fields.Float(string='Expected Main Grade')


