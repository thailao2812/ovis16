# -*- encoding: utf-8 -*-
import json

from odoo import api, fields, models, SUPERUSER_ID, _
from odoo.addons.report_aeroo.report_parser import Parser

from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"


class Parser(models.AbstractModel):
    _name = 'report.report_export_error_polygon'
    _inherit = ['report.report_aeroo.abstract']
    _description = 'report.report_export_error_polygon'

    def _set_localcontext(self):
        localcontext = super(Parser, self)._set_localcontext()
        localcontext.update({
            'get_line': self.get_line,
            'get_properties_data': self.get_properties_data,
            'get_data': self.get_data
        })
        return localcontext

    def get_line(self, report):
        if report:
            import_geojson = report.import_geojson_id
            error_line = import_geojson.line_ids.filtered(lambda x: x.state_check == 'red')
            print(error_line)
            return error_line
        else:
            return False

    def get_properties_data(self, report, line):
        properties_arr = line.properties_data
        properties_json = json.loads(properties_arr)
        properties_name = report.properties_id.name
        return properties_json[properties_name]

    def get_data(self, data):
        if data:
            return 'True'
        else:
            return ''