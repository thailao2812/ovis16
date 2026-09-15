# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"
DATE_FORMAT = "%Y-%m-%d"


class WizardExportError(models.TransientModel):
    _name = "wizard.export.error"

    properties_ids = fields.Many2many('properties.polygon')
    properties_id = fields.Many2one('properties.polygon')
    import_geojson_id = fields.Many2one('import.geojson')

    def generate_report(self):
        return self.env.ref('sd_master_ned.report_export_error_polygon').report_action(self)

    @api.model
    def default_get(self, fields):
        res = super(WizardExportError, self).default_get(fields)
        import_geojson = self.env['import.geojson'].browse(self.env.context.get('active_id'))
        if import_geojson:
            res['properties_ids'] = [(6, 0, import_geojson.properties_ids.ids)]
            res['import_geojson_id'] = import_geojson.id
        return res