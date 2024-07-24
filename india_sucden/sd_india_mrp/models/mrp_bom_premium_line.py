# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID


class MRPBomPremiumLine(models.Model):
    _inherit = 'mrp.bom.premium.line'

    aaa = fields.Float(string='AAA')
    aa = fields.Float(string='AA')
    a = fields.Float(string='A')
    b = fields.Float(string='B')
    pb = fields.Float(string='PB')
    c = fields.Float(string='C')
    e_bulk = fields.Float(string='E Bulk')
    black_b = fields.Float(string='Black B')
    bits = fields.Float(string='Bits')
    ct = fields.Float(string='CT')
    bulk = fields.Float(string='Bulk')
    coffee_husk = fields.Float(string='Coffee/Husk Bits')
    husk = fields.Float(string='Husk')
    stone = fields.Float(string='Stone')
    dust = fields.Float(string='Dust')