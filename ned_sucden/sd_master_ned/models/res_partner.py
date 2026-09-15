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

    def unlink(self):
        supplier_master = self.env['supplier.master.data'].search([
            ('supplier_id', '=', self.id),
        ])
        import_geojson = self.env['import.geojson'].search([
            ('supplier_id', '=', self.id),
        ])
        if supplier_master or import_geojson:
            raise UserError(_("The supplier cannot be deleted as it is currently connected to the Import Geojson."))
        return super(ResPartner, self).unlink()
