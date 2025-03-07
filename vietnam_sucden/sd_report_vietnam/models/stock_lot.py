from operator import attrgetter
from re import findall as regex_findall, split as regex_split

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError
import datetime
from odoo.tools import float_round


class StockLot(models.Model):
    _inherit = 'stock.lot'
    _order = 'name, id'
    
    area_name_link = fields.Char(related='zone_id.area_name', string='Area', compute='_compute_area_name', store = True)

    @api.depends('zone_id.area_name')
    def _compute_area_name(self):
        for lot in self:
            lot.area_name = lot.zone_id.area_name