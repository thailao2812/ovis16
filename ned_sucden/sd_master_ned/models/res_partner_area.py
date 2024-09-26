# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ResPartnerArea(models.Model):
    _inherit = 'res.partner.area'

    import_id = fields.Many2one('import.geojson', string='From Import')
    import_date = fields.Date(related='import_id.import_date', store=True)
    latitude = fields.Float(string='Latitude', digits=(10, 6))
    longitude = fields.Float(string='Longitude', digits=(10, 6))
    type_geometry = fields.Selection([
        ('polygon', 'Polygon'),
        ('point', 'Point')
    ], string='Type Geometry', default=None, compute='compute_type_geometry', store=True)

    @api.depends('gshape_type')
    def compute_type_geometry(self):
        for rec in self:
            if rec.gshape_type == 'polygon':
                rec.type_geometry = 'polygon'
            if rec.gshape_type == 'circle':
                rec.type_geometry = 'point'
