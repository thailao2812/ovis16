# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from odoo.osv import expression


class ResPartner(models.Model):
    _inherit = 'res.partner'

    farmer_id = fields.Char(string='Farmer ID')
    plot_id = fields.Char(string='Plot ID')
    area_qgis = fields.Float(string='Area QGIS')

    multiple_point_ids = fields.One2many('partner.multiple.point', 'partner_id')
