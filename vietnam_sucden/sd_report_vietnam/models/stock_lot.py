from operator import attrgetter
from re import findall as regex_findall, split as regex_split

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools import float_round


class StockLot(models.Model):
    _inherit = 'stock.lot'
    _order = 'name, id'
    
    area_name_link = fields.Char(related='zone_id.area_name', string='Area', store = True)
